import type { Page } from "playwright/test";
import { expect, test } from "./fixtures";

const validCommandId = "123e4567-e89b-42d3-a456-426614174000";

test("assigns one Axiom target and navigates without reload, a new tab, or focus", async ({
    context,
    extensionId,
    installAxiomFixture,
}) => {
    await installAxiomFixture();
    const targetPage = await context.newPage();
    await targetPage.goto("https://axiom.trade/");
    const extensionPage = await context.newPage();
    await extensionPage.goto(`chrome-extension://${extensionId}/popup.html`);

    await targetPage.bringToFront();
    await expect
        .poll(async () => {
            const response = await sendExtensionMessage(extensionPage, {
                type: "get_popup_state",
            });
            return isPopupState(response)
                ? response.state.activePage.kind
                : "invalid";
        })
        .toBe("axiom");

    const startResponse = await sendExtensionMessage(extensionPage, {
        type: "start_target",
    });
    expect(startResponse).toMatchObject({
        type: "action_result",
        ok: true,
        state: { target: { kind: "running" } },
    });

    const observerPage = await context.newPage();
    await observerPage.goto("about:blank");
    await observerPage.bringToFront();
    const activeTabBefore = await getActiveTabId(extensionPage);
    const pageCountBefore = context.pages().length;
    const documentIdBefore = await getFixtureDocumentId(targetPage);

    const rejectedResponse = await sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: validCommandId,
        url: "https://axiom.trade.evil.example/meme/pair?chain=sol",
        issuedAt: "2026-09-17T12:00:00.000Z",
    });
    expect(rejectedResponse).toMatchObject({
        type: "navigation_result",
        result: { status: "failed", errorCode: "invalid_origin" },
    });
    await expect(targetPage).toHaveURL("https://axiom.trade/");

    const navigationResponse = await sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174001",
        url: "https://axiom.trade/meme/pair-one?chain=sol",
        issuedAt: "2026-09-17T12:00:01.000Z",
    });
    expect(navigationResponse).toMatchObject({
        type: "navigation_result",
        result: { status: "completed", method: "history" },
    });
    await expect(targetPage).toHaveURL(
        "https://axiom.trade/meme/pair-one?chain=sol",
    );
    await expect(targetPage.locator("#rendered-token")).toHaveText("pair-one");
    expect(await getFixtureDocumentId(targetPage)).toBe(documentIdBefore);
    expect(await getFixtureNavigationCount(targetPage)).toBe(1);
    expect(context.pages()).toHaveLength(pageCountBefore);
    expect(await getActiveTabId(extensionPage)).toBe(activeTabBefore);

    await targetPage.close();
    await expect
        .poll(async () => {
            const response = await sendExtensionMessage(extensionPage, {
                type: "get_popup_state",
            });
            return isPopupState(response)
                ? response.state.target.kind
                : "invalid";
        })
        .toBe("paused");
    const missingTargetResponse = await sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174002",
        url: "https://axiom.trade/meme/pair-two?chain=sol",
        issuedAt: "2026-09-17T12:00:02.000Z",
    });
    expect(missingTargetResponse).toMatchObject({
        type: "navigation_result",
        result: { status: "ignored", errorCode: "target_missing" },
    });
});

test("deduplicates commands and keeps only the latest pending token", async ({
    context,
    extensionId,
    installAxiomFixture,
}) => {
    await installAxiomFixture();
    const targetPage = await context.newPage();
    await targetPage.goto("https://axiom.trade/");
    const extensionPage = await context.newPage();
    await extensionPage.goto(`chrome-extension://${extensionId}/popup.html`);
    await targetPage.bringToFront();
    await expect
        .poll(async () => {
            const response = await sendExtensionMessage(extensionPage, {
                type: "start_target",
            });
            return isSuccessfulAction(response);
        })
        .toBe(true);

    const observerPage = await context.newPage();
    await observerPage.goto("about:blank");
    await observerPage.bringToFront();
    const activeTabBefore = await getActiveTabId(extensionPage);
    const pageCountBefore = context.pages().length;

    const first = sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174010",
        url: "https://axiom.trade/meme/slow-pair?chain=sol",
        issuedAt: "2026-09-17T12:01:00.000Z",
    });
    await delay(40);
    const superseded = sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174011",
        url: "https://axiom.trade/meme/pair-two?chain=sol",
        issuedAt: "2026-09-17T12:01:01.000Z",
    });
    await delay(20);
    const latest = sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174012",
        url: "https://axiom.trade/meme/pair-three?chain=sol",
        issuedAt: "2026-09-17T12:01:02.000Z",
    });

    await expect(first).resolves.toMatchObject({
        result: { status: "completed", method: "history" },
    });
    await expect(superseded).resolves.toMatchObject({
        result: { status: "superseded" },
    });
    await expect(latest).resolves.toMatchObject({
        result: { status: "completed", method: "history" },
    });
    await expect(targetPage).toHaveURL(
        "https://axiom.trade/meme/pair-three?chain=sol",
    );

    const duplicate = await sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174012",
        url: "https://axiom.trade/meme/must-not-open?chain=sol",
        issuedAt: "2026-09-17T12:01:03.000Z",
    });
    expect(duplicate).toMatchObject({
        result: { status: "completed", method: "history" },
    });
    await expect(targetPage).toHaveURL(
        "https://axiom.trade/meme/pair-three?chain=sol",
    );
    await expect(targetPage.locator("#rendered-token")).toHaveText(
        "pair-three",
    );

    const alreadyOpen = await sendExtensionMessage(extensionPage, {
        type: "navigate_target",
        commandId: "123e4567-e89b-42d3-a456-426614174013",
        url: "https://axiom.trade/meme/pair-three?chain=sol",
        issuedAt: "2026-09-17T12:01:04.000Z",
    });
    expect(alreadyOpen).toMatchObject({
        result: { status: "ignored", errorCode: "already_open" },
    });
    expect(context.pages()).toHaveLength(pageCountBefore);
    expect(await getActiveTabId(extensionPage)).toBe(activeTabBefore);
});

async function sendExtensionMessage(
    page: Page,
    message: Record<string, unknown>,
): Promise<unknown> {
    return page.evaluate(async (request) => {
        const extensionGlobal = globalThis as unknown as {
            chrome: {
                runtime: {
                    sendMessage: (message: unknown) => Promise<unknown>;
                };
            };
        };
        return extensionGlobal.chrome.runtime.sendMessage(request);
    }, message);
}

async function getActiveTabId(page: Page): Promise<number | undefined> {
    return page.evaluate(async () => {
        const extensionGlobal = globalThis as unknown as {
            chrome: {
                tabs: {
                    query: (
                        query: Record<string, unknown>,
                    ) => Promise<Array<{ id?: number }>>;
                };
            };
        };
        const [tab] = await extensionGlobal.chrome.tabs.query({
            active: true,
            currentWindow: true,
        });
        return tab?.id;
    });
}

function isPopupState(value: unknown): value is {
    type: "popup_state";
    state: { activePage: { kind: string }; target: { kind: string } };
} {
    return (
        typeof value === "object" &&
        value !== null &&
        "type" in value &&
        value.type === "popup_state" &&
        "state" in value &&
        typeof value.state === "object" &&
        value.state !== null &&
        "activePage" in value.state &&
        typeof value.state.activePage === "object" &&
        value.state.activePage !== null &&
        "kind" in value.state.activePage &&
        typeof value.state.activePage.kind === "string" &&
        "target" in value.state &&
        typeof value.state.target === "object" &&
        value.state.target !== null &&
        "kind" in value.state.target &&
        typeof value.state.target.kind === "string"
    );
}

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

function delay(durationMs: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, durationMs));
}

async function getFixtureDocumentId(page: Page): Promise<string> {
    return page.evaluate(() => {
        const fixtureGlobal = globalThis as unknown as {
            __fixtureDocumentId: string;
        };
        return fixtureGlobal.__fixtureDocumentId;
    });
}

async function getFixtureNavigationCount(page: Page): Promise<number> {
    return page.evaluate(() => {
        const fixtureGlobal = globalThis as unknown as {
            __fixtureNavigationCount: number;
        };
        return fixtureGlobal.__fixtureNavigationCount;
    });
}
