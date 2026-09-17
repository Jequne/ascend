import { describe, expect, it, vi } from "vitest";
import { navigateInContent } from "./content-navigation";

const commandId = "123e4567-e89b-42d3-a456-426614174000";

describe("content navigation", () => {
    it("rejects another origin without side effects", async () => {
        const tryHistoryNavigation = vi.fn();
        const assignCurrentPage = vi.fn();

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
                    assignCurrentPage,
                },
            ),
        ).resolves.toMatchObject({ status: "failed" });
        expect(tryHistoryNavigation).not.toHaveBeenCalled();
        expect(assignCurrentPage).not.toHaveBeenCalled();
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
                assignCurrentPage: vi.fn(),
            },
        );

        expect(result).toEqual({
            commandId,
            status: "ignored",
            errorCode: "already_open",
        });
    });

    it("reports confirmed history navigation", async () => {
        const assignCurrentPage = vi.fn();
        const result = await navigateInContent(request(), {
            getCurrentUrl: () => "https://axiom.trade/",
            tryHistoryNavigation: vi.fn().mockResolvedValue(true),
            assignCurrentPage,
        });

        expect(result).toMatchObject({
            status: "completed",
            method: "history",
        });
        expect(assignCurrentPage).not.toHaveBeenCalled();
    });

    it("falls back to a same-tab reload", async () => {
        const assignCurrentPage = vi.fn();
        const result = await navigateInContent(request(), {
            getCurrentUrl: () => "https://axiom.trade/",
            tryHistoryNavigation: vi.fn().mockResolvedValue(false),
            assignCurrentPage,
        });

        expect(result).toMatchObject({
            status: "completed",
            method: "same_tab_reload",
        });
        await new Promise<void>((resolve) => setTimeout(resolve, 0));
        expect(assignCurrentPage).toHaveBeenCalledWith(
            "https://axiom.trade/meme/pair?chain=sol",
        );
    });
});

function request() {
    return {
        type: "content_navigate" as const,
        commandId,
        url: "https://axiom.trade/meme/pair?chain=sol",
    };
}
