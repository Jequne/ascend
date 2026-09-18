import { mkdir, mkdtemp, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
    chromium,
    test as base,
    type BrowserContext,
    type Page,
} from "playwright/test";
import { E2E_PAIRING_CODE, MockBridge } from "./mock-bridge";

type ExtensionFixtures = {
    context: BrowserContext;
    extensionId: string;
    installAxiomFixture: () => Promise<void>;
    mockBridge: MockBridge;
    pairExtension: (page: Page) => Promise<void>;
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
    mockBridge: async ({ extensionId }, use) => {
        const bridge = await MockBridge.start(extensionId);
        await use(bridge);
        await bridge.close();
    },
    pairExtension: async ({ mockBridge }, use) => {
        void mockBridge;
        await use(async (page) => {
            const response: unknown = await page.evaluate(
                async (pairingCode) => {
                    const extensionGlobal = globalThis as unknown as {
                        chrome: {
                            runtime: {
                                sendMessage: (
                                    message: unknown,
                                ) => Promise<unknown>;
                            };
                        };
                    };
                    return extensionGlobal.chrome.runtime.sendMessage({
                        type: "pair_bridge",
                        pairingCode,
                    });
                },
                E2E_PAIRING_CODE,
            );
            if (!isSuccessfulAction(response)) {
                throw new Error("extension_pairing_failed");
            }
        });
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

function isSuccessfulAction(value: unknown): boolean {
    return (
        typeof value === "object" &&
        value !== null &&
        "type" in value &&
        value.type === "action_result" &&
        "ok" in value &&
        value.ok === true
    );
}
