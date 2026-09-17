import { validateAxiomTokenUrl } from "./axiom-url";
import type { ContentNavigateRequest } from "../protocol/messages";
import type { NavigationResult } from "../types/navigation";

export type ContentNavigationDependencies = {
    getCurrentUrl: () => string;
    tryHistoryNavigation: (url: string) => Promise<boolean>;
};

export async function navigateInContent(
    request: ContentNavigateRequest,
    dependencies: ContentNavigationDependencies,
): Promise<NavigationResult> {
    const validation = validateAxiomTokenUrl(request.url);
    if (!validation.ok) {
        return {
            commandId: request.commandId,
            status: "failed",
            errorCode: validation.errorCode,
        };
    }

    const current = validateAxiomTokenUrl(dependencies.getCurrentUrl());
    if (current.ok && current.url === validation.url) {
        return {
            commandId: request.commandId,
            status: "ignored",
            errorCode: "already_open",
        };
    }

    if (await dependencies.tryHistoryNavigation(validation.url)) {
        return {
            commandId: request.commandId,
            status: "completed",
            method: "history",
        };
    }

    return {
        commandId: request.commandId,
        status: "failed",
        errorCode: "spa_navigation_unconfirmed",
    };
}
