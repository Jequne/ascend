import { DEFAULT_NOTIFICATIONS } from "$lib/config/constants";
import { normalizeNotifications } from "$lib/config/settings";
import { settingsStore } from "$lib/stores/settings.svelte";
import type { NotificationSettings } from "$lib/types";

class NotificationsStore {
    get settings(): NotificationSettings {
        return (
            settingsStore.getSection("notifications") ?? DEFAULT_NOTIFICATIONS
        );
    }

    get enabled(): boolean {
        return this.settings.enabled;
    }

    get volume(): number {
        return this.settings.volume;
    }

    toggle(): void {
        this.update({ enabled: !this.enabled });
    }

    update(partial: Partial<NotificationSettings>): void {
        settingsStore.replaceSection(
            "notifications",
            normalizeNotifications({ ...this.settings, ...partial }),
        );
    }

    replace(settings: NotificationSettings): void {
        settingsStore.replaceSection(
            "notifications",
            normalizeNotifications(settings),
        );
    }
}

export const notificationsStore = new NotificationsStore();
