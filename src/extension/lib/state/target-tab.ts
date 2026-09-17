import { isAxiomPageUrl } from "../navigation/axiom-url";
import type {
    ActivePageState,
    PopupSnapshot,
    TargetState,
} from "../types/popup";

const TARGET_STATE_KEY = "targetTabState";

export type TabCandidate = {
    id?: number;
    title?: string;
    url?: string;
};

export type TargetTabDependencies = {
    getSessionValue: (key: string) => Promise<unknown>;
    setSessionValue: (key: string, value: TargetState) => Promise<void>;
    getActiveTab: () => Promise<TabCandidate | null>;
    getTab: (tabId: number) => Promise<TabCandidate | null>;
};

export class TargetTabService {
    private state: TargetState = { kind: "idle" };

    constructor(private readonly dependencies: TargetTabDependencies) {}

    async initialize(): Promise<TargetState> {
        this.state = parseTargetState(
            await this.dependencies.getSessionValue(TARGET_STATE_KEY),
        );

        if (this.state.kind === "running") {
            const tab = await this.dependencies.getTab(this.state.tabId);
            if (!tab) {
                await this.pause("target_missing");
            } else if (!isAxiomPageUrl(tab.url)) {
                await this.pause("target_left_axiom");
            } else {
                await this.saveRunningTab(tab);
            }
        }

        return this.state;
    }

    getState(): TargetState {
        return this.state;
    }

    async getPopupSnapshot(): Promise<PopupSnapshot> {
        return {
            activePage: toActivePageState(
                await this.dependencies.getActiveTab(),
            ),
            target: this.state,
        };
    }

    async startOnActiveTab(): Promise<
        | { ok: true; state: PopupSnapshot }
        | { ok: false; errorCode: string; state: PopupSnapshot }
    > {
        const tab = await this.dependencies.getActiveTab();
        if (!tab || tab.id === undefined || !isAxiomPageUrl(tab.url)) {
            return {
                ok: false,
                errorCode: "active_tab_not_axiom",
                state: await this.getPopupSnapshot(),
            };
        }

        await this.saveRunningTab(tab);
        return { ok: true, state: await this.getPopupSnapshot() };
    }

    async stop(): Promise<PopupSnapshot> {
        this.state = { kind: "idle" };
        await this.persist();
        return this.getPopupSnapshot();
    }

    async handleTabRemoved(tabId: number): Promise<boolean> {
        if (this.state.kind !== "running" || this.state.tabId !== tabId) {
            return false;
        }
        await this.pause("target_closed");
        return true;
    }

    async handleTabUpdated(tabId: number, tab: TabCandidate): Promise<boolean> {
        if (this.state.kind !== "running" || this.state.tabId !== tabId) {
            return false;
        }
        if (!isAxiomPageUrl(tab.url)) {
            await this.pause("target_left_axiom");
        } else {
            await this.saveRunningTab(tab);
        }
        return true;
    }

    private async saveRunningTab(tab: TabCandidate): Promise<void> {
        if (tab.id === undefined || !isAxiomPageUrl(tab.url)) {
            await this.pause("target_missing");
            return;
        }
        this.state = {
            kind: "running",
            tabId: tab.id,
            title: tab.title?.trim() || "Axiom",
            url: tab.url,
        };
        await this.persist();
    }

    private async pause(
        reason: Extract<TargetState, { kind: "paused" }>["reason"],
    ): Promise<void> {
        this.state = { kind: "paused", reason };
        await this.persist();
    }

    private async persist(): Promise<void> {
        await this.dependencies.setSessionValue(TARGET_STATE_KEY, this.state);
    }
}

export function parseTargetState(value: unknown): TargetState {
    if (!isRecord(value) || typeof value.kind !== "string") {
        return { kind: "idle" };
    }
    if (value.kind === "idle") return { kind: "idle" };
    if (
        value.kind === "running" &&
        Number.isInteger(value.tabId) &&
        typeof value.tabId === "number" &&
        value.tabId >= 0 &&
        typeof value.title === "string" &&
        isAxiomPageUrl(value.url)
    ) {
        return {
            kind: "running",
            tabId: value.tabId,
            title: value.title,
            url: value.url,
        };
    }
    if (
        value.kind === "paused" &&
        (value.reason === "target_closed" ||
            value.reason === "target_left_axiom" ||
            value.reason === "target_missing")
    ) {
        return { kind: "paused", reason: value.reason };
    }
    return { kind: "idle" };
}

function toActivePageState(tab: TabCandidate | null): ActivePageState {
    if (!tab || tab.id === undefined) return { kind: "unavailable" };
    if (!isAxiomPageUrl(tab.url)) return { kind: "other" };
    return {
        kind: "axiom",
        tabId: tab.id,
        title: tab.title?.trim() || "Axiom",
        url: tab.url,
    };
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
