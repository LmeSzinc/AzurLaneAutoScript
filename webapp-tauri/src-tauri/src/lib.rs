use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use tauri::{
    AppHandle, Manager,
};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, TrayIconBuilder, TrayIconEvent};

pub struct BackendProcess {
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
const BACKEND_PORT: u16 = 22267;

/// Resolve the Alas project root: the directory containing gui.py.
/// Search order: ALAS_ROOT env, then walk up from the resource dir.
fn resolve_root(app: &AppHandle) -> PathBuf {
    if let Ok(root) = std::env::var("ALAS_ROOT") {
        return PathBuf::from(root);
    }
    let mut dir = app
        .path()
        .resource_dir()
        .unwrap_or_else(|_| std::env::current_dir().unwrap_or_default());
    loop {
        if dir.join("gui.py").exists() {
            return dir;
        }
        if !dir.pop() {
            break;
        }
    }
    std::env::current_dir().unwrap_or_default()
}

/// Resolve the python executable and the project root directory.
///
/// Search order:
///   1. ALAS_PYTHON environment variable
///   2. `alas-backend*.exe` next to the app binary (packaged PyInstaller
///      onedir sidecar, shipped via tauri externalBin)
///   3. <root>/.venv/Scripts/python.exe (development)
///   4. "python" from PATH
fn resolve_python(root: &PathBuf) -> PathBuf {
    if let Ok(p) = std::env::var("ALAS_PYTHON") {
        return PathBuf::from(p);
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            if let Ok(entries) = std::fs::read_dir(dir) {
                for entry in entries.flatten() {
                    let name = entry.file_name().to_string_lossy().to_string();
                    if name.starts_with("alas-backend") && name.ends_with(".exe") {
                        return entry.path();
                    }
                }
            }
        }
    }
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

/// Spawn the python webui backend and wait until it is ready, then show the
/// main window.
fn spawn_backend(app: AppHandle) {
    let root = resolve_root(&app);
    let python = resolve_python(&root);
    #[cfg(not(debug_assertions))]
    let port = find_free_port();

    // Installed sidecar: point the backend at a writable per-user data
    // directory (install dirs may be read-only, and the wholesale sidecar
    // swap during updates must not touch user data). gui.py seeds
    // config/assets/bin from the bundle on first run and chdirs there.
    let is_sidecar = python
        .file_name()
        .and_then(|n| n.to_str())
        .map(|n| n.starts_with("alas-backend") && n.ends_with(".exe"))
        .unwrap_or(false);

    let mut command = Command::new(&python);
    command
        .arg("gui.py")
        .current_dir(&root)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    // Keep stdin occupied by a real handle: alas-shell.exe is a GUI binary
    // whose stdin handle slot is NULL, and CreatePipe then reuses handle 0
    // for the multiprocessing spawn handshake. The EnableReload child reads
    // that handshake through sys.stdin (CPython's spawn_main), hits EOF on
    // the misrouted pipe and dies silently a split second after start.
    #[cfg(not(debug_assertions))]
    command.arg("--port").arg(port.to_string());
    // Stdio is GBK-encoded pipes here; force UTF-8 so rich/loguru output
    // (box-drawing rules, CJK) never crashes the backend's error paths.
    command.env("PYTHONIOENCODING", "utf-8");
    if is_sidecar {
        if let Ok(data_dir) = app.path().app_data_dir() {
            command.env("ALAS_DATA_DIR", &data_dir);
        }
    }
    // python.exe is a console-subsystem binary: without CREATE_NO_WINDOW
    // Windows pops up an empty console window next to the app.
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x0800_0000);
    }
    // Dev builds load the SPA from the vite dev server (devUrl), which is
    // cross-origin to the backend; allow that origin via the backend's
    // ALAS_CORS_ORIGINS gate. Packaged builds serve the SPA from the
    // backend itself (same origin) and need no CORS.
    #[cfg(debug_assertions)]
    command.env("ALAS_CORS_ORIGINS", "http://127.0.0.1:1420");

    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(e) => {
            eprintln!("Failed to spawn backend {}: {}", python.display(), e);
            show_backend_error(&app);
            return;
        }
    };

    // Drain the backend stdout pipe: an unread pipe fills up (64KB) and
    // blocks the backend once its logs exceed the buffer. Mirror to the
    // console in debug builds.
    let stdout = child.stdout.take();
    std::thread::spawn(move || {
        if let Some(stdout) = stdout {
            let reader = BufReader::new(stdout);
            #[allow(unused_variables)]
            for line in reader.lines().map_while(Result::ok) {
                #[cfg(debug_assertions)]
                println!("[backend] {}", line);
            }
        }
    });

    // Backend stderr carries both the readiness marker and every failure
    // (tracebacks, bind errors). Mirror it to a file so release-build
    // problems stay diagnosable even though the pipe swallows them.
    let stderr_log = app
        .path()
        .app_log_dir()
        .map(|dir| {
            let _ = std::fs::create_dir_all(&dir);
            dir.join("backend.log")
        })
        .unwrap_or_else(|_| PathBuf::from("backend.log"));

    let ready = Arc::new(AtomicBool::new(false));
    let stderr = child.stderr.take();
    let handle = app.clone();
    let ready_reader = Arc::clone(&ready);
    let stderr_log_reader = stderr_log.clone();
    std::thread::spawn(move || {
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&stderr_log_reader)
            .ok();
        if let Some(stderr) = stderr {
            let reader = BufReader::new(stderr);
            for line in reader.lines().map_while(Result::ok) {
                // Mirror backend logs to the console in debug builds.
                #[cfg(debug_assertions)]
                println!("[backend] {}", line);
                if let Some(file) = log_file.as_mut() {
                    let _ = writeln!(file, "{line}");
                }
                if line.contains("Application startup complete") {
                    ready_reader.store(true, Ordering::SeqCst);
                    if let Some(window) = handle.get_webview_window("main") {
                        // The backend binds its port right after the marker;
                        // wait briefly so the first navigation lands.
                        std::thread::sleep(Duration::from_millis(500));
                        // Packaged builds navigate to the SPA served by the
                        // backend itself (same origin). Dev builds stay on
                        // the vite devUrl, so navigation is skipped there.
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
                }
            }
        }
        // stderr closed => the backend exited. If the marker never arrived,
        // surface the failure instead of hiding the window forever.
        if !ready_reader.load(Ordering::SeqCst) {
            show_backend_error(&handle);
        }
    });

    // Watchdog for a hung backend that never becomes ready and never exits.
    let ready_watch = Arc::clone(&ready);
    let handle_watch = app.clone();
    std::thread::spawn(move || {
        std::thread::sleep(Duration::from_secs(60));
        if !ready_watch.load(Ordering::SeqCst) {
            show_backend_error(&handle_watch);
        }
    });

    // Pin the whole backend tree to a kill-on-close job (see BackendProcess).
    #[cfg(target_os = "windows")]
    {
        let job = assign_kill_on_close_job(&child);
        *app.state::<BackendProcess>().job.lock().unwrap() = job;
    }

    app.state::<BackendProcess>().child.lock().unwrap().replace(child);
}

fn kill_backend(app: &AppHandle) {
    let child = app.state::<BackendProcess>().child.lock().unwrap().take();
    if let Some(mut child) = child {
        let _ = child.kill();
        let _ = child.wait();
    }
    #[cfg(target_os = "windows")]
    {
        use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
        let job = app.state::<BackendProcess>().job.lock().unwrap().take();
        if let Some(job) = job {
            unsafe {
                // Reaps every process in the backend tree (the reload child
                // and its own spawns would otherwise survive the direct kill).
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
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(BackendProcess {
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
