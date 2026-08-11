<script lang="ts">
    import {
        SETTINGS_EXPORT_FILENAME,
        SETTINGS_IMPORT_MAX_BYTES,
        createSettingsExportPayload,
        parseSettingsImport,
    } from "$lib/config/settings";
    import type { FilterSettings } from "$lib/types";
    import {
        blacklistEntriesToText,
        normalizeBlacklistEntries,
    } from "$lib/utils/blacklist";
    import { Copy, Download, FileJson, Upload } from "@lucide/svelte";

    export let settings: FilterSettings;
    export let blacklistText: string;

    let importText = "";
    let message = "";
    let error = "";

    $: exportedJson = JSON.stringify(
        createSettingsExportPayload({
            filters: {
                ...settings,
                blacklist: normalizeBlacklistEntries(blacklistText),
            },
        }),
        null,
        2,
    );

    function showSuccess(value: string): void {
        message = value;
        error = "";
    }

    function showError(value: unknown): void {
        error = value instanceof Error ? value.message : String(value);
        message = "";
    }

    function applyImport(rawJson: string): void {
        if (
            new TextEncoder().encode(rawJson).byteLength >
            SETTINGS_IMPORT_MAX_BYTES
        ) {
            throw new Error("Settings JSON is too large.");
        }

        const imported = parseSettingsImport(rawJson);
        settings = imported.filters;
        blacklistText = blacklistEntriesToText(imported.filters.blacklist);
        showSuccess(
            "Settings loaded into the draft. Press Save to apply them.",
        );
    }

    async function copySettings(): Promise<void> {
        try {
            if (!navigator.clipboard?.writeText) {
                throw new Error("Clipboard access is unavailable.");
            }

            await navigator.clipboard.writeText(exportedJson);
            showSuccess("Settings copied to clipboard.");
        } catch (caught: unknown) {
            showError(caught);
        }
    }

    function downloadSettings(): void {
        const blob = new Blob([exportedJson], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = SETTINGS_EXPORT_FILENAME;
        anchor.click();
        URL.revokeObjectURL(url);
        showSuccess(`Downloaded ${SETTINGS_EXPORT_FILENAME}.`);
    }

    function importPastedSettings(): void {
        try {
            applyImport(importText);
        } catch (caught: unknown) {
            showError(caught);
        }
    }

    async function importFile(event: Event): Promise<void> {
        const input = event.currentTarget as HTMLInputElement;
        const file = input.files?.[0];
        input.value = "";

        if (!file) return;

        try {
            if (!file.name.toLowerCase().endsWith(".json")) {
                throw new Error("Choose a .json settings file.");
            }
            if (file.size > SETTINGS_IMPORT_MAX_BYTES) {
                throw new Error("Settings file is too large.");
            }

            applyImport(await file.text());
        } catch (caught: unknown) {
            showError(caught);
        }
    }
</script>

<div class="flex flex-col gap-3 p-3">
    <section
        class="overflow-hidden rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))] shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]"
        aria-labelledby="export-settings-heading"
    >
        <div class="flex items-start gap-2.5 border-b border-white/[0.06] p-3">
            <span
                class="text-accent-purple bg-accent-purple/10 flex size-8 shrink-0 items-center justify-center rounded-lg border border-indigo-400/15"
            >
                <FileJson size={17} aria-hidden="true" />
            </span>
            <div>
                <h3
                    id="export-settings-heading"
                    class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                >
                    Export settings
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Create a portable copy of the entire current draft.
                </p>
            </div>
        </div>

        <div class="grid gap-2 p-3 sm:grid-cols-2">
            <button
                class="border-accent-blue/30 bg-accent-blue/15 hover:border-accent-blue/50 hover:bg-accent-blue/20 focus-visible:ring-accent-blue inline-flex h-10 items-center justify-center gap-2 rounded-[10px] border px-3 text-xs font-semibold text-blue-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] transition-colors focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                onclick={copySettings}
            >
                <Copy size={14} aria-hidden="true" />
                Copy JSON
            </button>
            <button
                class="focus-visible:ring-accent-purple inline-flex h-10 items-center justify-center gap-2 rounded-[10px] border border-white/10 bg-white/[0.035] px-3 text-xs font-semibold text-slate-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)] transition-colors hover:border-white/20 hover:bg-white/[0.065] focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                onclick={downloadSettings}
            >
                <Download size={14} aria-hidden="true" />
                Download JSON
            </button>
        </div>
    </section>

    <div class="flex items-center gap-3 px-1" aria-hidden="true">
        <span class="h-px grow bg-white/[0.06]"></span>
        <span
            class="text-[0.57rem] font-bold tracking-[0.08em] text-slate-600 uppercase"
            >Restore a configuration</span
        >
        <span class="h-px grow bg-white/[0.06]"></span>
    </div>

    <section
        class="overflow-hidden rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))] shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]"
        aria-labelledby="import-settings-heading"
    >
        <div class="flex items-start gap-2.5 border-b border-white/[0.06] p-3">
            <span
                class="text-accent-blue bg-accent-blue/10 flex size-8 shrink-0 items-center justify-center rounded-lg border border-blue-400/15"
            >
                <Upload size={17} aria-hidden="true" />
            </span>
            <div>
                <h3
                    id="import-settings-heading"
                    class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                >
                    Import settings
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Validate a JSON file or pasted configuration before adding
                    it to this draft.
                </p>
            </div>
        </div>

        <div class="flex flex-col gap-3 p-3">
            <div class="grid items-center gap-2 sm:grid-cols-[1fr_auto]">
                <label
                    class="hover:border-accent-purple/40 hover:bg-accent-purple/[0.06] focus-within:ring-accent-purple flex h-10 cursor-pointer items-center justify-center gap-2 rounded-[10px] border border-dashed border-white/15 bg-black/15 px-3 text-xs font-semibold text-slate-200 transition-colors focus-within:ring-2"
                >
                    <Upload size={14} aria-hidden="true" />
                    Choose .json file
                    <input
                        class="sr-only"
                        id="settings-import-file"
                        name="settingsImportFile"
                        type="file"
                        accept="application/json,.json"
                        onchange={importFile}
                    />
                </label>
                <p class="text-muted m-0 text-[0.6rem] whitespace-nowrap">
                    Up to {SETTINGS_IMPORT_MAX_BYTES / 1_000_000} MB
                </p>
            </div>

            <div class="flex items-center gap-2" aria-hidden="true">
                <span class="h-px grow bg-white/[0.06]"></span>
                <span class="text-[0.58rem] text-slate-600">or paste JSON</span>
                <span class="h-px grow bg-white/[0.06]"></span>
            </div>

            <label
                class="text-xs font-semibold text-slate-200"
                for="settings-import-json"
            >
                Settings JSON
            </label>
            <textarea
                id="settings-import-json"
                name="settingsImportJson"
                class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 min-h-28 w-full resize-y rounded-[10px] border border-white/10 bg-[#10131c] p-2.5 font-mono text-[0.68rem] leading-relaxed outline-none placeholder:text-slate-600 focus:ring-2"
                rows="5"
                bind:value={importText}
                spellcheck="false"
                placeholder="Paste exported JSON here"></textarea>
            <div class="flex justify-end">
                <button
                    class="border-accent-blue/30 bg-accent-blue/15 hover:border-accent-blue/50 hover:bg-accent-blue/20 focus-visible:ring-accent-blue inline-flex h-9 items-center justify-center gap-2 rounded-[10px] border px-3 text-xs font-semibold text-blue-100 transition-colors focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                    type="button"
                    disabled={!importText.trim()}
                    onclick={importPastedSettings}
                >
                    <Upload size={14} aria-hidden="true" />
                    Import pasted JSON
                </button>
            </div>
        </div>
    </section>

    {#if message}
        <p
            class="border-success/25 bg-success/10 m-0 rounded-[10px] border px-3 py-2 text-xs text-emerald-300"
            role="status"
        >
            {message}
        </p>
    {/if}
    {#if error}
        <p
            class="m-0 rounded-[10px] border border-red-500/25 bg-red-500/10 px-3 py-2 text-xs text-red-300"
            role="alert"
        >
            {error}
        </p>
    {/if}
</div>
