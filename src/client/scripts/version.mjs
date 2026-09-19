import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const clientRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const files = {
    package: resolve(clientRoot, "package.json"),
    packageLock: resolve(clientRoot, "package-lock.json"),
    tauri: resolve(clientRoot, "src-tauri/tauri.conf.json"),
    cargo: resolve(clientRoot, "src-tauri/Cargo.toml"),
    cargoLock: resolve(clientRoot, "src-tauri/Cargo.lock"),
};

const [packageJson, packageLock, tauriConfig, cargoToml, cargoLock] =
    await Promise.all([
        readFile(files.package, "utf8").then(JSON.parse),
        readFile(files.packageLock, "utf8").then(JSON.parse),
        readFile(files.tauri, "utf8").then(JSON.parse),
        readFile(files.cargo, "utf8"),
        readFile(files.cargoLock, "utf8"),
    ]);
const cargoVersion = cargoToml.match(/^version\s*=\s*"([^"]+)"/m)?.[1];
const cargoLockVersion = cargoLock.match(
    /\[\[package\]\]\r?\nname = "srcclientclient"\r?\nversion = "([^"]+)"/,
)?.[1];
const versions = new Map([
    ["package.json", packageJson.version],
    ["package-lock.json", packageLock.version],
    ["package-lock.json packages['']", packageLock.packages?.[""]?.version],
    ["src-tauri/tauri.conf.json", tauriConfig.version],
    ["src-tauri/Cargo.toml", cargoVersion],
    ["src-tauri/Cargo.lock", cargoLockVersion],
]);
const expected = packageJson.version;

if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(expected)) {
    throw new Error(
        `Client version must use MAJOR.MINOR.PATCH, received: ${expected}`,
    );
}

const mismatches = [...versions].filter(([, version]) => version !== expected);
if (mismatches.length > 0) {
    const details = [...versions]
        .map(([file, version]) => `${file}: ${version ?? "missing"}`)
        .join("\n");
    throw new Error(`Client versions are not synchronized:\n${details}`);
}

console.log(`Client version ${expected} is synchronized.`);
