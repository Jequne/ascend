<script lang="ts">
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import { Ban, Trash2 } from "@lucide/svelte";

    export let value: string;

    $: entries = normalizeBlacklistEntries(value);
</script>

<div class="flex flex-col gap-3 p-3">
    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)]"
    >
        <div class="mb-2.5 flex items-start justify-between gap-3">
            <div>
                <h3
                    class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
                >
                    Hidden values
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Dev wallet, token name, ticker, or admin nickname. One entry
                    per line or comma.
                </p>
            </div>
            <span
                class="border-accent-purple/25 bg-accent-purple/10 shrink-0 rounded-full border px-2 py-1 text-[0.64rem] font-bold text-purple-300"
                aria-label={`${entries.length} unique blacklist entries`}
            >
                {entries.length} unique
            </span>
        </div>

        <label class="sr-only" for="blacklist-values">Blacklist values</label>
        <textarea
            id="blacklist-values"
            class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 min-h-36 w-full resize-y rounded-lg border border-white/10 bg-black/20 p-2.5 text-xs leading-relaxed outline-none placeholder:text-slate-600 focus:ring-2"
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
        <ul
            class="m-0 grid list-none gap-1.5 p-0"
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
</div>
