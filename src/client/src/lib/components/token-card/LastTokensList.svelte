<script lang="ts">
    import SocialLinks from "$lib/components/token-card/SocialLinks.svelte";
    import { openExternalUrl } from "$lib/services/opener";
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { LastDeployedToken } from "$lib/types";
    import { buildTerminalUrl } from "$lib/utils/tokenLinks";
    import { formatCompactNumber, timeAgo } from "$lib/utils/tokenDisplay";
    import {
        ChartNoAxesCombined,
        CircleCheck,
        Clock3,
        Zap,
    } from "@lucide/svelte";

    export let tokens: LastDeployedToken[];

    function openTerminal(token: LastDeployedToken): void {
        const url = buildTerminalUrl(token, filtersStore.terminal);
        if (url) openExternalUrl(url);
    }

    function handleClick(event: MouseEvent, token: LastDeployedToken): void {
        if (
            event.target instanceof Element &&
            event.target.closest("a, button, input, textarea, select, label")
        ) {
            return;
        }

        openTerminal(token);
    }

    function handleKeydown(
        event: KeyboardEvent,
        token: LastDeployedToken,
    ): void {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        openTerminal(token);
    }

    function hideBrokenImage(event: Event): void {
        if (event.currentTarget instanceof HTMLImageElement) {
            event.currentTarget.style.display = "none";
        }
    }
</script>

<section class="flex w-full flex-col" aria-labelledby="last-tokens-heading">
    <h4
        id="last-tokens-heading"
        class="m-0 text-xs tracking-[0.05em] text-slate-500 uppercase"
    >
        Last Tokens
    </h4>
    <div class="flex flex-col gap-2">
        {#each tokens as token, index (`${token.token_address}:${index}`)}
            <div
                class="hover:border-accent-purple/20 focus-visible:border-accent-purple/30 focus-visible:ring-accent-purple/60 relative isolate flex cursor-pointer flex-wrap items-center justify-between gap-2 overflow-hidden rounded-md border border-white/[0.03] bg-black/15 px-2 py-1.5 transition-[transform,border-color,box-shadow,background-color] duration-150 before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit] before:bg-[linear-gradient(135deg,rgba(129,140,248,0.12),transparent_42%),linear-gradient(315deg,rgba(16,185,129,0.08),transparent_55%)] before:opacity-0 before:transition-opacity before:duration-150 hover:-translate-y-px hover:shadow-[0_10px_24px_rgba(0,0,0,0.18),0_0_0_1px_rgba(129,140,248,0.12)] hover:before:opacity-100 focus-visible:-translate-y-px focus-visible:ring-1 focus-visible:outline-none focus-visible:before:opacity-100 motion-reduce:transform-none motion-reduce:transition-none"
                role="button"
                tabindex="0"
                aria-label={`Open ${token.token_name} in ${filtersStore.terminal.toUpperCase()}`}
                onclick={(event) => handleClick(event, token)}
                onkeydown={(event) => handleKeydown(event, token)}
            >
                <div
                    class="relative z-[1] flex min-w-0 grow items-center gap-2"
                >
                    <div
                        class="bg-border relative size-[26px] shrink-0 overflow-hidden rounded-md"
                    >
                        <div
                            class="absolute inset-0 flex items-center justify-center text-[0.8rem] font-bold text-slate-500"
                        >
                            {token.token_ticker?.substring(0, 2) || "?"}
                        </div>
                        {#if token.token_image}
                            <img
                                class="absolute inset-0 size-full object-cover"
                                src={token.token_image}
                                alt={`${token.token_ticker} token`}
                                onerror={hideBrokenImage}
                            />
                        {/if}
                    </div>

                    <div class="flex min-w-0 grow flex-col gap-0.5">
                        <div
                            class="flex w-full items-center gap-1.5 text-[0.85rem] leading-[1.2] font-medium"
                        >
                            <span
                                class="text-muted shrink-0 rounded bg-white/[0.08] px-1 py-0.5 text-xs font-normal"
                                >${token.token_ticker}</span
                            >
                            <span class="truncate">{token.token_name}</span>
                        </div>

                        <div
                            class="text-muted flex flex-wrap items-center gap-2 text-[0.7rem]"
                        >
                            <span
                                class="text-accent-purple inline-flex items-center gap-1"
                            >
                                <Clock3 size={11} aria-hidden="true" />
                                {timeAgo(token.created_at)} ago
                            </span>
                            {#if token.ath_mcap_in_usd}
                                <span
                                    class="text-success inline-flex items-center gap-1 font-medium"
                                >
                                    <ChartNoAxesCombined
                                        size={11}
                                        aria-hidden="true"
                                    />
                                    ${formatCompactNumber(
                                        token.ath_mcap_in_usd,
                                    )}
                                </span>
                            {/if}
                            {#if token.total_pair_fees_paid}
                                <span
                                    class="inline-flex items-center gap-1 text-amber-400"
                                >
                                    <Zap size={11} aria-hidden="true" />
                                    {token.total_pair_fees_paid.toFixed(1)} SOL
                                </span>
                            {/if}
                            {#if token.dex_paid}
                                <span
                                    title="DEX Screener paid"
                                    aria-label="DEX Screener paid"
                                >
                                    <img
                                        class="size-3 opacity-80"
                                        src="/icons/dexscreener_logo.svg"
                                        alt=""
                                        aria-hidden="true"
                                    />
                                </span>
                            {/if}
                            {#if token.is_migrated}
                                <span
                                    class="inline-flex"
                                    title="Migrated"
                                    aria-label="Migrated"
                                >
                                    <CircleCheck size={12} aria-hidden="true" />
                                </span>
                            {/if}
                        </div>
                    </div>
                </div>

                <div class="relative z-[1]">
                    <SocialLinks {token} />
                </div>
            </div>
        {/each}
    </div>
</section>
