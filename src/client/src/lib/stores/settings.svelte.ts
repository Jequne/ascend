import {
    cloneDefaultSettings,
    createSettingsExportPayload,
    normalizeSettingsSections,
    parseSettingsImport,
    readStoredSettings,
    writeStoredSettings,
} from "$lib/config/settings";
import type { SettingsSections } from "$lib/types";

class SettingsStore {
    sections = $state<SettingsSections>(cloneDefaultSettings());
    isLoaded = $state(false);

    init(): void {
        if (this.isLoaded) return;

        const storedSettings = readStoredSettings();
        if (storedSettings) this.sections = storedSettings;
        this.isLoaded = true;
    }

    getSection<K extends keyof SettingsSections>(
        sectionName: K,
    ): SettingsSections[K] | null {
        return this.sections[sectionName] ?? null;
    }

    setSection<K extends keyof SettingsSections>(
        sectionName: K,
        nextSection: Partial<SettingsSections[K]>,
    ): void {
        this.sections = {
            ...this.sections,
            [sectionName]: {
                ...this.sections[sectionName],
                ...nextSection,
            },
        };
        this.persist();
    }

    replaceSections(nextSections: unknown): void {
        this.sections = normalizeSettingsSections(nextSections);
        this.persist();
    }

    reset(): void {
        this.sections = cloneDefaultSettings();
        this.persist();
    }

    exportToJson(): string {
        return JSON.stringify(
            createSettingsExportPayload(this.sections),
            null,
            2,
        );
    }

    importFromJson(rawJson: string): SettingsSections {
        const parsedSettings = parseSettingsImport(rawJson);
        this.sections = parsedSettings;
        this.persist();
        return parsedSettings;
    }

    persist(): void {
        writeStoredSettings(this.sections);
    }
}

export const settingsStore = new SettingsStore();
