<script lang="ts">
    import SocialLinks from "$lib/components/token-card/SocialLinks.svelte";
    import DevBlacklistButton from "$lib/components/token-card/DevBlacklistButton.svelte";
    import RetryingTokenImage from "$lib/components/token-card/RetryingTokenImage.svelte";
    import { filtersStore } from "$lib/stores/filters.svelte";
    import type { TokenFeed } from "$lib/types";
    import { openExternalUrl } from "$lib/services/opener";
    import { resolveTokenImageUrl } from "$lib/utils/tokenImage";
    import { buildTerminalUrl, buildXProfileUrl } from "$lib/utils/tokenLinks";

    export let feed: TokenFeed;

    $: tokenImageUrl = resolveTokenImageUrl(feed);

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

    function openAdminProfile(event: MouseEvent): void {
        event.preventDefault();
        event.stopPropagation();

        const url = buildXProfileUrl(feed.twitter_admin_nickname);
        if (url) openExternalUrl(url);
    }
</script>

<div
    class="focus-visible:ring-accent-purple/60 cursor-pointer rounded-[10px] border border-transparent px-1.5 pt-1 pb-1.5 transition-[transform,border-color,background-color,box-shadow] duration-150 hover:-translate-y-px hover:border-white/[0.07] hover:bg-white/[0.025] hover:shadow-[0_8px_18px_rgba(0,0,0,0.14)] focus-visible:border-white/[0.08] focus-visible:bg-white/[0.025] focus-visible:ring-1 focus-visible:outline-none motion-reduce:transform-none motion-reduce:transition-none"
    role="button"
    tabindex="0"
    aria-label={`Open ${feed.token_name} in ${filtersStore.terminal.toUpperCase()}`}
    onclick={handleClick}
    onkeydown={handleKeydown}
>
    <div class="flex w-full flex-nowrap items-center gap-2">
        <div
            class="bg-border relative size-8 shrink-0 overflow-hidden rounded-lg border border-white/[0.08] shadow-[0_3px_9px_rgba(0,0,0,0.28)]"
        >
            <div
                class="absolute inset-0 flex items-center justify-center text-base font-bold text-slate-500"
            >
                {feed.token_ticker?.substring(0, 2) || "?"}
            </div>
            {#if tokenImageUrl}
                <RetryingTokenImage
                    className="absolute inset-0 size-full object-cover"
                    src={tokenImageUrl}
                    alt={`${feed.token_ticker} token`}
                />
            {/if}
        </div>

        <div class="flex min-w-0 grow flex-col gap-1.5">
            <div class="flex flex-col justify-center gap-0.5">
                <div class="flex min-w-0 items-start gap-2">
                    <button
                        class="hover:text-accent-purple focus-visible:text-accent-purple focus-visible:ring-accent-purple m-0 flex min-w-0 grow cursor-pointer items-center gap-1.5 border-0 bg-transparent p-0 text-left text-sm font-semibold text-inherit transition-colors duration-150 focus-visible:ring-2 focus-visible:outline-none"
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

                    <DevBlacklistButton {feed} />
                </div>

                {#if buildXProfileUrl(feed.twitter_admin_nickname) !== null}
                    <a
                        class="w-fit truncate text-xs font-medium text-sky-400 underline decoration-sky-400/60 underline-offset-2 transition-[color,text-shadow,text-decoration-color] duration-150 hover:text-sky-300 hover:decoration-sky-300 hover:[text-shadow:0_0_8px_rgba(56,189,248,0.65)] focus-visible:rounded-sm focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:outline-none"
                        href={buildXProfileUrl(feed.twitter_admin_nickname) ??
                            undefined}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`Open ${feed.twitter_admin_nickname} on X`}
                        aria-label={`Open ${feed.twitter_admin_nickname} on X`}
                        onclick={openAdminProfile}
                    >
                        {feed.twitter_admin_nickname}
                    </a>
                {/if}
            </div>

            <SocialLinks token={feed} />
        </div>
    </div>
</div>
