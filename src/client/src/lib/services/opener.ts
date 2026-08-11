import { openUrl } from "@tauri-apps/plugin-opener";

export interface UrlOpener {
    open(url: string): Promise<void>;
}

class TauriUrlOpener implements UrlOpener {
    open(url: string): Promise<void> {
        return openUrl(url);
    }
}

export const openerService: UrlOpener = new TauriUrlOpener();

export function openExternalUrl(url: string): void {
    void openerService.open(url).catch((error: unknown) => {
        console.error("Failed to open URL:", error);
    });
}
