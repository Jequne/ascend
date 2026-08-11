<script lang="ts">
    import SocialLinks from "$lib/components/token-card/SocialLinks.svelte";
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { TokenFeed } from "$lib/types";
    import { openExternalUrl } from "$lib/services/opener";
    import { buildTerminalUrl } from "$lib/utils/tokenLinks";

    export let feed: TokenFeed;

    function openTerminal(): void {
        const url = buildTerminalUrl(feed, filtersStore.terminal);
        if (url) openExternalUrl(url);
    }

    function handleClick(event: MouseEvent): void {
        if (
            event.target instanceof Element &&
            event.target.closest("a, button, input, textarea, select, label")
        ) {
            return;
        }

        openTerminal();
    }

    function handleKeydown(event: KeyboardEvent): void {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        openTerminal();
    }

    function copyAddress(): void {
        if (!feed.token_address) return;
        void navigator.clipboard.writeText(feed.token_address);
    }

    function hideBrokenImage(event: Event): void {
        if (event.currentTarget instanceof HTMLImageElement) {
            event.currentTarget.style.display = "none";
        }
    }
</script>

<div
    class="focus-visible:ring-accent-purple/60 relative isolate cursor-pointer overflow-hidden rounded-lg px-0.5 pt-0.5 pb-1 transition-[transform,border-color,box-shadow,background-color] duration-150 before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit] before:bg-[linear-gradient(135deg,rgba(129,140,248,0.12),transparent_42%),linear-gradient(315deg,rgba(16,185,129,0.08),transparent_55%)] before:opacity-0 before:transition-opacity before:duration-150 hover:-translate-y-px hover:shadow-[0_10px_24px_rgba(0,0,0,0.18),0_0_0_1px_rgba(129,140,248,0.12)] hover:before:opacity-100 focus-visible:-translate-y-px focus-visible:shadow-[0_10px_24px_rgba(0,0,0,0.18)] focus-visible:ring-1 focus-visible:outline-none focus-visible:before:opacity-100 motion-reduce:transform-none motion-reduce:transition-none"
    role="button"
    tabindex="0"
    aria-label={`Open ${feed.token_name} in ${filtersStore.terminal.toUpperCase()}`}
    onclick={handleClick}
    onkeydown={handleKeydown}
>
    <div class="relative z-[1] flex w-full flex-nowrap items-center gap-2">
        <div
            class="bg-border relative size-8 shrink-0 overflow-hidden rounded-md"
        >
            <div
                class="absolute inset-0 flex items-center justify-center text-base font-bold text-slate-500"
            >
                {feed.token_ticker?.substring(0, 2) || "?"}
            </div>
            {#if feed.token_image}
                <img
                    class="absolute inset-0 size-full object-cover"
                    src={feed.token_image}
                    alt={`${feed.token_ticker} token`}
                    onerror={hideBrokenImage}
                />
            {/if}
        </div>

        <div class="flex min-w-0 grow flex-col gap-1.5">
            <div class="flex flex-col justify-center">
                <button
                    class="hover:text-accent-purple focus-visible:text-accent-purple focus-visible:ring-accent-purple m-0 flex w-full cursor-pointer items-center gap-1.5 border-0 bg-transparent p-0 text-left text-sm font-semibold text-inherit transition-colors duration-150 focus-visible:ring-2 focus-visible:outline-none"
                    type="button"
                    title="Copy token address"
                    aria-label={`Copy ${feed.token_ticker} address`}
                    onclick={(event) => {
                        event.stopPropagation();
                        copyAddress();
                    }}
                >
                    <span
                        class="text-muted shrink-0 rounded bg-white/[0.08] px-1 py-0.5 text-xs font-normal"
                        >${feed.token_ticker}</span
                    >
                    <span class="truncate">{feed.token_name}</span>
                </button>

                <div class="mt-0.5 flex flex-wrap items-center">
                    {#if feed.dev_holds_percent !== null}
                        <span
                            class="inline-flex items-center rounded border border-amber-500/30 bg-amber-500/15 px-1.5 py-0.5 text-[0.7rem] font-semibold tracking-[0.02em] text-amber-400 shadow-[0_2px_4px_rgba(0,0,0,0.1)]"
                        >
                            DH: {feed.dev_holds_percent.toFixed(1)}%
                        </span>
                    {/if}
                </div>
            </div>

            <SocialLinks token={feed} />
        </div>
    </div>
</div>
