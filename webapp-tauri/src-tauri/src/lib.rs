use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{
    AppHandle, Manager,
};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, TrayIconBuilder, TrayIconEvent};

pub struct BackendProcess {
    /// Non-Windows fallback: the poll thread cannot own the Child there
    /// (no job object), so the handle stays managed here.
    #[cfg(not(target_os = "windows"))]
    pub child: Mutex<Option<Child>>,
    /// Windows job object holding the whole backend process tree. Killing
    /// the direct child does NOT kill its EnableReload grandchild (Windows
    /// processes have no parent-kill propagation), so the tree is pinned to
    /// a kill-on-close job: TerminateJobObject reaps it on exit, and if the
    /// shell itself dies (crash, task manager) the OS closes the handle and
    /// reaps the backend automatically - no orphaned uvicorn on 22267.
    /// Stored as usize: HANDLE is a raw pointer, which is !Send.
    #[cfg(target_os = "windows")]
    pub job: Mutex<Option<usize>>,
}

/// Create a kill-on-close job object and assign the just-spawned backend to
/// it. Best effort: a failure here degrades to the old orphan-prone
/// behavior instead of blocking startup.
#[cfg(target_os = "windows")]
fn assign_kill_on_close_job(child: &Child) -> Option<usize> {
    use std::os::windows::io::AsRawHandle;
    use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    unsafe {
        let job: HANDLE = CreateJobObjectW(std::ptr::null(), std::ptr::null());
        if job.is_null() {
            return None;
        }
        let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            &info as *const _ as *const _,
            std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
        ) == 0
        {
            CloseHandle(job);
            return None;
        }
        if AssignProcessToJobObject(job, child.as_raw_handle() as HANDLE) == 0 {
            CloseHandle(job);
            return None;
        }
        Some(job as usize)
    }
}

/// Default backend port; release builds probe upwards from here for a free
/// one so a concurrently running web instance never blocks the desktop
/// backend (uvicorn exits on a bind conflict and the marker never arrives).
#[cfg(not(debug_assertions))]
const BACKEND_PORT: u16 = 22267;

/// Walk up from `start` looking for a directory containing gui.py (the
/// source checkout root). The mode decision must never depend on the
/// launch CWD: an installed shell launched with a stray CWD must still
/// resolve its sidecar, not some unrelated source tree.
fn find_source_root(start: &Path) -> Option<PathBuf> {
    let mut dir = Some(start.to_path_buf());
    while let Some(d) = dir {
        if d.join("gui.py").exists() {
            return Some(d);
        }
        dir = d.parent().map(PathBuf::from);
    }
    None
}

/// Find the PyInstaller onedir sidecar next to the shell exe: the
/// `alas-backend` directory whose own `alas-backend.exe` is the backend
/// entry point (bundle.resources installs the whole directory beside the
/// shell exe).
fn find_sidecar(exe_dir: &Path) -> Option<PathBuf> {
    let entries = std::fs::read_dir(exe_dir).ok()?;
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().to_string();
        if name.starts_with("alas-backend") {
            let path = entry.path();
            if path.is_dir() {
                if let Ok(inner) = std::fs::read_dir(&path) {
                    for f in inner.flatten() {
                        let fname = f.file_name().to_string_lossy().to_string();
                        if fname.ends_with(".exe") {
                            return Some(f.path());
                        }
                    }
                }
            } else if name.ends_with(".exe") {
                return Some(path);
            }
        }
    }
    None
}

/// Resolve the python executable for a source root: the venv interpreter
/// if present, else `python` from PATH. (ALAS_PYTHON is handled by the
/// caller.)
fn resolve_python(root: &Path) -> PathBuf {
    let dev = root.join(".venv").join("Scripts").join("python.exe");
    if dev.exists() {
        return dev;
    }
    PathBuf::from("python")
}

/// First free port at or after the backend default (release builds only).
/// Dev builds keep the backend on the default port, which the vite dev
/// proxy targets (see vite.config.ts).
///
/// Probe with TCP connect, not bind: on Windows a bind to 127.0.0.1:P can
/// succeed even while another process listens on 0.0.0.0:P (SO_REUSEADDR
/// hijack), which would make a bind-based probe useless.
#[cfg(not(debug_assertions))]
fn find_free_port() -> u16 {
    use std::net::TcpStream;
    (BACKEND_PORT..BACKEND_PORT + 20)
        .find(|port| {
            let addr = format!("127.0.0.1:{port}").parse().unwrap();
            TcpStream::connect_timeout(&addr, Duration::from_millis(150)).is_err()
        })
        .unwrap_or(BACKEND_PORT)
}

/// The backend failed (spawn error, early exit, or startup timeout): show
/// the window with the embedded error page instead of leaving the app as
/// an invisible tray-only process.
fn show_backend_error(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.navigate(url::Url::parse("tauri://localhost/error.html").unwrap());
        let _ = window.show();
        let _ = window.set_focus();
    }
}

/// Copy a directory tree. Used to seed the install directory from the
/// PyInstaller bundle on first run; failures are per-file and ignored (the
/// backend surfaces what it needs in its own logs).
fn copy_dir_recursive(src: &Path, dst: &Path) {
    let Ok(entries) = std::fs::read_dir(src) else {
        return;
    };
    let _ = std::fs::create_dir_all(dst);
    for entry in entries.flatten() {
        let from = entry.path();
        let to = dst.join(entry.file_name());
        if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
            copy_dir_recursive(&from, &to);
        } else {
            let _ = std::fs::copy(&from, &to);
        }
    }
}

/// Installed sidecar: the install directory is the data directory.
/// currentUser installs are writable, and updates only replace the files
/// that ship in the installer (exe + sidecar dir), so config/log/assets/bin
/// left beside them survive. First run seeds those directories from the
/// PyInstaller bundle, whose datas live next to the exe under `_internal/`.
fn seed_sidecar_data(python: &Path, root: &Path) {
    let Some(bundle_dir) = python.parent() else {
        return;
    };
    let internal = bundle_dir.join("_internal");
    for name in ["config", "assets", "bin"] {
        let dst = root.join(name);
        if !dst.exists() {
            copy_dir_recursive(&internal.join(name), &dst);
        }
    }
}

/// Open the packaged-build backend log file for append (diagnostics only,
/// never parsed). Falls back to a null stdio on any failure.
#[cfg(not(debug_assertions))]
fn open_log(path: &Path) -> Stdio {
    use std::fs::OpenOptions;
    OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map(Stdio::from)
        .unwrap_or_else(|_| Stdio::null())
}

/// A backend HTTP port is ready when it accepts a connection and answers
/// with any status (uvicorn binds before serving, so a reply - even
/// 401/404 - proves the app is up). Pure std TCP keeps this
/// dependency-free.
fn http_probe(addr: std::net::SocketAddr) -> bool {
    use std::io::{Read, Write};
    use std::net::TcpStream;

    let Ok(mut stream) = TcpStream::connect_timeout(&addr, Duration::from_millis(300)) else {
        return false;
    };
    let Ok(()) = stream.set_read_timeout(Some(Duration::from_millis(500))) else {
        return false;
    };
    if stream
        .write_all(b"GET / HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n")
        .is_err()
    {
        return false;
    }
    let mut buf = [0u8; 1];
    stream.read(&mut buf).is_ok_and(|n| n > 0)
}

/// Spawn the python webui backend, poll its HTTP port until it answers,
/// then show the main window.
fn spawn_backend(app: AppHandle) {
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|exe| exe.parent().map(|p| p.to_path_buf()));

    // Mode decision, CWD-independent: a source checkout exists iff gui.py
    // sits at or above the shell exe (ALAS_ROOT overrides). Otherwise this
    // is an installed build - the sidecar next to the exe is the backend
    // and the install dir is the data dir (see seed_sidecar_data).
    let source_root = std::env::var("ALAS_ROOT")
        .ok()
        .map(PathBuf::from)
        .or_else(|| exe_dir.as_deref().and_then(find_source_root));

    let (root, python, is_sidecar) = if let Some(root) = source_root {
        let python = std::env::var("ALAS_PYTHON")
            .ok()
            .map(PathBuf::from)
            .unwrap_or_else(|| resolve_python(&root));
        (root, python, false)
    } else {
        let dir = exe_dir.unwrap_or_else(|| PathBuf::from("."));
        let python = find_sidecar(&dir)
            .or_else(|| std::env::var("ALAS_PYTHON").ok().map(PathBuf::from))
            .unwrap_or_else(|| PathBuf::from("python"));
        (dir, python, true)
    };

    if is_sidecar {
        seed_sidecar_data(&python, &root);
    }

    // Dev: fixed port, the vite proxy target (vite.config.ts). Release:
    // probe upwards from the default so a running web instance never
    // blocks the desktop backend.
    #[cfg(debug_assertions)]
    let port: u16 = 22267;
    #[cfg(not(debug_assertions))]
    let port = find_free_port();

    let mut command = Command::new(&python);
    command
        .arg("gui.py")
        .arg("--port")
        .arg(port.to_string())
        .current_dir(&root)
        // Keep stdin occupied by a real handle: alas-shell.exe is a GUI
        // binary whose stdin handle slot is NULL, and CreatePipe then
        // reuses handle 0 for the multiprocessing spawn handshake. The
        // EnableReload child reads that handshake through sys.stdin
        // (CPython's spawn_main), hits EOF on the misrouted pipe and dies
        // silently a split second after start.
        .stdin(Stdio::null());

    #[cfg(debug_assertions)]
    {
        // Dev builds inherit the terminal, so backend logs appear exactly
        // as with `uv run gui.py` (console-native encoding, no mojibake).
        // The SPA loads from the vite dev server (devUrl), which is
        // cross-origin to the backend; allow that origin via the backend's
        // ALAS_CORS_ORIGINS gate.
        command.env("ALAS_CORS_ORIGINS", "http://127.0.0.1:1420");
    }

    #[cfg(not(debug_assertions))]
    {
        // Packaged builds: stdout+stderr go into a log file (no pipes: the
        // frozen PyInstaller runtime has shown fragile behavior under
        // piped, no-console stdio combinations, while file handles are
        // always fine). The file is diagnostics only - readiness is
        // detected over HTTP, never by parsing logs.
        let backend_log = app
            .path()
            .app_log_dir()
            .map(|dir| {
                let _ = std::fs::create_dir_all(&dir);
                dir.join("backend.log")
            })
            .unwrap_or_else(|_| PathBuf::from("backend.log"));
        let _ = std::fs::remove_file(&backend_log);
        command.stdout(open_log(&backend_log)).stderr(open_log(&backend_log));

        // python.exe is a console-subsystem binary: without
        // CREATE_NO_WINDOW Windows pops up an empty console window next to
        // the app.
        #[cfg(target_os = "windows")]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x0800_0000);
        }
    }

    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(e) => {
            eprintln!("Failed to spawn backend {}: {}", python.display(), e);
            show_backend_error(&app);
            return;
        }
    };

    // Pin the whole backend tree to a kill-on-close job (see BackendProcess).
    // Must run before the poll thread takes ownership of the Child handle.
    #[cfg(target_os = "windows")]
    {
        let job = assign_kill_on_close_job(&child);
        *app.state::<BackendProcess>().job.lock().unwrap() = job;
    }

    let handle = app.clone();
    std::thread::spawn(move || {
        // Readiness: the backend binds its HTTP port before serving, so the
        // first response means ready. Poll until an answer arrives, the
        // backend exits, or 60s elapse.
        let addr = format!("127.0.0.1:{port}").parse().unwrap();
        let deadline = std::time::Instant::now() + Duration::from_secs(60);
        let mut ready = false;
        while !ready && std::time::Instant::now() < deadline {
            if let Ok(Some(_)) = child.try_wait() {
                break; // backend exited before answering
            }
            ready = http_probe(addr);
            if !ready {
                std::thread::sleep(Duration::from_millis(300));
            }
        }
        if !ready {
            // Backend exited early or never came up: surface the failure
            // instead of leaving an invisible tray-only process.
            show_backend_error(&handle);
            return;
        }
        if let Some(window) = handle.get_webview_window("main") {
            #[cfg(not(debug_assertions))]
            {
                let url = std::env::var("ALAS_WEBUI_URL")
                    .unwrap_or_else(|_| format!("http://127.0.0.1:{port}"));
                match url::Url::parse(&url) {
                    Ok(url) => {
                        let _ = window.navigate(url);
                    }
                    Err(e) => {
                        eprintln!("Invalid ALAS_WEBUI_URL: {e}");
                    }
                }
            }
            let _ = window.show();
            let _ = window.set_focus();
        }
    });

    // The poll thread owns the Child handle now; kill_backend reaps the
    // tree through the job object instead.
    #[cfg(not(target_os = "windows"))]
    app.state::<BackendProcess>().child.lock().unwrap().replace(child);
}

fn kill_backend(app: &AppHandle) {
    #[cfg(not(target_os = "windows"))]
    {
        let child = app.state::<BackendProcess>().child.lock().unwrap().take();
        if let Some(mut child) = child {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    #[cfg(target_os = "windows")]
    {
        use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
        let job = app.state::<BackendProcess>().job.lock().unwrap().take();
        if let Some(job) = job {
            unsafe {
                // Reaps every process in the backend tree (children and
                // their own spawns would otherwise survive a direct kill).
                windows_sys::Win32::System::JobObjects::TerminateJobObject(job as HANDLE, 0);
                CloseHandle(job as HANDLE);
            }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                if window.is_minimized().unwrap_or(false) {
                    let _ = window.unminimize();
                }
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .manage(BackendProcess {
            #[cfg(not(target_os = "windows"))]
            child: Mutex::new(None),
            #[cfg(target_os = "windows")]
            job: Mutex::new(None),
        })
        .setup(|app| {
            let handle = app.handle().clone();
            spawn_backend(handle.clone());

            // System tray
            let show = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let hide = MenuItem::with_id(app, "hide", "Hide", true, None::<&str>)?;
            let exit = MenuItem::with_id(app, "exit", "Exit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &hide, &exit])?;
            let _tray = TrayIconBuilder::with_id("alas-tray")
                .icon(app.default_window_icon().expect("bundled window icon").clone())
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
                    "exit" => {
                        kill_backend(app);
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    // Only a left click shows the window. A right click pops
                    // the context menu natively; showing+focusing the window
                    // here would steal focus and dismiss the menu instantly.
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        ..
                    }
                    | TrayIconEvent::DoubleClick {
                        button: MouseButton::Left,
                        ..
                    } = event
                    {
                        if let Some(window) = tray.app_handle().get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            // Close = quit (native titlebar X, taskbar close, or Alt+F4).
            // The backend is killed and the process exits, taking the tray
            // icon with it - no hidden zombie.
            if let Some(window) = app.get_webview_window("main") {
                let handle = app.handle().clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { .. } = event {
                        kill_backend(&handle);
                        handle.exit(0);
                    }
                });
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app, event| {
        if let tauri::RunEvent::Exit = event {
            kill_backend(app);
        }
    });
}
