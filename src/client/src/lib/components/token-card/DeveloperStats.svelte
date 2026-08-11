<script lang="ts">
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { TokenFeed } from "$lib/types";
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import { hasRelevantIndicator } from "$lib/utils/tokenDisplay";
    import { CircleCheck, Database, TrendingUp } from "@lucide/svelte";

    export let feed: TokenFeed;

    let devWalletBlacklisted = false;

    $: showDevBlacklistButton =
        hasRelevantIndicator(feed) && Boolean(feed.dev_wallet);
    $: if (showDevBlacklistButton) {
        devWalletBlacklisted = isDevWalletBlacklisted();
    }
    $: migratedRatio = feed.all_tokens_count
        ? ((feed.migrated_tokens_count / feed.all_tokens_count) * 100).toFixed(
              1,
          )
        : "0";

    function isDevWalletBlacklisted(): boolean {
        const devWallet = feed.dev_wallet.trim().toLowerCase();
        return normalizeBlacklistEntries(filtersStore.blacklist).some(
            (entry) => entry.toLowerCase() === devWallet,
        );
    }

    function toggleDevWalletBlacklist(): void {
        const devWallet = feed.dev_wallet.trim();
        if (!devWallet) return;

        const blacklist = normalizeBlacklistEntries(filtersStore.blacklist);
        const normalizedDevWallet = devWallet.toLowerCase();
        const isBlacklisted = blacklist.some(
            (entry) => entry.toLowerCase() === normalizedDevWallet,
        );

        filtersStore.blacklist = isBlacklisted
            ? blacklist.filter(
                  (entry) => entry.toLowerCase() !== normalizedDevWallet,
              )
            : [...blacklist, devWallet];
        devWalletBlacklisted = !isBlacklisted;
    }
</script>

<div class="mt-0.5 flex flex-col gap-1.5">
    <div class="flex w-full items-center gap-2">
        <div class="flex min-w-0 flex-wrap items-center gap-1.5">
            {#each feed.indicators as indicator (indicator)}
                <span
                    class="rounded border px-1.5 py-0.5 text-[0.7rem] font-semibold whitespace-nowrap uppercase {indicator
                        .trim()
                        .toLowerCase() === 'last tokens'
                        ? 'border-[#d6b94a]/35 bg-[#d6b94a]/15 text-[#e2ca67]'
                        : 'text-success border-emerald-500/30 bg-emerald-500/15'}"
                    >{indicator}</span
                >
            {/each}
            <span
                class="rounded border border-purple-500/30 bg-purple-500/15 px-1.5 py-0.5 text-[0.7rem] font-semibold whitespace-nowrap text-purple-400 uppercase"
                >{feed.blockchain || "sol"}</span
            >
        </div>

        {#if showDevBlacklistButton}
            <button
                class="ml-auto inline-flex h-6 min-w-11 cursor-pointer items-center justify-center gap-1 rounded-md border px-1.5 text-[0.65rem] leading-none font-extrabold tracking-[0.03em] whitespace-nowrap uppercase transition-[background-color,border-color,color,transform,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:outline-none motion-reduce:transform-none {devWalletBlacklisted
                    ? 'border-red-500/45 bg-red-500/15 text-red-300 hover:border-red-500/65 hover:bg-red-500/20 hover:text-red-200'
                    : 'border-orange-500/40 bg-orange-500/15 text-orange-300 hover:border-orange-500/60 hover:bg-orange-500/25 hover:text-orange-200'} hover:-translate-y-px active:translate-y-0"
                type="button"
                title={devWalletBlacklisted
                    ? "Remove from blacklist"
                    : "Add to blacklist"}
                aria-label={devWalletBlacklisted
                    ? "Remove developer wallet from blacklist"
                    : "Add developer wallet to blacklist"}
                aria-pressed={devWalletBlacklisted}
                onclick={toggleDevWalletBlacklist}
            >
                <Database size={12} strokeWidth={2} aria-hidden="true" />
                <span>{devWalletBlacklisted ? "Dev BL-" : "Dev BL+"}</span>
            </button>
        {/if}
    </div>

    <div
        class="flex flex-wrap items-center gap-2 rounded-lg border border-white/[0.045] bg-black/10 px-2 py-1.5 text-[0.8rem] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]"
    >
        <span
            class="text-foreground inline-flex items-center gap-1"
            title="Total Tokens"
        >
            <Database size={10} strokeWidth={2} aria-hidden="true" />
            {feed.all_tokens_count} tokens
        </span>
        <span class="size-1 rounded-full bg-white/20" aria-hidden="true"></span>
        <span
            class="text-success inline-flex items-center gap-1"
            title="Migrated Tokens"
        >
            <CircleCheck size={10} strokeWidth={2} aria-hidden="true" />
            {feed.migrated_tokens_count} migrated
        </span>
        <span class="size-1 rounded-full bg-white/20" aria-hidden="true"></span>
        <span
            class="text-accent-blue inline-flex items-center gap-1 font-medium"
            title="Migration Rate"
        >
            <TrendingUp size={10} strokeWidth={2} aria-hidden="true" />
            {migratedRatio}% rate
        </span>
        {#if feed.is_migrated}
            <span title="Migrated" aria-label="Migrated">
                <CircleCheck size={10} strokeWidth={2} aria-hidden="true" />
            </span>
        {/if}
    </div>
</div>
