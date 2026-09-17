import { describe, expect, it, vi } from "vitest";
import { navigateInContent } from "./content-navigation";

const commandId = "123e4567-e89b-42d3-a456-426614174000";

describe("content navigation", () => {
    it("rejects another origin without side effects", async () => {
        const tryHistoryNavigation = vi.fn();

        await expect(
            navigateInContent(
                {
                    type: "content_navigate",
                    commandId,
                    url: "https://evil.example/meme/pair?chain=sol",
                },
                {
                    getCurrentUrl: () => "https://axiom.trade/",
                    tryHistoryNavigation,
                },
            ),
        ).resolves.toMatchObject({ status: "failed" });
        expect(tryHistoryNavigation).not.toHaveBeenCalled();
    });

    it("ignores an already open normalized URL", async () => {
        const result = await navigateInContent(
            {
                type: "content_navigate",
                commandId,
                url: "https://axiom.trade/meme/pair?trackerChains=sol&chain=sol",
            },
            {
                getCurrentUrl: () =>
                    "https://axiom.trade/meme/pair?chain=sol&trackerChains=sol",
                tryHistoryNavigation: vi.fn(),
            },
        );

        expect(result).toEqual({
            commandId,
            status: "ignored",
            errorCode: "already_open",
        });
    });

    it("reports confirmed history navigation", async () => {
        const result = await navigateInContent(request(), {
            getCurrentUrl: () => "https://axiom.trade/",
            tryHistoryNavigation: vi.fn().mockResolvedValue(true),
        });

        expect(result).toMatchObject({
            status: "completed",
            method: "history",
        });
    });

    it("fails safely without reloading when SPA navigation is unconfirmed", async () => {
        const result = await navigateInContent(request(), {
            getCurrentUrl: () => "https://axiom.trade/",
            tryHistoryNavigation: vi.fn().mockResolvedValue(false),
        });

        expect(result).toEqual({
            commandId,
            status: "failed",
            errorCode: "spa_navigation_unconfirmed",
        });
    });
});

function request() {
    return {
        type: "content_navigate" as const,
        commandId,
        url: "https://axiom.trade/meme/pair?chain=sol",
    };
}
