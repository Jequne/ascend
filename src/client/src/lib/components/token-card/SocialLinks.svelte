<script lang="ts">
    import { openExternalUrl } from "$lib/services/opener";
    import type { LastDeployedToken, TokenFeed } from "$lib/types";
    import { normalizeExternalUrl } from "$lib/utils/tokenLinks";
    import { Globe } from "@lucide/svelte";

    export let token: TokenFeed | LastDeployedToken;

    function openLink(event: MouseEvent, value: string | null): void {
        event.preventDefault();
        event.stopPropagation();

        const url = normalizeExternalUrl(value);
        if (url) openExternalUrl(url);
    }
</script>

<div class="relative z-[2] flex shrink-0 items-center gap-1.5">
    {#if normalizeExternalUrl(token.website) !== null}
        <a
            class="text-muted hover:text-foreground focus-visible:text-foreground focus-visible:ring-accent-purple inline-flex size-[18px] items-center justify-center rounded opacity-70 transition-[opacity,color,box-shadow] duration-150 hover:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:outline-none"
            href={normalizeExternalUrl(token.website) ?? undefined}
            target="_blank"
            rel="noopener noreferrer"
            title="Website"
            aria-label="Open website"
            onclick={(event) => openLink(event, token.website)}
        >
            <Globe size={12} strokeWidth={2} aria-hidden="true" />
        </a>
    {/if}

    {#if normalizeExternalUrl(token.twitter) !== null}
        <a
            class="focus-visible:ring-accent-purple inline-flex size-[18px] items-center justify-center rounded opacity-70 transition-[opacity,box-shadow] duration-150 hover:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:outline-none"
            href={normalizeExternalUrl(token.twitter) ?? undefined}
            target="_blank"
            rel="noopener noreferrer"
            title="X"
            aria-label="Open X profile"
            onclick={(event) => openLink(event, token.twitter)}
        >
            <img class="size-3" src="/icons/x.svg" alt="" aria-hidden="true" />
        </a>
    {/if}

    {#if normalizeExternalUrl(token.telegram) !== null}
        <a
            class="focus-visible:ring-accent-purple inline-flex size-[18px] items-center justify-center rounded opacity-70 transition-[opacity,box-shadow] duration-150 hover:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:outline-none"
            href={normalizeExternalUrl(token.telegram) ?? undefined}
            target="_blank"
            rel="noopener noreferrer"
            title="Telegram"
            aria-label="Open Telegram"
            onclick={(event) => openLink(event, token.telegram)}
        >
            <img
                class="size-3"
                src="/icons/telegram.svg"
                alt=""
                aria-hidden="true"
            />
        </a>
    {/if}

    {#if normalizeExternalUrl(token.discord) !== null}
        <a
            class="focus-visible:ring-accent-purple inline-flex size-[18px] items-center justify-center rounded opacity-70 transition-[opacity,box-shadow] duration-150 hover:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:outline-none"
            href={normalizeExternalUrl(token.discord) ?? undefined}
            target="_blank"
            rel="noopener noreferrer"
            title="Discord"
            aria-label="Open Discord"
            onclick={(event) => openLink(event, token.discord)}
        >
            <img
                class="size-3"
                src="/icons/discord.svg"
                alt=""
                aria-hidden="true"
            />
        </a>
    {/if}
</div>
