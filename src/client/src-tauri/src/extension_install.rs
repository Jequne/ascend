use std::{fs, io, path::Path};

use serde::Serialize;
use tauri::{AppHandle, Manager};
use tauri_plugin_opener::OpenerExt;

const RESOURCE_DIRECTORY: &str = "extension/chrome-mv3";
const INSTALL_ROOT: &str = "extension";
const COMPLETE_MARKER: &str = ".ascend-install-complete";

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExtensionInstallationInfo {
    path: String,
    version: &'static str,
}

#[derive(Debug, Serialize)]
pub struct ExtensionInstallationError {
    code: &'static str,
}

impl ExtensionInstallationError {
    fn new(code: &'static str) -> Self {
        Self { code }
    }
}

#[tauri::command]
pub fn prepare_extension_installation(
    app: AppHandle,
) -> Result<ExtensionInstallationInfo, ExtensionInstallationError> {
    prepare_installation(&app)
}

#[tauri::command]
pub fn open_extension_installation_folder(
    app: AppHandle,
) -> Result<ExtensionInstallationInfo, ExtensionInstallationError> {
    let installation = prepare_installation(&app)?;
    app.opener()
        .open_path(&installation.path, None::<&str>)
        .map_err(|_| ExtensionInstallationError::new("extension_folder_open_failed"))?;
    Ok(installation)
}

pub(crate) fn prepare_installation(
    app: &AppHandle,
) -> Result<ExtensionInstallationInfo, ExtensionInstallationError> {
    let source = app
        .path()
        .resource_dir()
        .map_err(|_| ExtensionInstallationError::new("resource_directory_unavailable"))?
        .join(RESOURCE_DIRECTORY);
    validate_extension_bundle(&source)
        .map_err(|_| ExtensionInstallationError::new("extension_bundle_invalid"))?;

    let install_root = app
        .path()
        .app_data_dir()
        .map_err(|_| ExtensionInstallationError::new("app_data_unavailable"))?
        .join(INSTALL_ROOT);
    let destination = install_root.join(format!("ascend-ext-{}", env!("CARGO_PKG_VERSION")));
    let marker = destination.join(COMPLETE_MARKER);

    if !installation_is_current(&source, &destination, &marker) {
        if destination.exists() {
            fs::remove_dir_all(&destination)
                .map_err(|_| ExtensionInstallationError::new("extension_copy_failed"))?;
        }
        fs::create_dir_all(&install_root)
            .map_err(|_| ExtensionInstallationError::new("extension_copy_failed"))?;
        copy_directory(&source, &destination)
            .map_err(|_| ExtensionInstallationError::new("extension_copy_failed"))?;
        fs::write(&marker, env!("CARGO_PKG_VERSION"))
            .map_err(|_| ExtensionInstallationError::new("extension_copy_failed"))?;
    }

    Ok(ExtensionInstallationInfo {
        path: destination.to_string_lossy().into_owned(),
        version: env!("CARGO_PKG_VERSION"),
    })
}

fn installation_is_current(source: &Path, destination: &Path, marker: &Path) -> bool {
    marker.is_file()
        && fs::read_to_string(marker).is_ok_and(|version| version == env!("CARGO_PKG_VERSION"))
        && directories_match(source, destination, true).unwrap_or(false)
}

fn directories_match(source: &Path, destination: &Path, is_root: bool) -> Result<bool, io::Error> {
    if !source.is_dir() || !destination.is_dir() {
        return Ok(false);
    }

    let mut source_entries = fs::read_dir(source)?
        .map(|entry| entry.map(|entry| entry.file_name()))
        .collect::<Result<Vec<_>, _>>()?;
    let mut destination_entries = fs::read_dir(destination)?
        .filter_map(|entry| match entry {
            Ok(entry) if is_root && entry.file_name() == COMPLETE_MARKER => None,
            result => Some(result.map(|entry| entry.file_name())),
        })
        .collect::<Result<Vec<_>, _>>()?;
    source_entries.sort();
    destination_entries.sort();
    if source_entries != destination_entries {
        return Ok(false);
    }

    for name in source_entries {
        let source_entry = source.join(&name);
        let destination_entry = destination.join(name);
        let source_type = fs::symlink_metadata(&source_entry)?.file_type();
        let destination_type = fs::symlink_metadata(&destination_entry)?.file_type();
        if source_type.is_symlink() || destination_type.is_symlink() {
            return Ok(false);
        }
        if source_type.is_dir() && destination_type.is_dir() {
            if !directories_match(&source_entry, &destination_entry, false)? {
                return Ok(false);
            }
        } else if source_type.is_file() && destination_type.is_file() {
            if fs::read(source_entry)? != fs::read(destination_entry)? {
                return Ok(false);
            }
        } else {
            return Ok(false);
        }
    }
    Ok(true)
}

fn validate_extension_bundle(path: &Path) -> Result<(), io::Error> {
    let manifest_path = path.join("manifest.json");
    let manifest: serde_json::Value = serde_json::from_slice(&fs::read(manifest_path)?)
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
    if manifest
        .get("manifest_version")
        .and_then(serde_json::Value::as_u64)
        != Some(3)
        || manifest.get("name").and_then(serde_json::Value::as_str) != Some("Ascend ext")
        || manifest.get("version").and_then(serde_json::Value::as_str)
            != Some(env!("CARGO_PKG_VERSION"))
    {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "unexpected extension manifest",
        ));
    }
    Ok(())
}

fn copy_directory(source: &Path, destination: &Path) -> Result<(), io::Error> {
    fs::create_dir_all(destination)?;
    for entry in fs::read_dir(source)? {
        let entry = entry?;
        let file_type = entry.file_type()?;
        let target = destination.join(entry.file_name());
        if file_type.is_symlink() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "extension bundle contains a symlink",
            ));
        }
        if file_type.is_dir() {
            copy_directory(&entry.path(), &target)?;
        } else if file_type.is_file() {
            fs::copy(entry.path(), target)?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        path::PathBuf,
        sync::atomic::{AtomicU64, Ordering},
    };

    static NEXT_FIXTURE_ID: AtomicU64 = AtomicU64::new(1);

    fn temporary_directory(label: &str) -> PathBuf {
        std::env::temp_dir().join(format!(
            "ascend-extension-install-{label}-{}-{}",
            std::process::id(),
            NEXT_FIXTURE_ID.fetch_add(1, Ordering::Relaxed)
        ))
    }

    #[test]
    fn validates_expected_manifest_and_copies_nested_bundle() {
        let root = temporary_directory("copy");
        let source = root.join("source");
        let destination = root.join("destination");
        fs::create_dir_all(source.join("assets")).expect("create source");
        fs::write(
            source.join("manifest.json"),
            format!(
                r#"{{"manifest_version":3,"name":"Ascend ext","version":"{}"}}"#,
                env!("CARGO_PKG_VERSION")
            ),
        )
        .expect("write manifest");
        fs::write(source.join("assets/popup.js"), "content").expect("write asset");

        validate_extension_bundle(&source).expect("valid manifest");
        copy_directory(&source, &destination).expect("copy bundle");
        assert_eq!(
            fs::read_to_string(destination.join("assets/popup.js")).expect("read asset"),
            "content"
        );

        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn rejects_a_different_extension_manifest() {
        let root = temporary_directory("invalid");
        fs::create_dir_all(&root).expect("create fixture");
        fs::write(
            root.join("manifest.json"),
            r#"{"manifest_version":3,"name":"Another extension","version":"0.1.0"}"#,
        )
        .expect("write manifest");

        assert!(validate_extension_bundle(&root).is_err());
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn detects_stale_installations_even_when_the_version_is_unchanged() {
        let root = temporary_directory("freshness");
        let source = root.join("source");
        let destination = root.join("destination");
        fs::create_dir_all(source.join("assets")).expect("create source");
        fs::create_dir_all(destination.join("assets")).expect("create destination");
        fs::write(source.join("manifest.json"), "current manifest").expect("write source");
        fs::write(source.join("assets/background.js"), "protocol 1").expect("write source");
        fs::write(destination.join("manifest.json"), "current manifest")
            .expect("write destination");
        fs::write(destination.join("assets/background.js"), "protocol 2")
            .expect("write destination");
        let marker = destination.join(COMPLETE_MARKER);
        fs::write(&marker, env!("CARGO_PKG_VERSION")).expect("write marker");

        assert!(!installation_is_current(&source, &destination, &marker));

        fs::write(destination.join("assets/background.js"), "protocol 1")
            .expect("refresh destination");
        assert!(installation_is_current(&source, &destination, &marker));

        fs::write(destination.join("stale.js"), "stale file").expect("write stale file");
        assert!(!installation_is_current(&source, &destination, &marker));
        fs::remove_dir_all(root).expect("remove fixture");
    }
}
