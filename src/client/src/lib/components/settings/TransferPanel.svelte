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

<div class="grid gap-3 p-3 sm:grid-cols-2">
    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)]"
    >
        <div class="mb-3 flex items-start gap-2">
            <FileJson
                class="text-accent-purple mt-0.5 shrink-0"
                size={18}
                aria-hidden="true"
            />
            <div>
                <h3
                    class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
                >
                    Export settings
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Copy the current draft or download a JSON file.
                </p>
            </div>
        </div>

        <div class="flex flex-col gap-2">
            <button
                class="border-accent-blue/30 bg-accent-blue/15 hover:border-accent-blue/50 hover:bg-accent-blue/20 focus-visible:ring-accent-blue inline-flex h-9 items-center justify-center gap-2 rounded-lg border px-3 text-xs font-semibold text-blue-200 transition-colors focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                onclick={copySettings}
            >
                <Copy size={14} aria-hidden="true" />
                Copy JSON
            </button>
            <button
                class="focus-visible:ring-accent-purple inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 text-xs font-semibold text-slate-200 transition-colors hover:border-white/20 hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                onclick={downloadSettings}
            >
                <Download size={14} aria-hidden="true" />
                Download JSON
            </button>
        </div>
    </section>

    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)]"
    >
        <div class="mb-3 flex items-start gap-2">
            <Upload
                class="text-accent-purple mt-0.5 shrink-0"
                size={18}
                aria-hidden="true"
            />
            <div>
                <h3
                    class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
                >
                    Import file
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Validate and load a JSON file into this draft.
                </p>
            </div>
        </div>

        <label
            class="hover:border-accent-purple/40 hover:bg-accent-purple/[0.06] focus-within:ring-accent-purple flex h-9 cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-white/15 bg-black/15 px-3 text-xs font-semibold text-slate-200 transition-colors focus-within:ring-2"
        >
            <Upload size={14} aria-hidden="true" />
            Choose .json file
            <input
                class="sr-only"
                type="file"
                accept="application/json,.json"
                onchange={importFile}
            />
        </label>
        <p class="text-muted mt-2 mb-0 text-[0.6rem]">
            Maximum size: {SETTINGS_IMPORT_MAX_BYTES / 1_000_000} MB.
        </p>
    </section>

    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)] sm:col-span-2"
    >
        <label
            class="mb-1.5 block text-xs font-semibold text-slate-200"
            for="settings-import-json"
        >
            Paste settings JSON
        </label>
        <textarea
            id="settings-import-json"
            class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 min-h-28 w-full resize-y rounded-lg border border-white/10 bg-black/20 p-2.5 font-mono text-[0.68rem] leading-relaxed outline-none placeholder:text-slate-600 focus:ring-2"
            rows="5"
            bind:value={importText}
            spellcheck="false"
            placeholder="Paste exported JSON here"></textarea>
        <div class="mt-2 flex justify-end">
            <button
                class="border-accent-blue/30 bg-accent-blue/15 hover:border-accent-blue/50 hover:bg-accent-blue/20 focus-visible:ring-accent-blue inline-flex h-9 items-center justify-center gap-2 rounded-lg border px-3 text-xs font-semibold text-blue-200 transition-colors focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                type="button"
                disabled={!importText.trim()}
                onclick={importPastedSettings}
            >
                <Upload size={14} aria-hidden="true" />
                Import pasted JSON
            </button>
        </div>
    </section>

    {#if message}
        <p
            class="border-success/25 bg-success/10 m-0 rounded-lg border px-3 py-2 text-xs text-emerald-300 sm:col-span-2"
            role="status"
        >
            {message}
        </p>
    {/if}
    {#if error}
        <p
            class="m-0 rounded-lg border border-red-500/25 bg-red-500/10 px-3 py-2 text-xs text-red-300 sm:col-span-2"
            role="alert"
        >
            {error}
        </p>
    {/if}
</div>
