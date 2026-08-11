import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import AuthBox from "./AuthBox.svelte";

describe("AuthBox", () => {
    it("renders the activation form", () => {
        render(AuthBox);

        expect(
            screen.getByRole("heading", { name: "License Required" }),
        ).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Activate" })).toBeEnabled();
    });
});
