import { mkdir, mkdtemp, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium, test as base, type BrowserContext } from "playwright/test";

type ExtensionFixtures = {
    context: BrowserContext;
    extensionId: string;
    installAxiomFixture: () => Promise<void>;
};

export const test = base.extend<ExtensionFixtures>({
    context: async ({ browserName }, use) => {
        void browserName;
        const extensionPath = resolve(".output/chrome-mv3");
        const profileRoot = resolve("e2e/.tmp/profiles");
        await mkdir(profileRoot, { recursive: true });
        const profilePath = await mkdtemp(resolve(profileRoot, "chromium-"));
        const context = await chromium.launchPersistentContext(profilePath, {
            channel: "chromium",
            headless: true,
            args: [
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`,
            ],
        });

        await use(context);
        await context.close();
    },
    extensionId: async ({ context }, use) => {
        let [serviceWorker] = context.serviceWorkers();
        serviceWorker ??= await context.waitForEvent("serviceworker");
        const extensionId = new URL(serviceWorker.url()).hostname;
        await use(extensionId);
    },
    installAxiomFixture: async ({ context }, use) => {
        const fixture = await readFile(
            resolve("e2e/fixture/axiom.html"),
            "utf8",
        );
        await context.route("https://axiom.trade/**", async (route) => {
            if (route.request().resourceType() === "document") {
                if (
                    new URL(route.request().url()).pathname.endsWith(
                        "/slow-pair",
                    )
                ) {
                    await new Promise<void>((resolveDelay) =>
                        setTimeout(resolveDelay, 350),
                    );
                }
                await route.fulfill({
                    status: 200,
                    contentType: "text/html; charset=utf-8",
                    body: fixture,
                });
                return;
            }
            await route.abort();
        });
        await use(async () => undefined);
    },
});

export const expect = test.expect;
