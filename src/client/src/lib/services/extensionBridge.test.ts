import { describe, expect, it } from "vitest";
import {
    isExtensionBridgeState,
    isExtensionInstallationInfo,
} from "$lib/services/extensionBridge";

describe("extension bridge boundaries", () => {
    it.each([
        "disconnected",
        "connected",
        "pairing_rejected",
        "version_mismatch",
    ] as const)("accepts the %s connection state", (connectionStatus) => {
        expect(
            isExtensionBridgeState({
                listenerStatus: "ready",
                connectionStatus,
                targetStatus: "missing",
                mode: "off",
            }),
        ).toBe(true);
    });

    it("rejects unknown bridge states", () => {
        expect(
            isExtensionBridgeState({
                listenerStatus: "ready",
                connectionStatus: "running",
                targetStatus: "missing",
                mode: "off",
            }),
        ).toBe(false);
    });

    it("validates installation paths and semantic versions", () => {
        expect(
            isExtensionInstallationInfo({
                path: "C:\\Users\\owner\\AppData\\Ascend\\extension",
                version: "0.1.0",
            }),
        ).toBe(true);
        expect(isExtensionInstallationInfo({ path: "", version: "dev" })).toBe(
            false,
        );
    });
});
