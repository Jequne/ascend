<script lang="ts">
    import { normalizeDeveloperLabels } from "$lib/config/settings";
    import type { DeveloperLabels } from "$lib/types";
    import { Plus, Search, Tag, Trash2, WalletCards } from "@lucide/svelte";

    export let value: DeveloperLabels;

    let wallet = "";
    let label = "";
    let searchQuery = "";

    $: entries = Object.entries(normalizeDeveloperLabels(value));
    $: normalizedQuery = searchQuery.trim().toLowerCase();
    $: visibleEntries = normalizedQuery
        ? entries.filter(([entryWallet, entryLabel]) =>
              `${entryWallet} ${entryLabel}`
                  .toLowerCase()
                  .includes(normalizedQuery),
          )
        : entries;
    $: canSubmit = Boolean(wallet.trim() && label.trim());

    function addLabel(event: SubmitEvent): void {
        event.preventDefault();
        if (!canSubmit) return;

        value = normalizeDeveloperLabels({
            ...value,
            [wallet.trim()]: label,
        });
        wallet = "";
        label = "";
    }

    function removeLabel(entryWallet: string): void {
        const nextValue = { ...value };
        delete nextValue[entryWallet];
        value = normalizeDeveloperLabels(nextValue);
    }
</script>

<div class="flex flex-col gap-3 p-3">
    <section
        class={[
            "overflow-hidden rounded-xl border border-white/[0.075]",
            "bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))]",
            "shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]",
        ]}
    >
        <div class="flex items-start gap-2.5 border-b border-white/[0.06] p-3">
            <span
                class={[
                    "text-accent-purple bg-accent-purple/10 flex size-8",
                    "shrink-0 items-center justify-center rounded-lg border",
                    "border-indigo-400/15",
                ]}
            >
                <Tag size={17} aria-hidden="true" />
            </span>
            <div>
                <h3
                    class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                >
                    Developer labels
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Give a developer wallet a memorable name. Labels remain on
                    this device and appear on every matching token card.
                </p>
            </div>
        </div>

        <form class="grid gap-2 p-3" onsubmit={addLabel}>
            <div
                class="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,0.7fr)]"
            >
                <label
                    class="grid gap-1.5 text-xs font-semibold text-slate-200"
                >
                    Developer wallet
                    <input
                        class={[
                            "text-foreground h-10 min-w-0 rounded-[10px] border",
                            "border-white/10 bg-[#10131c] px-2.5 text-xs outline-none",
                            "placeholder:text-slate-600 focus:border-indigo-400/50",
                            "focus:ring-2 focus:ring-indigo-400/15",
                        ]}
                        name="developerWallet"
                        bind:value={wallet}
                        placeholder="Paste wallet address"
                        autocomplete="off"
                        spellcheck="false"
                    />
                </label>
                <label
                    class="grid gap-1.5 text-xs font-semibold text-slate-200"
                >
                    Label
                    <input
                        class={[
                            "text-foreground h-10 min-w-0 rounded-[10px] border",
                            "border-white/10 bg-[#10131c] px-2.5 text-xs outline-none",
                            "placeholder:text-slate-600 focus:border-indigo-400/50",
                            "focus:ring-2 focus:ring-indigo-400/15",
                        ]}
                        name="developerLabel"
                        bind:value={label}
                        maxlength="48"
                        placeholder="e.g. Strong dev"
                        autocomplete="off"
                    />
                </label>
            </div>
            <div class="flex items-center justify-between gap-3">
                <p class="text-muted m-0 text-[0.6rem] leading-snug">
                    Adding the same wallet again updates its label.
                </p>
                <button
                    class={[
                        "border-accent-blue/30 bg-accent-blue/12 inline-flex h-8",
                        "shrink-0 items-center gap-1.5 rounded-lg border px-2.5",
                        "text-[0.68rem] font-semibold text-blue-200 transition-colors",
                        "hover:border-blue-400/50 hover:bg-blue-500/20",
                        "focus-visible:ring-2 focus-visible:ring-blue-400",
                        "focus-visible:outline-none disabled:cursor-not-allowed",
                        "disabled:opacity-40",
                    ]}
                    type="submit"
                    disabled={!canSubmit}
                >
                    <Plus size={13} aria-hidden="true" />
                    Add label
                </button>
            </div>
        </form>
    </section>

    {#if entries.length === 0}
        <div
            class={[
                "text-muted flex min-h-24 flex-col items-center justify-center",
                "rounded-xl border border-dashed border-white/10 bg-black/10",
                "px-4 text-center",
            ]}
            role="status"
        >
            <WalletCards size={20} strokeWidth={1.6} aria-hidden="true" />
            <p class="mt-2 mb-0 text-xs font-semibold">No labels yet</p>
            <p class="mt-1 mb-0 text-[0.64rem]">
                Add one here or click “Add dev label” on a token card.
            </p>
        </div>
    {:else}
        <section
            class="overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.02]"
        >
            <div class="border-b border-white/[0.06] p-2.5">
                <label class="relative block">
                    <span class="sr-only">Search developer labels</span>
                    <Search
                        class="text-muted pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2"
                        size={14}
                        aria-hidden="true"
                    />
                    <input
                        class={[
                            "text-foreground h-9 w-full rounded-lg border border-white/10",
                            "bg-black/15 pr-2.5 pl-8 text-xs outline-none",
                            "placeholder:text-slate-600 focus:border-indigo-400/45",
                            "focus:ring-2 focus:ring-indigo-400/15",
                        ]}
                        type="search"
                        bind:value={searchQuery}
                        placeholder="Search by wallet or label"
                        autocomplete="off"
                    />
                </label>
            </div>

            {#if visibleEntries.length > 0}
                <ul
                    class="m-0 grid max-h-56 list-none gap-1.5 overflow-y-auto p-2.5"
                    aria-label="Developer labels"
                >
                    {#each visibleEntries as [entryWallet, entryLabel] (entryWallet)}
                        <li
                            class={[
                                "flex min-w-0 items-center gap-2 rounded-lg border",
                                "border-white/[0.06] bg-black/15 px-2.5 py-2",
                            ]}
                        >
                            <span
                                class={[
                                    "flex size-6 shrink-0 items-center justify-center",
                                    "rounded-md bg-indigo-400/10 text-indigo-300",
                                ]}
                            >
                                <Tag size={12} aria-hidden="true" />
                            </span>
                            <span class="min-w-0 grow">
                                <span
                                    class="block truncate text-xs font-semibold text-slate-200"
                                    title={entryLabel}>{entryLabel}</span
                                >
                                <span
                                    class="text-muted mt-0.5 block truncate font-mono text-[0.58rem]"
                                    title={entryWallet}>{entryWallet}</span
                                >
                            </span>
                            <button
                                class={[
                                    "inline-flex size-8 shrink-0 items-center justify-center",
                                    "rounded-lg text-slate-500 transition-colors",
                                    "hover:bg-red-500/10 hover:text-red-300",
                                    "focus-visible:ring-2 focus-visible:ring-red-400",
                                    "focus-visible:outline-none",
                                ]}
                                type="button"
                                title="Remove label"
                                aria-label={`Remove label for ${entryWallet}`}
                                onclick={() => removeLabel(entryWallet)}
                            >
                                <Trash2 size={13} aria-hidden="true" />
                            </button>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p
                    class="text-muted m-0 px-3 py-5 text-center text-xs"
                    role="status"
                >
                    No labels match “{searchQuery.trim()}”.
                </p>
            {/if}
        </section>
    {/if}
</div>
