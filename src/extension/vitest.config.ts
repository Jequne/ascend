import { svelteTesting } from "@testing-library/svelte/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { configDefaults, defineConfig } from "vitest/config";
import { WxtVitest } from "wxt/testing/vitest-plugin";

export default defineConfig({
    plugins: [svelte(), svelteTesting(), WxtVitest()],
    test: {
        environment: "jsdom",
        exclude: [...configDefaults.exclude, "e2e/**"],
        setupFiles: ["./vitest-setup.ts"],
    },
});
