fn main() {
    // Autogenerate `allow-<command>`/`deny-<command>` permissions for the
    // app commands registered in lib.rs, so capabilities can grant them
    // explicitly (remote origins enforce the ACL for app commands too).
    tauri_build::try_build(
        tauri_build::Attributes::new().app_manifest(
            tauri_build::AppManifest::new()
                .commands(&["window_min", "window_max", "window_tray", "window_close"]),
        ),
    )
    .expect("failed to run tauri-build");
}
