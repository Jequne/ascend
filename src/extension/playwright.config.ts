import { defineConfig } from "playwright/test";

export default defineConfig({
    testDir: "./e2e",
    fullyParallel: false,
    workers: 1,
    timeout: 30_000,
    expect: {
        timeout: 5_000,
    },
    outputDir: "./e2e/.tmp/test-results",
    reporter: "line",
    use: {
        trace: "retain-on-failure",
    },
});
