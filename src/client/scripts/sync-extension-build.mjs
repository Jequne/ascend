import { cp, mkdir, rm, stat } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const clientRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(clientRoot, "../extension/.output/chrome-mv3");
const target = resolve(clientRoot, "src-tauri/resources/extension/chrome-mv3");
const relativeTarget = relative(clientRoot, target);

if (
    relativeTarget.startsWith("..") ||
    relativeTarget === "" ||
    resolve(clientRoot, relativeTarget) !== target
) {
    throw new Error("invalid_extension_resource_target");
}

if (!(await stat(resolve(source, "manifest.json"))).isFile()) {
    throw new Error("extension_manifest_missing");
}

await rm(target, { recursive: true, force: true });
await mkdir(dirname(target), { recursive: true });
await cp(source, target, { recursive: true, errorOnExist: true });
