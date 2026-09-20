<script lang="ts">
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import {
        AlertTriangle,
        Ban,
        ListFilter,
        Plus,
        Search,
        Trash2,
    } from "@lucide/svelte";
    import { tick } from "svelte";

    export let value: string;

    let pendingValue = "";
    let searchQuery = "";
    let clearDialog: HTMLDialogElement;
    let keepValuesButton: HTMLButtonElement;

    $: entries = normalizeBlacklistEntries(value);
    $: pendingEntries = normalizeBlacklistEntries(pendingValue);
    $: normalizedQuery = searchQuery.trim().toLowerCase();
    $: visibleEntries = entries
        .map((entry, index) => ({ entry, index }))
        .filter(({ entry }) => entry.toLowerCase().includes(normalizedQuery));

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
        searchQuery = "";
        closeClearDialog();
    }

    function removeEntry(entryToRemove: string): void {
        value = entries.filter((entry) => entry !== entryToRemove).join("\n");
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
        <div
            class="flex items-start justify-between gap-3 border-b border-white/[0.06] p-3"
        >
            <div class="flex min-w-0 items-start gap-2.5">
                <span
                    class={[
                        "text-accent-purple bg-accent-purple/10 flex size-8",
                        "shrink-0 items-center justify-center rounded-lg border",
                        "border-indigo-400/15",
                    ]}
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
                        Match fragments anywhere in developer wallets, token
                        names, tickers, or admin nicknames.
                    </p>
                </div>
            </div>
            <span
                class={[
                    "border-accent-purple/25 bg-accent-purple/10 shrink-0",
                    "rounded-full border px-2 py-1 text-[0.64rem]",
                    "font-bold text-purple-300",
                ]}
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
                class={[
                    "text-foreground min-h-24 w-full resize-y rounded-[10px]",
                    "border border-white/10 bg-[#10131c] p-2.5 text-xs",
                    "leading-relaxed outline-none placeholder:text-slate-600",
                    "focus:border-accent-blue/50 focus:ring-accent-blue/15 focus:ring-2",
                ]}
                rows="4"
                bind:value={pendingValue}
                placeholder="Paste values here, one per line"
                spellcheck="false"></textarea>

            <div class="mt-2 flex items-center justify-between gap-3">
                <p class="text-muted m-0 text-[0.6rem] leading-snug">
                    Matching ignores capitalization and apostrophes. Duplicates
                    and empty lines are ignored.
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
            class={[
                "text-muted flex min-h-24 flex-col items-center justify-center",
                "rounded-xl border border-dashed border-white/10 bg-black/10",
                "px-4 text-center",
            ]}
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
            <div
                class="flex items-center gap-2 border-b border-white/[0.06] p-2.5"
            >
                <label class="relative min-w-0 grow">
                    <span class="sr-only">Search blacklist</span>
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
                        placeholder="Search wallet, token, or nickname"
                        autocomplete="off"
                    />
                </label>
                <button
                    class={[
                        "inline-flex size-9 shrink-0 items-center justify-center rounded-lg",
                        "border border-white/[0.06] text-red-300 transition-colors",
                        "hover:border-red-400/20 hover:bg-red-500/10 hover:text-red-200",
                        "focus-visible:ring-2 focus-visible:ring-red-400",
                        "focus-visible:outline-none",
                    ]}
                    type="button"
                    title="Clear blacklist"
                    aria-label="Clear blacklist"
                    onclick={requestClear}
                >
                    <Trash2 size={14} aria-hidden="true" />
                </button>
            </div>

            {#if visibleEntries.length > 0}
                <ul
                    class="m-0 grid max-h-64 list-none gap-1.5 overflow-y-auto p-2.5"
                    id="blacklist-entries-preview"
                    aria-label="Normalized blacklist preview"
                >
                    {#each visibleEntries as { entry, index } (entry.toLowerCase())}
                        <li
                            class={[
                                "flex min-w-0 items-center gap-2 rounded-lg border",
                                "border-white/[0.06] bg-black/15 px-2.5 py-2",
                                "text-xs text-slate-200",
                            ]}
                        >
                            <span
                                class={[
                                    "flex size-5 shrink-0 items-center justify-center",
                                    "rounded bg-white/[0.06] text-[0.6rem]",
                                    "font-bold text-slate-500",
                                ]}
                                aria-hidden="true"
                            >
                                {index + 1}
                            </span>
                            <span class="min-w-0 grow truncate" title={entry}
                                >{entry}</span
                            >
                            <button
                                class={[
                                    "inline-flex size-7 shrink-0 items-center justify-center",
                                    "rounded-md text-slate-500 transition-colors",
                                    "hover:bg-red-500/10 hover:text-red-300",
                                    "focus-visible:ring-2 focus-visible:ring-red-400",
                                    "focus-visible:outline-none",
                                ]}
                                type="button"
                                title={`Remove ${entry}`}
                                aria-label={`Remove ${entry} from blacklist`}
                                onclick={() => removeEntry(entry)}
                            >
                                <Trash2 size={12} aria-hidden="true" />
                            </button>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p
                    class="text-muted m-0 px-3 py-5 text-center text-xs"
                    role="status"
                >
                    No blacklist entries match “{searchQuery.trim()}”.
                </p>
            {/if}
        </section>
    {/if}
</div>

<dialog
    class={[
        "text-foreground m-auto w-[min(360px,calc(100vw-32px))]",
        "max-w-none rounded-xl border border-red-400/20 bg-[#151822] p-0",
        "shadow-[0_24px_70px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.04)]",
        "backdrop:bg-black/65 backdrop:backdrop-blur-[4px]",
    ]}
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
                class={[
                    "flex size-9 shrink-0 items-center justify-center rounded-[10px]",
                    "border border-red-400/20 bg-red-500/10 text-red-300",
                ]}
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
        <div
            class="mt-4 flex justify-end gap-2 max-[359px]:flex-col max-[359px]:items-stretch"
        >
            <button
                class={[
                    "inline-flex h-9 items-center justify-center rounded-lg border",
                    "border-white/10 bg-white/[0.04] px-3 text-xs font-semibold",
                    "text-slate-300 transition-colors hover:bg-white/[0.07]",
                    "focus-visible:ring-2 focus-visible:ring-slate-400",
                    "focus-visible:outline-none max-[359px]:w-full",
                ]}
                type="button"
                bind:this={keepValuesButton}
                onclick={closeClearDialog}
            >
                Keep values
            </button>
            <button
                class={[
                    "inline-flex h-9 items-center justify-center rounded-lg border",
                    "border-red-400/30 bg-red-500/15 px-3 text-xs font-semibold",
                    "text-red-200 transition-colors hover:border-red-400/45",
                    "hover:bg-red-500/22 focus-visible:ring-2",
                    "focus-visible:ring-red-400 focus-visible:outline-none max-[359px]:w-full",
                ]}
                type="button"
                onclick={clearEntries}
            >
                Clear permanently
            </button>
        </div>
    </div>
</dialog>
