import { fireEvent, render, screen } from "@testing-library/svelte";
import { afterEach, describe, expect, it, vi } from "vitest";
import { tick } from "svelte";
import RetryingTokenImage from "./RetryingTokenImage.svelte";

describe("RetryingTokenImage", () => {
    afterEach(() => {
        vi.useRealTimers();
    });

    it("retries a fresh image with bounded cache-busting requests", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            src: "https://cdn.example/token.png?size=64#image",
            alt: "EXM token",
        });

        const image = screen.getByRole("img", { name: "EXM token" });
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64#image",
        );
        expect(image).toHaveClass("opacity-0");

        await fireEvent.error(image);
        await vi.advanceTimersByTimeAsync(1_000);
        await tick();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=1#image",
        );

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
        await vi.runAllTimersAsync();
        expect(image).toHaveAttribute(
            "src",
            "https://cdn.example/token.png?size=64&_ascend_retry=3#image",
        );
    });

    it("reveals a successfully loaded image without scheduling retries", async () => {
        vi.useFakeTimers();
        render(RetryingTokenImage, {
            src: "https://cdn.example/token.png",
            alt: "EXM token",
        });

        const image = screen.getByRole("img", { name: "EXM token" });
        await fireEvent.load(image);
        await vi.runAllTimersAsync();

        expect(image).not.toHaveClass("opacity-0");
        expect(image).toHaveAttribute("src", "https://cdn.example/token.png");
    });
});
