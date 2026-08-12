<script lang="ts">
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { TokenFeed } from "$lib/types";
    import { normalizeBlacklistEntries } from "$lib/utils/blacklist";
    import { hasRelevantIndicator } from "$lib/utils/tokenDisplay";
    import { Database } from "@lucide/svelte";

    export let feed: TokenFeed;

    let devWalletBlacklisted = false;

    $: visible = hasRelevantIndicator(feed) && Boolean(feed.dev_wallet);
    $: if (visible) {
        devWalletBlacklisted = isDevWalletBlacklisted();
    }

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

{#if visible}
    <button
        class="inline-flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-[10px] border transition-[background-color,border-color,color,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-orange-400 focus-visible:outline-none {devWalletBlacklisted
            ? 'border-red-500/45 bg-red-500/15 text-red-300 hover:border-red-500/65 hover:bg-red-500/20 hover:text-red-200'
            : 'border-orange-500/40 bg-orange-500/15 text-orange-300 hover:border-orange-400/65 hover:bg-orange-500/22 hover:text-orange-200'} hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
        type="button"
        data-testid="developer-blacklist-button"
        title={devWalletBlacklisted
            ? "Remove from blacklist"
            : "Add to blacklist"}
        aria-label={devWalletBlacklisted
            ? "Remove developer wallet from blacklist"
            : "Add developer wallet to blacklist"}
        aria-pressed={devWalletBlacklisted}
        onclick={toggleDevWalletBlacklist}
    >
        <Database size={15} strokeWidth={2} aria-hidden="true" />
    </button>
{/if}
