<script lang="ts">
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import {
        AlertTriangle,
        Ban,
        ChevronDown,
        ListFilter,
        Plus,
        Trash2,
    } from "@lucide/svelte";
    import { tick } from "svelte";

    export let value: string;

    let entriesExpanded = false;
    let pendingValue = "";
    let clearDialog: HTMLDialogElement;
    let keepValuesButton: HTMLButtonElement;

    $: entries = normalizeBlacklistEntries(value);
    $: pendingEntries = normalizeBlacklistEntries(pendingValue);
    $: if (entries.length === 0) entriesExpanded = false;

    function addEntries(event: SubmitEvent): void {
        event.preventDefault();
        if (pendingEntries.length === 0) return;

        value = normalizeBlacklistEntries([...entries, ...pendingEntries]).join(
            "\n",
        );
        pendingValue = "";
    }

    function requestClear(): void {
        clearDialog.showModal();
        void tick().then(() => keepValuesButton.focus());
    }

    function closeClearDialog(): void {
        clearDialog.close();
    }

    function clearEntries(): void {
        value = "";
        pendingValue = "";
        closeClearDialog();
    }
</script>

<div class="flex flex-col gap-3 p-3">
    <section
        class="overflow-hidden rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))] shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]"
    >
        <div
            class="flex items-start justify-between gap-3 border-b border-white/[0.06] p-3"
        >
            <div class="flex min-w-0 items-start gap-2.5">
                <span
                    class="text-accent-purple bg-accent-purple/10 flex size-8 shrink-0 items-center justify-center rounded-lg border border-indigo-400/15"
                >
                    <ListFilter size={17} aria-hidden="true" />
                </span>
                <div>
                    <h3
                        class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                    >
                        Hidden values
                    </h3>
                    <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                        Match developer wallets, token names, tickers, or admin
                        nicknames.
                    </p>
                </div>
            </div>
            <span
                class="border-accent-purple/25 bg-accent-purple/10 shrink-0 rounded-full border px-2 py-1 text-[0.64rem] font-bold text-purple-300"
                aria-label={`${entries.length} unique blacklist entries`}
            >
                {entries.length} unique
            </span>
        </div>

        <form class="p-3" onsubmit={addEntries}>
            <label
                class="mb-1.5 block text-xs font-semibold text-slate-200"
                for="blacklist-values"
            >
                Add hidden values
            </label>
            <textarea
                id="blacklist-values"
                name="blacklistValues"
                class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 min-h-24 w-full resize-y rounded-[10px] border border-white/10 bg-[#10131c] p-2.5 text-xs leading-relaxed outline-none placeholder:text-slate-600 focus:ring-2"
                rows="4"
                bind:value={pendingValue}
                placeholder="Paste values here, one per line"
                spellcheck="false"></textarea>

            <div class="mt-2 flex items-center justify-between gap-3">
                <p class="text-muted m-0 text-[0.6rem] leading-snug">
                    Paste as many values as needed. Duplicates and empty lines
                    are ignored.
                </p>
                <button
                    class="border-accent-blue/30 bg-accent-blue/12 inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-[0.68rem] font-semibold text-blue-200 transition-colors hover:border-blue-400/50 hover:bg-blue-500/20 focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                    type="submit"
                    disabled={pendingEntries.length === 0}
                >
                    <Plus size={13} aria-hidden="true" />
                    Add
                </button>
            </div>
        </form>
    </section>

    {#if entries.length === 0}
        <div
            class="text-muted flex min-h-24 flex-col items-center justify-center rounded-xl border border-dashed border-white/10 bg-black/10 px-4 text-center"
            role="status"
        >
            <Ban size={20} strokeWidth={1.6} aria-hidden="true" />
            <p class="mt-2 mb-0 text-xs font-semibold">Blacklist is empty</p>
            <p class="mt-1 mb-0 text-[0.64rem]">
                Incoming tokens are not hidden by wallet or name.
            </p>
        </div>
    {:else}
        <section
            class="overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.02]"
        >
            <div class="flex items-stretch">
                <button
                    class="focus-visible:ring-accent-purple flex min-h-11 min-w-0 grow items-center justify-between gap-3 px-3 text-left transition-colors hover:bg-white/[0.035] focus-visible:ring-2 focus-visible:outline-none"
                    type="button"
                    aria-expanded={entriesExpanded}
                    aria-controls="blacklist-entries-preview"
                    onclick={() => (entriesExpanded = !entriesExpanded)}
                >
                    <span class="min-w-0">
                        <span
                            class="block truncate text-xs font-semibold text-slate-200"
                        >
                            {entriesExpanded ? "Hide" : "Show"}
                            {entries.length}
                            blacklist {entries.length === 1
                                ? "entry"
                                : "entries"}
                        </span>
                        <span class="text-muted mt-0.5 block text-[0.6rem]">
                            Review the normalized values that will be saved.
                        </span>
                    </span>
                    <ChevronDown
                        class="text-muted shrink-0 transition-transform duration-150 motion-reduce:transition-none {entriesExpanded
                            ? 'rotate-180'
                            : ''}"
                        size={16}
                        aria-hidden="true"
                    />
                </button>
                <button
                    class="inline-flex w-11 shrink-0 items-center justify-center border-l border-white/[0.06] text-red-300 transition-colors hover:bg-red-500/10 hover:text-red-200 focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none"
                    type="button"
                    title="Clear blacklist"
                    aria-label="Clear blacklist"
                    onclick={requestClear}
                >
                    <Trash2 size={14} aria-hidden="true" />
                </button>
            </div>

            {#if entriesExpanded}
                <ul
                    class="m-0 grid list-none gap-1.5 border-t border-white/[0.06] p-2.5"
                    id="blacklist-entries-preview"
                    aria-label="Normalized blacklist preview"
                >
                    {#each entries as entry, index (entry.toLowerCase())}
                        <li
                            class="flex min-w-0 items-center gap-2 rounded-lg border border-white/[0.06] bg-black/15 px-2.5 py-2 text-xs text-slate-200"
                        >
                            <span
                                class="flex size-5 shrink-0 items-center justify-center rounded bg-white/[0.06] text-[0.6rem] font-bold text-slate-500"
                                aria-hidden="true"
                            >
                                {index + 1}
                            </span>
                            <span class="truncate" title={entry}>{entry}</span>
                        </li>
                    {/each}
                </ul>
            {/if}
        </section>
    {/if}
</div>

<dialog
    class="text-foreground m-auto w-[min(360px,calc(100vw-32px))] max-w-none rounded-xl border border-red-400/20 bg-[#151822] p-0 shadow-[0_24px_70px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.04)] backdrop:bg-black/65 backdrop:backdrop-blur-[4px]"
    aria-labelledby="clear-blacklist-title"
    bind:this={clearDialog}
    oncancel={(event) => {
        event.preventDefault();
        closeClearDialog();
    }}
>
    <div class="p-4">
        <div class="flex items-start gap-3">
            <span
                class="flex size-9 shrink-0 items-center justify-center rounded-[10px] border border-red-400/20 bg-red-500/10 text-red-300"
            >
                <AlertTriangle size={18} aria-hidden="true" />
            </span>
            <div>
                <h4 id="clear-blacklist-title" class="m-0 text-sm font-bold">
                    Clear the entire blacklist?
                </h4>
                <p class="text-muted mt-1.5 mb-0 text-xs leading-relaxed">
                    This removes every hidden value. After you save, the list
                    cannot be restored unless you exported your settings first.
                </p>
            </div>
        </div>
        <div class="mt-4 flex justify-end gap-2">
            <button
                class="inline-flex h-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] px-3 text-xs font-semibold text-slate-300 transition-colors hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:outline-none"
                type="button"
                bind:this={keepValuesButton}
                onclick={closeClearDialog}
            >
                Keep values
            </button>
            <button
                class="inline-flex h-9 items-center justify-center rounded-lg border border-red-400/30 bg-red-500/15 px-3 text-xs font-semibold text-red-200 transition-colors hover:border-red-400/45 hover:bg-red-500/22 focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none"
                type="button"
                onclick={clearEntries}
            >
                Clear permanently
            </button>
        </div>
    </div>
</dialog>
