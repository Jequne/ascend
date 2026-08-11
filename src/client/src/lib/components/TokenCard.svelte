<script lang="ts">
    import DeveloperStats from "$lib/components/token-card/DeveloperStats.svelte";
    import LastTokensList from "$lib/components/token-card/LastTokensList.svelte";
    import TokenMainInfo from "$lib/components/token-card/TokenMainInfo.svelte";
    import type { TokenFeed } from "$lib/types";

    export let feed: TokenFeed;
</script>

<article
    class="bg-canvas focus-within:border-accent-purple/30 my-1 mr-2 ml-2 flex w-[calc(100%-16px)] max-w-full flex-col gap-1.5 rounded-[10px] border border-white/[0.06] px-2.5 py-1.5 shadow-[0_4px_6px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.025)] transition-[transform,border-color,box-shadow] duration-200 hover:-translate-y-px hover:border-white/10 hover:shadow-[0_8px_18px_rgba(0,0,0,0.24),inset_0_1px_0_rgba(255,255,255,0.04)] motion-reduce:transform-none motion-reduce:transition-none"
    data-testid="token-card"
    data-token-key={feed.clientKey}
>
    <section class="border-border flex w-full flex-col gap-2 border-b pb-2.5">
        <TokenMainInfo {feed} />
        <DeveloperStats {feed} />
    </section>

    {#if feed.last_deployed_tokens.length > 0}
        <LastTokensList tokens={feed.last_deployed_tokens} />
    {/if}
</article>
