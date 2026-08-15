use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{
    AppHandle, Manager, WebviewWindow,
};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder, TrayIconEvent};

pub struct BackendProcess(pub Mutex<Option<Child>>);

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
///   4. <root>/toolkit/python/python.exe (legacy packed layout)
///   5. "python" from PATH
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
    let packed = root
        .join("toolkit")
        .join("python")
        .join("python.exe");
    if packed.exists() {
        return packed;
    }
    PathBuf::from("python")
}

/// Spawn the python webui backend and wait until it is ready, then show the
/// main window.
fn spawn_backend(app: AppHandle) {
    let root = resolve_root(&app);
    let python = resolve_python(&root);
    let mut command = Command::new(&python);
    command
        .arg("gui.py")
        .current_dir(&root)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
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
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }
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
            for line in reader.lines().map_while(Result::ok) {
                #[cfg(debug_assertions)]
                println!("[backend] {}", line);
            }
        }
    });

    let stderr = child.stderr.take();
    let handle = app.clone();
    std::thread::spawn(move || {
        if let Some(stderr) = stderr {
            let reader = BufReader::new(stderr);
            for line in reader.lines().map_while(Result::ok) {
                // Mirror backend logs to the console in debug builds.
                #[cfg(debug_assertions)]
                println!("[backend] {}", line);
                if line.contains("Application startup complete") {
                    if let Some(window) = handle.get_webview_window("main") {
                        // The backend binds its port right after the marker;
                        // wait briefly so the first navigation lands.
                        std::thread::sleep(std::time::Duration::from_millis(500));
                        // Packaged builds navigate to the SPA served by the
                        // backend itself (same origin). Dev builds stay on
                        // the vite devUrl, so navigation is skipped there.
                        #[cfg(not(debug_assertions))]
                        {
                            let url = std::env::var("ALAS_WEBUI_URL")
                                .unwrap_or_else(|_| "http://127.0.0.1:22267".to_string());
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
    });

    app.state::<BackendProcess>().0.lock().unwrap().replace(child);
}

fn kill_backend(app: &AppHandle) {
    let state = app.state::<BackendProcess>();
    let child = state.0.lock().unwrap().take();
    if let Some(mut child) = child {
        let _ = child.kill();
        let _ = child.wait();
    }
}

#[tauri::command]
fn window_min(window: WebviewWindow) {
    let _ = window.minimize();
}

#[tauri::command]
fn window_max(window: WebviewWindow) {
    if window.is_maximized().unwrap_or(false) {
        let _ = window.unmaximize();
    } else {
        let _ = window.maximize();
    }
}

#[tauri::command]
fn window_tray(window: WebviewWindow) {
    let _ = window.hide();
}

#[tauri::command]
fn window_close(app: AppHandle) {
    kill_backend(&app);
    app.exit(0);
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
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            spawn_backend(handle.clone());

            // System tray
            let show = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let hide = MenuItem::with_id(app, "hide", "Hide", true, None::<&str>)?;
            let exit = MenuItem::with_id(app, "exit", "Exit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &hide, &exit])?;
            let _tray = TrayIconBuilder::with_id("alas-tray")
                .menu(&menu)
                .on_menu_event(move |app, event| match event.id.as_ref() {
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
                    if let TrayIconEvent::Click { .. } = event {
                        if let Some(window) = tray.app_handle().get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            // Keep the window hidden until the backend is ready (done in
            // spawn_backend); closing the window hides it to the tray.
            if let Some(window) = app.get_webview_window("main") {
                let handle = app.handle().clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        if let Some(window) = handle.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
                });
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            window_min,
            window_max,
            window_tray,
            window_close,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app, event| {
        if let tauri::RunEvent::Exit = event {
            kill_backend(app);
        }
    });
}
