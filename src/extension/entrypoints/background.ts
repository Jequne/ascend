import { browser } from "wxt/browser";
import { defineBackground } from "wxt/utils/define-background";
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
                                state: await targetTabs.getPopupSnapshot(),
                            } satisfies InternalResponse;
                        }
                        if (request.type === "start_target") {
                            const result = await targetTabs.startOnActiveTab();
                            return {
                                type: "action_result",
                                ...result,
                            } satisfies InternalResponse;
                        }
                        if (request.type === "stop_target") {
                            navigationQueue.clearPending("mode_off");
                            return {
                                type: "action_result",
                                ok: true,
                                state: await targetTabs.stop(),
                            } satisfies InternalResponse;
                        }

                        const validation = validateAxiomTokenUrl(request.url);
                        if (!validation.ok) {
                            return {
                                type: "navigation_result",
                                result: {
                                    commandId: request.commandId,
                                    status: "failed",
                                    errorCode: validation.errorCode,
                                },
                            } satisfies InternalResponse;
                        }

                        return {
                            type: "navigation_result",
                            result: await navigationQueue.submit({
                                commandId: request.commandId,
                                issuedAt: request.issuedAt,
                                url: validation.url,
                            }),
                        } satisfies InternalResponse;
                    })
                    .then(sendResponse);
                return true;
            },
        );

        browser.tabs.onRemoved.addListener((tabId) => {
            void initialized.then(async () => {
                if (await targetTabs.handleTabRemoved(tabId)) {
                    navigationQueue.clearPending("target_missing");
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
                        navigationQueue.clearPending("target_missing");
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
