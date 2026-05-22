import {
    cloneDefaultSettings,
    normalizeSettingsSections,
    parseSettingsImport,
    readStoredSettings,
    writeStoredSettings,
    createSettingsExportPayload,
} from "$lib/config/settings.js";

class SettingsStore {
    sections = $state(cloneDefaultSettings());
    isLoaded = $state(false);

    init() {
        if (this.isLoaded) return;

        const storedSettings = readStoredSettings();
        if (storedSettings) {
            this.sections = storedSettings;
        }

        this.isLoaded = true;
    }

    getSection(sectionName) {
        return this.sections[sectionName] ?? null;
    }

    setSection(sectionName, nextSection) {
        this.sections = {
            ...this.sections,
            [sectionName]: {
                ...(this.sections[sectionName] ?? {}),
                ...(nextSection ?? {}),
            },
        };

        this.persist();
    }

    replaceSections(nextSections) {
        this.sections = normalizeSettingsSections(nextSections);
        this.persist();
    }

    reset() {
        this.sections = cloneDefaultSettings();
        this.persist();
    }

    exportToJson() {
        return JSON.stringify(createSettingsExportPayload(this.sections), null, 2);
    }

    importFromJson(rawJson) {
        const parsedSettings = parseSettingsImport(rawJson);
        this.sections = parsedSettings;
        this.persist();
        return parsedSettings;
    }

    persist() {
        writeStoredSettings(this.sections);
    }
}

export const settingsStore = new SettingsStore();