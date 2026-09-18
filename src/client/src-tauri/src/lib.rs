mod bridge;

use bridge::BridgeState;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let app_data_dir = app.path().app_data_dir()?;
            let bridge = BridgeState::initialize(app_data_dir)?;
            app.manage(bridge.clone());
            bridge.start(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            bridge::get_extension_bridge_state,
            bridge::get_extension_pairing_code,
            bridge::rotate_extension_pairing_code,
            bridge::set_extension_auto_open_mode,
            bridge::send_extension_navigation,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
