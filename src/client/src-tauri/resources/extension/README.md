# Ascend ext resource staging

`npm run build:extension-resource` builds the extension and copies its production output to the ignored `chrome-mv3` directory. Tauri bundles that staged directory under `extension/chrome-mv3`.

Do not edit or commit the build output.
