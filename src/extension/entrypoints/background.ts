import { browser } from "wxt/browser";
import { defineBackground } from "wxt/utils/define-background";
import { ExtensionBridgeClient, isPairingSecret } from "../lib/bridge/client";
import { validateAxiomTokenUrl } from "../lib/navigation/axiom-url";
import { NavigationQueue } from "../lib/navigation/navigation-queue";
import {
    parseInternalRequest,
    parseNavigationResult,
    type ContentNavigateRequest,
    type InternalResponse,
} from "../lib/protocol/messages";
import { TargetTabService, type TabCandidate } from "../lib/state/target-tab";
import type {
    NavigateCommand,
    NavigationResult,
} from "../lib/types/navigation";
import type { ExtensionBridgeSnapshot } from "../lib/types/bridge";

const PAIRING_SECRET_STORAGE_KEY = "ascend.extensionBridge.pairingSecret";

export default defineBackground({
    type: "module",
    main() {
        const targetTabs = new TargetTabService({
            getSessionValue: async (key) => {
                const stored = await browser.storage.session.get(key);
                return stored[key];
            },
            setSessionValue: async (key, value) => {
                await browser.storage.session.set({ [key]: value });
            },
            getActiveTab: async () => {
                const [tab] = await browser.tabs.query({
                    active: true,
                    currentWindow: true,
                });
                return tab ? toTabCandidate(tab) : null;
            },
            getTab: async (tabId) => {
                try {
                    return toTabCandidate(await browser.tabs.get(tabId));
                } catch {
                    return null;
                }
            },
        });

        const navigationQueue = new NavigationQueue((command) =>
            executeNavigation(command, targetTabs),
        );
        const initialized = targetTabs.initialize();
        let bridgeSnapshot: ExtensionBridgeSnapshot = {
            connection: "unpaired",
            mode: "off",
            reconnectAttempt: 0,
        };
        const bridge = new ExtensionBridgeClient({
            getSecret: async () => {
                const stored = await browser.storage.local.get(
                    PAIRING_SECRET_STORAGE_KEY,
                );
                const secret = stored[PAIRING_SECRET_STORAGE_KEY];
                return typeof secret === "string" ? secret : null;
            },
            getExtensionVersion: () => browser.runtime.getManifest().version,
            onSnapshot: (snapshot) => {
                const reconnected =
                    snapshot.connection === "connected" &&
                    bridgeSnapshot.connection !== "connected";
                bridgeSnapshot = snapshot;
                if (snapshot.connection !== "connected") {
                    navigationQueue.cancelActive("bridge_disconnected");
                }
                if (reconnected && snapshot.mode === "current_axiom_tab") {
                    void initialized.then(async () => {
                        if (targetTabs.getState().kind === "running") {
                            await bridge.requestMode("current_axiom_tab");
                        }
                    });
                }
                if (
                    snapshot.connection === "connected" &&
                    snapshot.mode !== "current_axiom_tab"
                ) {
                    navigationQueue.cancelActive("mode_off");
                    void initialized.then(() => targetTabs.stop());
                }
            },
            onNavigate: async (command) =>
                submitNavigation(command, navigationQueue),
        });
        void bridge.start();

        browser.runtime.onMessage.addListener(
            (message, _sender, sendResponse) => {
                const request = parseInternalRequest(message);
                if (!request) {
                    sendResponse({
                        type: "invalid_request",
                        errorCode: "invalid_message",
                    } satisfies InternalResponse);
                    return false;
                }

                void initialized
                    .then(async () => {
                        if (request.type === "get_popup_state") {
                            return {
                                type: "popup_state",
                                state: {
                                    ...(await targetTabs.getPopupSnapshot()),
                                    bridge: bridgeSnapshot,
                                },
                            } satisfies InternalResponse;
                        }
                        if (request.type === "pair_bridge") {
                            const pairingCode = request.pairingCode.trim();
                            if (!isPairingSecret(pairingCode)) {
                                return {
                                    type: "action_result",
                                    ok: false,
                                    errorCode: "invalid_pairing_code",
                                    state: {
                                        ...(await targetTabs.getPopupSnapshot()),
                                        bridge: bridge.getSnapshot(),
                                    },
                                } satisfies InternalResponse;
                            }
                            try {
                                await bridge.pair(pairingCode);
                                await browser.storage.local.set({
                                    [PAIRING_SECRET_STORAGE_KEY]: pairingCode,
                                });
                                return {
                                    type: "action_result",
                                    ok: true,
                                    state: {
                                        ...(await targetTabs.getPopupSnapshot()),
                                        bridge: bridge.getSnapshot(),
                                    },
                                } satisfies InternalResponse;
                            } catch {
                                return {
                                    type: "action_result",
                                    ok: false,
                                    errorCode: "pairing_failed",
                                    state: {
                                        ...(await targetTabs.getPopupSnapshot()),
                                        bridge: bridge.getSnapshot(),
                                    },
                                } satisfies InternalResponse;
                            }
                        }
                        if (request.type === "retry_bridge") {
                            bridge.retry();
                            return {
                                type: "action_result",
                                ok: true,
                                state: {
                                    ...(await targetTabs.getPopupSnapshot()),
                                    bridge: bridge.getSnapshot(),
                                },
                            } satisfies InternalResponse;
                        }
                        if (request.type === "start_target") {
                            const result = await targetTabs.startOnActiveTab();
                            if (result.ok) {
                                const accepted =
                                    await bridge.requestMode(
                                        "current_axiom_tab",
                                    );
                                if (!accepted) {
                                    await targetTabs.stop();
                                    return {
                                        type: "action_result",
                                        ok: false,
                                        errorCode: "bridge_not_connected",
                                        state: {
                                            ...(await targetTabs.getPopupSnapshot()),
                                            bridge: bridge.getSnapshot(),
                                        },
                                    } satisfies InternalResponse;
                                }
                            }
                            return {
                                type: "action_result",
                                ...result,
                                state: {
                                    ...result.state,
                                    bridge: bridge.getSnapshot(),
                                },
                            } satisfies InternalResponse;
                        }
                        if (request.type === "stop_target") {
                            navigationQueue.cancelActive("mode_off");
                            const accepted = await bridge.requestMode("off");
                            const state = {
                                ...(await targetTabs.stop()),
                                bridge: bridge.getSnapshot(),
                            };
                            return accepted
                                ? ({
                                      type: "action_result",
                                      ok: true,
                                      state,
                                  } satisfies InternalResponse)
                                : ({
                                      type: "action_result",
                                      ok: false,
                                      errorCode: "bridge_not_connected",
                                      state,
                                  } satisfies InternalResponse);
                        }

                        return {
                            type: "navigation_result",
                            result: await submitNavigation(
                                request,
                                navigationQueue,
                            ),
                        } satisfies InternalResponse;
                    })
                    .then(sendResponse);
                return true;
            },
        );

        browser.tabs.onRemoved.addListener((tabId) => {
            void initialized.then(async () => {
                if (await targetTabs.handleTabRemoved(tabId)) {
                    navigationQueue.cancelActive("target_missing");
                }
            });
        });

        browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (
                changeInfo.url === undefined &&
                changeInfo.title === undefined
            ) {
                return;
            }
            void initialized.then(async () => {
                if (
                    await targetTabs.handleTabUpdated(
                        tabId,
                        toTabCandidate(tab),
                    )
                ) {
                    const state = targetTabs.getState();
                    if (state.kind !== "running") {
                        navigationQueue.cancelActive("target_missing");
                    }
                }
            });
        });
    },
});

async function executeNavigation(
    command: NavigateCommand,
    targetTabs: TargetTabService,
): Promise<NavigationResult> {
    const state = targetTabs.getState();
    if (state.kind !== "running") {
        return {
            commandId: command.commandId,
            status: "ignored",
            errorCode: "target_missing",
        };
    }

    const request: ContentNavigateRequest = {
        type: "content_navigate",
        commandId: command.commandId,
        url: command.url,
    };
    try {
        const response: unknown = await browser.tabs.sendMessage(
            state.tabId,
            request,
        );
        const result = parseNavigationResult(response);
        if (!result || result.commandId !== command.commandId) {
            return {
                commandId: command.commandId,
                status: "failed",
                errorCode: "invalid_content_response",
            };
        }
        return result;
    } catch {
        return {
            commandId: command.commandId,
            status: "failed",
            errorCode: "content_unavailable",
        };
    }
}

async function submitNavigation(
    command: NavigateCommand,
    navigationQueue: NavigationQueue,
): Promise<NavigationResult> {
    const validation = validateAxiomTokenUrl(command.url);
    if (!validation.ok) {
        return {
            commandId: command.commandId,
            status: "failed",
            errorCode: validation.errorCode,
        };
    }
    return navigationQueue.submit({ ...command, url: validation.url });
}

function toTabCandidate(tab: {
    id?: number;
    title?: string;
    url?: string;
}): TabCandidate {
    return {
        ...(tab.id === undefined ? {} : { id: tab.id }),
        ...(tab.title === undefined ? {} : { title: tab.title }),
        ...(tab.url === undefined ? {} : { url: tab.url }),
    };
}
