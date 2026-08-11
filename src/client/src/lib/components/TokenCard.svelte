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
    class="token-card focus-within:border-accent-purple/30 relative isolate my-1 mr-2 ml-2 flex w-[calc(100%-16px)] max-w-full flex-col gap-1.5 rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(35,38,50,0.97),rgba(23,24,33,0.98))] px-2.5 py-1.5 shadow-[0_8px_22px_rgba(0,0,0,0.24),inset_0_1px_0_rgba(255,255,255,0.04)] transition-[border-color,box-shadow] duration-200 hover:shadow-[0_10px_25px_rgba(0,0,0,0.28),inset_0_1px_0_rgba(255,255,255,0.05)]"
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
        border-color: rgb(16 185 129 / 0.3);
        background:
            linear-gradient(145deg, rgb(16 185 129 / 0.055), transparent 42%),
            linear-gradient(145deg, rgb(35 38 50 / 0.97), rgb(23 24 33 / 0.98));
    }

    .token-card[data-last-tokens="true"] {
        border-color: rgb(214 185 74 / 0.3);
        background:
            linear-gradient(145deg, rgb(214 185 74 / 0.055), transparent 42%),
            linear-gradient(145deg, rgb(35 38 50 / 0.97), rgb(23 24 33 / 0.98));
    }

    .token-card[data-dev-migrations="true"][data-last-tokens="true"] {
        border-color: rgb(112 187 102 / 0.38);
        background:
            linear-gradient(
                115deg,
                rgb(16 185 129 / 0.07),
                transparent 42%,
                rgb(214 185 74 / 0.07)
            ),
            linear-gradient(145deg, rgb(35 38 50 / 0.97), rgb(23 24 33 / 0.98));
    }

    .token-card[data-dev-migrations="true"]::before,
    .token-card[data-last-tokens="true"]::before {
        position: absolute;
        z-index: -1;
        inset: -2px;
        border-radius: inherit;
        background: rgb(16 185 129 / 0.22);
        filter: blur(7px);
        content: "";
        pointer-events: none;
        animation: token-card-glow 3.8s ease-in-out infinite alternate;
        will-change: opacity;
    }

    .token-card[data-last-tokens="true"]::before {
        background: rgb(214 185 74 / 0.22);
    }

    .token-card[data-dev-migrations="true"][data-last-tokens="true"]::before {
        background: linear-gradient(
            105deg,
            rgb(16 185 129 / 0.25),
            rgb(214 185 74 / 0.24)
        );
    }

    @keyframes token-card-glow {
        from {
            opacity: 0.38;
        }
        to {
            opacity: 0.72;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .token-card[data-dev-migrations="true"]::before,
        .token-card[data-last-tokens="true"]::before {
            animation: none;
            opacity: 0.52;
            will-change: auto;
        }
    }
</style>
