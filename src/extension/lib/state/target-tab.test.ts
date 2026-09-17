import { describe, expect, it } from "vitest";
import {
    TargetTabService,
    parseTargetState,
    type TabCandidate,
} from "./target-tab";
import type { TargetState } from "../types/popup";

describe("TargetTabService", () => {
    it("assigns only an active exact-origin Axiom tab", async () => {
        const harness = createHarness();
        const service = new TargetTabService(harness.dependencies);
        await service.initialize();

        await expect(service.startOnActiveTab()).resolves.toMatchObject({
            ok: false,
            errorCode: "active_tab_not_axiom",
        });

        harness.activeTab = {
            id: 42,
            title: "Token · Axiom",
            url: "https://axiom.trade/meme/pair?chain=sol",
        };
        await expect(service.startOnActiveTab()).resolves.toMatchObject({
            ok: true,
            state: { target: { kind: "running", tabId: 42 } },
        });
        expect(harness.stored).toMatchObject({
            kind: "running",
            tabId: 42,
        });
    });

    it("restores a valid session target after service-worker restart", async () => {
        const harness = createHarness({
            kind: "running",
            tabId: 8,
            title: "Old title",
            url: "https://axiom.trade/",
        });
        harness.tabs.set(8, {
            id: 8,
            title: "Current token",
            url: "https://axiom.trade/meme/pair?chain=bsc",
        });

        const service = new TargetTabService(harness.dependencies);
        await expect(service.initialize()).resolves.toEqual({
            kind: "running",
            tabId: 8,
            title: "Current token",
            url: "https://axiom.trade/meme/pair?chain=bsc",
        });
    });

    it("pauses when the target closes or leaves Axiom", async () => {
        const harness = createHarness();
        harness.activeTab = {
            id: 17,
            title: "Axiom",
            url: "https://axiom.trade/",
        };
        const service = new TargetTabService(harness.dependencies);
        await service.initialize();
        await service.startOnActiveTab();

        await expect(service.handleTabRemoved(99)).resolves.toBe(false);
        await expect(
            service.handleTabUpdated(17, {
                id: 17,
                title: "Other",
                url: "https://example.com/",
            }),
        ).resolves.toBe(true);
        expect(service.getState()).toEqual({
            kind: "paused",
            reason: "target_left_axiom",
        });

        harness.activeTab = {
            id: 18,
            title: "Axiom",
            url: "https://axiom.trade/",
        };
        await service.startOnActiveTab();
        await service.handleTabRemoved(18);
        expect(service.getState()).toEqual({
            kind: "paused",
            reason: "target_closed",
        });
    });

    it("safely normalizes malformed stored state", () => {
        expect(parseTargetState(null)).toEqual({ kind: "idle" });
        expect(
            parseTargetState({
                kind: "running",
                tabId: 5,
                title: "Spoof",
                url: "https://axiom.trade.evil.example/",
            }),
        ).toEqual({ kind: "idle" });
    });
});

function createHarness(initialStored: unknown = { kind: "idle" }) {
    const harness: {
        stored: unknown;
        activeTab: TabCandidate | null;
        tabs: Map<number, TabCandidate>;
        dependencies: {
            getSessionValue: () => Promise<unknown>;
            setSessionValue: (key: string, value: TargetState) => Promise<void>;
            getActiveTab: () => Promise<TabCandidate | null>;
            getTab: (tabId: number) => Promise<TabCandidate | null>;
        };
    } = {
        stored: initialStored,
        activeTab: {
            id: 1,
            title: "Other",
            url: "https://example.com/",
        },
        tabs: new Map(),
        dependencies: {
            getSessionValue: async () => harness.stored,
            setSessionValue: async (_key, value) => {
                harness.stored = value;
            },
            getActiveTab: async () => harness.activeTab,
            getTab: async (tabId) => harness.tabs.get(tabId) ?? null,
        },
    };
    return harness;
}
