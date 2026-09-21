import { fireEvent, render, screen } from "@testing-library/svelte";
import { afterEach, describe, expect, it, vi } from "vitest";
import { tick } from "svelte";
import RetryingTokenImage from "./RetryingTokenImage.svelte";

describe("RetryingTokenImage", () => {
    afterEach(() => {
        vi.useRealTimers();
    });

    it("keeps retrying the final source after the initial failures", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            sources: ["https://cdn.example/token.png?size=64#image"],
            alt: "EXM token",
        });

        const image = screen.getByRole("img", { name: "EXM token" });
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64#image",
        );
        expect(image).not.toHaveClass("opacity-0");

        await fireEvent.error(image);
        await vi.advanceTimersByTimeAsync(1_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=1#image",
        );
        expect(image).not.toHaveClass("opacity-0");

        await fireEvent.error(image);
        await vi.advanceTimersByTimeAsync(2_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=2#image",
        );

        await fireEvent.error(image);
        await vi.advanceTimersByTimeAsync(4_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=3#image",
        );

        await fireEvent.error(image);
        await vi.advanceTimersByTimeAsync(8_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=4#image",
        );

        await fireEvent.load(image);
        expect(vi.getTimerCount()).toBe(0);
    });

    it("keeps a valid image visible without waiting for a load event", () => {
        render(RetryingTokenImage, {
            sources: ["https://cdn.example/cached-token.png"],
            alt: "CACHED token",
        });

        const image = screen.getByRole("img", { name: "CACHED token" });

        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/cached-token.png",
        );
        expect(image).not.toHaveClass("opacity-0");
    });

    it("reveals a successfully loaded image without scheduling retries", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            sources: ["https://cdn.example/token.png"],
            alt: "EXM token",
        });

        const image = screen.getByRole("img", { name: "EXM token" });
        await fireEvent.load(image);
        await vi.runAllTimersAsync();

        expect(image).not.toHaveClass("opacity-0");
        expect(image).toHaveAttribute("src", "https://cdn.example/token.png");
    });

    it("uses the next candidate immediately when the supplied image fails", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            sources: [
                "https://origin.example/token.png",
                "https://cdn.example/token.webp",
            ],
            alt: "EXM token",
        });

        const image = screen.getByRole("img", { name: "EXM token" });
        await fireEvent.error(image);
        await tick();

        expect(image).toHaveAttribute("src", "https://cdn.example/token.webp");
        expect(vi.getTimerCount()).toBe(0);
    });

    it("rechecks earlier sources when the final fallback fails", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            sources: [
                "https://origin.example/token.png",
                "https://cdn.example/token.webp",
            ],
            alt: "OLD token",
        });

        const image = screen.getByRole("img", { name: "OLD token" });
        await fireEvent.error(image);
        await fireEvent.error(image);

        expect(image).toHaveAttribute("src", "https://cdn.example/token.webp");
        expect(image).toHaveClass("opacity-0");
        await vi.advanceTimersByTimeAsync(1_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://origin.example/token.png?_ascend_retry=1",
        );

        await fireEvent.error(image);
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.webp?_ascend_retry=1",
        );
        await fireEvent.load(image);
        expect(image).not.toHaveClass("opacity-0");
        expect(vi.getTimerCount()).toBe(0);
    });

    it("caps the delay between repeated failures", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            sources: ["https://cdn.example/token.webp"],
            alt: "OLD token",
        });

        const image = screen.getByRole("img", { name: "OLD token" });
        const delays = [
            1_000, 2_000, 4_000, 8_000, 16_000, 30_000, 60_000, 300_000,
            300_000,
        ];
        for (const [index, delay] of delays.entries()) {
            await fireEvent.error(image);
            await vi.advanceTimersByTimeAsync(delay - 1);
            expect(image).toHaveAttribute(
                "src",
                index === 0
                    ? "https://cdn.example/token.webp"
                    : `https://cdn.example/token.webp?_ascend_retry=${index}`,
            );
            await vi.advanceTimersByTimeAsync(1);
            await tick();
            expect(image).toHaveAttribute(
                "src",
                `https://cdn.example/token.webp?_ascend_retry=${index + 1}`,
            );
        }
    });

    it("stops retrying when the token card is removed", async () => {
        vi.useFakeTimers();
        const { unmount } = render(RetryingTokenImage, {
            sources: ["https://cdn.example/token.webp"],
            alt: "OLD token",
        });

        await fireEvent.error(screen.getByRole("img", { name: "OLD token" }));
        expect(vi.getTimerCount()).toBe(1);

        unmount();
        expect(vi.getTimerCount()).toBe(0);
    });
});
