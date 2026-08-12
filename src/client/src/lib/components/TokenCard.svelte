<script lang="ts">
    import DeveloperStats from "$lib/components/token-card/DeveloperStats.svelte";
    import LastTokensList from "$lib/components/token-card/LastTokensList.svelte";
    import TokenMainInfo from "$lib/components/token-card/TokenMainInfo.svelte";
    import type { TokenFeed } from "$lib/types";
    import { hasIndicator } from "$lib/utils/tokenDisplay";

    export let feed: TokenFeed;

    $: hasDevMigrations = hasIndicator(feed, "dev migrations");
    $: hasLastTokens = hasIndicator(feed, "last tokens");
</script>

<article
    class="token-card focus-within:border-accent-purple/30 relative isolate my-1 mr-2 ml-2 flex w-[calc(100%-16px)] max-w-full flex-col gap-1.5 rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(35,38,50,0.97),rgba(23,24,33,0.98))] px-2.5 py-1.5 shadow-[0_8px_22px_rgba(0,0,0,0.24),inset_0_1px_0_rgba(255,255,255,0.04)] transition-[border-color,box-shadow] duration-200 ease-out hover:border-white/[0.1] hover:shadow-[0_9px_24px_rgba(0,0,0,0.26),inset_0_1px_0_rgba(255,255,255,0.05)]"
    data-testid="token-card"
    data-token-key={feed.clientKey}
    data-dev-migrations={hasDevMigrations}
    data-last-tokens={hasLastTokens}
>
    <section
        class="flex w-full flex-col gap-2 border-b border-white/[0.065] pb-2.5"
    >
        <TokenMainInfo {feed} />
        <DeveloperStats {feed} />
    </section>

    {#if feed.last_deployed_tokens.length > 0}
        <LastTokensList tokens={feed.last_deployed_tokens} />
    {/if}
</article>

<style>
    .token-card[data-dev-migrations="true"] {
        border-color: rgb(52 211 153 / 0.48);
        box-shadow:
            0 0 0 1px rgb(16 185 129 / 0.08),
            0 0 9px rgb(16 185 129 / 0.12),
            0 8px 22px rgb(0 0 0 / 0.24),
            inset 0 1px 0 rgb(255 255 255 / 0.04);
    }

    .token-card[data-last-tokens="true"] {
        border-color: rgb(214 185 74 / 0.48);
        box-shadow:
            0 0 0 1px rgb(214 185 74 / 0.08),
            0 0 9px rgb(214 185 74 / 0.12),
            0 8px 22px rgb(0 0 0 / 0.24),
            inset 0 1px 0 rgb(255 255 255 / 0.04);
    }

    .token-card[data-dev-migrations="true"][data-last-tokens="true"] {
        border-color: rgb(112 187 102 / 0.56);
        box-shadow:
            0 0 0 1px rgb(112 187 102 / 0.1),
            0 0 9px rgb(112 187 102 / 0.14),
            0 8px 22px rgb(0 0 0 / 0.24),
            inset 0 1px 0 rgb(255 255 255 / 0.04);
    }
</style>
