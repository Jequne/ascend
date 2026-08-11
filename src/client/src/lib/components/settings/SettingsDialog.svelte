<script lang="ts">
    import AutoOpenControl from "$lib/components/settings/AutoOpenControl.svelte";
    import BlacklistPanel from "$lib/components/settings/BlacklistPanel.svelte";
    import FiltersPanel from "$lib/components/settings/FiltersPanel.svelte";
    import SettingsTabs from "$lib/components/settings/SettingsTabs.svelte";
    import TransferPanel from "$lib/components/settings/TransferPanel.svelte";
    import { DEFAULT_FILTERS } from "$lib/config/constants";
    import { normalizeFilters } from "$lib/config/settings";
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { FilterSettings, SettingsTab } from "$lib/types";
    import {
        blacklistEntriesToText,
        normalizeBlacklistEntries,
    } from "$lib/utils/blacklist";
    import { X } from "@lucide/svelte";
    import { tick } from "svelte";

    export let open: boolean;
    export let trigger: HTMLButtonElement | null = null;

    let dialog: HTMLDialogElement;
    let wasOpen = false;
    let activeTab: SettingsTab = "filters";
    let draft: FilterSettings = normalizeFilters(DEFAULT_FILTERS);
    let blacklistText = "";

    const tabIndexes: Record<SettingsTab, number> = {
        filters: 0,
        blacklist: 1,
        transfer: 2,
    };

    $: if (dialog && open && !wasOpen) {
        draft = normalizeFilters(filtersStore.filters);
        blacklistText = blacklistEntriesToText(draft.blacklist);
        activeTab = "filters";
        wasOpen = true;
        dialog.showModal();
        void tick().then(() => {
            dialog.querySelector<HTMLButtonElement>('[role="switch"]')?.focus();
        });
    }

    $: if (dialog && !open && wasOpen) {
        closeDialog();
    }

    function restoreFocus(): void {
        void tick().then(() => trigger?.focus());
    }

    function closeDialog(): void {
        if (dialog.open) dialog.close();
        open = false;
        wasOpen = false;
        restoreFocus();
    }

    function cancel(): void {
        closeDialog();
    }

    function save(): void {
        filtersStore.updateFilters({
            ...draft,
            blacklist: normalizeBlacklistEntries(blacklistText),
        });
        closeDialog();
    }

    function handleCancel(event: Event): void {
        event.preventDefault();
        cancel();
    }

    function handleBackdropClick(event: MouseEvent): void {
        if (event.target === event.currentTarget) cancel();
    }

    function handleNativeClose(): void {
        open = false;
        wasOpen = false;
        restoreFocus();
    }
</script>

<dialog
    class="text-foreground m-auto h-[min(680px,calc(100dvh-20px))] max-h-none w-[min(620px,calc(100vw-20px))] max-w-none overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0d1018] p-0 shadow-[0_24px_80px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.04)] backdrop:bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.18),transparent_42%),rgba(4,7,14,0.76)] backdrop:backdrop-blur-[10px]"
    aria-labelledby="settings-title"
    bind:this={dialog}
    oncancel={handleCancel}
    onclose={handleNativeClose}
    onclick={handleBackdropClick}
>
    <div
        class="grid size-full grid-rows-[auto_auto_auto_minmax(0,1fr)_auto] bg-[linear-gradient(180deg,rgba(18,22,34,0.98),rgba(13,16,26,0.98))]"
    >
        <header
            class="flex items-start justify-between gap-3 border-b border-white/[0.06] bg-linear-to-b from-white/[0.03] to-transparent px-3.5 py-3"
        >
            <div>
                <h2 id="settings-title" class="m-0 text-base font-bold">
                    Settings
                </h2>
                <p class="text-muted mt-1 mb-0 text-[0.68rem] leading-snug">
                    Changes stay local to this dialog until Save.
                </p>
            </div>
            <button
                class="text-muted hover:text-foreground focus-visible:ring-accent-purple inline-flex size-8 shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.035] transition-colors hover:border-white/15 hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                title="Close settings"
                aria-label="Close settings"
                onclick={cancel}
            >
                <X size={16} aria-hidden="true" />
            </button>
        </header>

        <AutoOpenControl
            bind:checked={draft.autoOpenInNewTab}
            bind:terminal={draft.terminal}
        />

        <SettingsTabs {activeTab} onSelect={(tab) => (activeTab = tab)} />

        <div class="min-h-0 overflow-hidden">
            <div
                class="settings-track flex h-full w-[300%]"
                style:transform={`translateX(-${tabIndexes[activeTab] * (100 / 3)}%)`}
            >
                <div
                    class="settings-panel h-full w-1/3 shrink-0 overflow-y-auto overscroll-contain"
                    role="tabpanel"
                    id="settings-panel-filters"
                    aria-labelledby="settings-tab-filters"
                    aria-hidden={activeTab !== "filters"}
                    inert={activeTab !== "filters"}
                    tabindex={activeTab === "filters" ? 0 : -1}
                >
                    <FiltersPanel bind:settings={draft} />
                </div>

                <div
                    class="settings-panel h-full w-1/3 shrink-0 overflow-y-auto overscroll-contain"
                    role="tabpanel"
                    id="settings-panel-blacklist"
                    aria-labelledby="settings-tab-blacklist"
                    aria-hidden={activeTab !== "blacklist"}
                    inert={activeTab !== "blacklist"}
                    tabindex={activeTab === "blacklist" ? 0 : -1}
                >
                    <BlacklistPanel bind:value={blacklistText} />
                </div>

                <div
                    class="settings-panel h-full w-1/3 shrink-0 overflow-y-auto overscroll-contain"
                    role="tabpanel"
                    id="settings-panel-transfer"
                    aria-labelledby="settings-tab-transfer"
                    aria-hidden={activeTab !== "transfer"}
                    inert={activeTab !== "transfer"}
                    tabindex={activeTab === "transfer" ? 0 : -1}
                >
                    <TransferPanel bind:settings={draft} bind:blacklistText />
                </div>
            </div>
        </div>

        <footer
            class="flex shrink-0 justify-end gap-2 border-t border-white/[0.06] bg-linear-to-b from-transparent to-white/[0.025] px-3.5 py-3"
        >
            <button
                class="focus-visible:ring-accent-purple inline-flex h-9 min-w-20 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 text-xs font-semibold text-slate-300 transition-colors hover:border-white/15 hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                onclick={cancel}
            >
                Cancel
            </button>
            <button
                class="border-accent-blue/30 focus-visible:ring-offset-canvas inline-flex h-9 min-w-24 items-center justify-center rounded-lg border bg-linear-to-br from-[#2f7cf6] to-[#2563eb] px-3 text-xs font-semibold text-white transition-[filter,box-shadow] hover:brightness-110 focus-visible:ring-2 focus-visible:ring-blue-300 focus-visible:ring-offset-1 focus-visible:outline-none"
                type="button"
                onclick={save}
            >
                Save
            </button>
        </footer>
    </div>
</dialog>

<style>
    .settings-track {
        transition: transform 200ms ease;
    }

    .settings-panel::-webkit-scrollbar {
        width: 9px;
    }

    .settings-panel::-webkit-scrollbar-track {
        background: transparent;
    }

    .settings-panel::-webkit-scrollbar-thumb {
        border: 2px solid transparent;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.28);
        background-clip: padding-box;
    }

    @media (prefers-reduced-motion: reduce) {
        .settings-track {
            transition: none;
        }
    }
</style>
