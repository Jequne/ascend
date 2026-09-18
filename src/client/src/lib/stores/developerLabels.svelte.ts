import { normalizeDeveloperLabels } from "$lib/config/settings";
import { settingsStore } from "$lib/stores/settings.svelte";
import type { DeveloperLabels } from "$lib/types";

function walletLookupKey(wallet: string): string {
    const trimmedWallet = wallet.trim();
    return trimmedWallet.startsWith("0x")
        ? trimmedWallet.toLowerCase()
        : trimmedWallet;
}

class DeveloperLabelsStore {
    get labels(): DeveloperLabels {
        return settingsStore.getSection("developerLabels") ?? {};
    }

    getLabel(wallet: string): string {
        const target = walletLookupKey(wallet);
        const match = Object.entries(this.labels).find(
            ([candidate]) => walletLookupKey(candidate) === target,
        );
        return match?.[1] ?? "";
    }

    replace(labels: unknown): void {
        settingsStore.replaceSection(
            "developerLabels",
            normalizeDeveloperLabels(labels),
        );
    }

    setLabel(wallet: string, label: string): void {
        const trimmedWallet = wallet.trim();
        if (!trimmedWallet) return;

        const nextLabels = { ...this.labels };
        const existingWallet = Object.keys(nextLabels).find(
            (candidate) =>
                walletLookupKey(candidate) === walletLookupKey(trimmedWallet),
        );

        if (existingWallet && existingWallet !== trimmedWallet) {
            delete nextLabels[existingWallet];
        }

        const trimmedLabel = label.trim().slice(0, 48);
        if (trimmedLabel) {
            nextLabels[trimmedWallet] = trimmedLabel;
        } else {
            delete nextLabels[existingWallet ?? trimmedWallet];
        }

        this.replace(nextLabels);
    }

    removeLabel(wallet: string): void {
        this.setLabel(wallet, "");
    }
}

export const developerLabelsStore = new DeveloperLabelsStore();
