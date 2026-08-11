<script lang="ts">
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import { Ban, ChevronDown, ListFilter, Trash2 } from "@lucide/svelte";

    export let value: string;

    let entriesExpanded = false;

    $: entries = normalizeBlacklistEntries(value);
    $: if (entries.length === 0) entriesExpanded = false;
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
                        nicknames. Enter one value per line or separate them
                        with commas.
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

        <div class="p-3">
            <label class="sr-only" for="blacklist-values"
                >Blacklist values</label
            >
            <textarea
                id="blacklist-values"
                name="blacklistValues"
                class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 min-h-36 w-full resize-y rounded-[10px] border border-white/10 bg-[#10131c] p-2.5 text-xs leading-relaxed outline-none placeholder:text-slate-600 focus:ring-2"
                rows="7"
                bind:value
                placeholder="wallet-address&#10;token name&#10;ticker"
                spellcheck="false"></textarea>

            <div class="mt-2 flex items-center justify-between gap-3">
                <p class="text-muted m-0 text-[0.6rem] leading-snug">
                    Matching ignores case and surrounding spaces. Duplicates and
                    empty values are removed on Save.
                </p>
                <button
                    class="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-red-500/25 bg-red-500/10 px-2.5 text-[0.68rem] font-semibold text-red-300 transition-colors hover:border-red-500/45 hover:bg-red-500/15 focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                    type="button"
                    disabled={entries.length === 0}
                    onclick={() => (value = "")}
                >
                    <Trash2 size={13} aria-hidden="true" />
                    Clear
                </button>
            </div>
        </div>
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
            <button
                class="focus-visible:ring-accent-purple flex min-h-11 w-full items-center justify-between gap-3 px-3 text-left transition-colors hover:bg-white/[0.035] focus-visible:ring-2 focus-visible:outline-none"
                type="button"
                aria-expanded={entriesExpanded}
                aria-controls="blacklist-entries-preview"
                onclick={() => (entriesExpanded = !entriesExpanded)}
            >
                <span>
                    <span class="block text-xs font-semibold text-slate-200">
                        {entriesExpanded ? "Hide" : "Show"}
                        {entries.length}
                        blacklist {entries.length === 1 ? "entry" : "entries"}
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
                                aria-hidden="true">{index + 1}</span
                            >
                            <span class="truncate" title={entry}>{entry}</span>
                        </li>
                    {/each}
                </ul>
            {/if}
        </section>
    {/if}
</div>
