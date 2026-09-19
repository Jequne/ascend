import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const extensionRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const [packageJson, packageLock] = await Promise.all([
    readFile(resolve(extensionRoot, "package.json"), "utf8").then(JSON.parse),
    readFile(resolve(extensionRoot, "package-lock.json"), "utf8").then(
        JSON.parse,
    ),
]);
const expected = packageJson.version;

if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(expected)) {
    throw new Error(
        `Extension version must use MAJOR.MINOR.PATCH, received: ${expected}`,
    );
}

if (
    packageLock.version !== expected ||
    packageLock.packages?.[""]?.version !== expected
) {
    throw new Error(
        "Extension versions in package.json and package-lock.json are not synchronized.",
    );
}

console.log(`Extension version ${expected} is synchronized.`);
