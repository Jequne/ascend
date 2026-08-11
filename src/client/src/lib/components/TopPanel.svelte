<script lang="ts">
    import SettingsDialog from "$lib/components/settings/SettingsDialog.svelte";
    import { wsStore } from "$lib/stores/websocket.svelte";
    import { Settings2, Trash2, Wifi, WifiOff } from "@lucide/svelte";
    import { onDestroy } from "svelte";

    let settingsOpen = false;
    let settingsButton: HTMLButtonElement | null = null;

    function formatSolPrice(value: number | string | null): string {
        const numericValue = Number(value);
        return Number.isFinite(numericValue)
            ? `$${numericValue.toFixed(1)}`
            : "-";
    }

    onDestroy(() => {
        wsStore.disconnect();
    });
</script>

<header
    class="relative z-10 flex min-h-[10vh] w-full shrink-0 items-center bg-linear-to-b from-[rgba(15,17,26,0.8)] to-transparent px-4 py-3 max-[600px]:px-3 max-[600px]:py-2"
>
    <div class="flex w-full flex-wrap items-center gap-2 max-[600px]:gap-1.5">
        <button
            type="button"
            class="focus-visible:ring-accent-purple focus-visible:ring-offset-canvas inline-flex h-[42px] min-w-[116px] cursor-pointer items-center justify-center rounded-lg border bg-[#1b1e28] px-3 text-[13px] font-medium tracking-[0.1px] shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] transition-colors duration-150 hover:bg-[#222631] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:bg-[#171a23] max-[600px]:min-w-[104px] max-[600px]:px-2.5 max-[600px]:text-xs {wsStore.isConnected
                ? 'border-emerald-400/25 text-emerald-300 hover:border-emerald-400/40 hover:bg-emerald-400/[0.06]'
                : 'border-red-400/25 text-red-300 hover:border-red-400/40 hover:bg-red-400/[0.06]'}"
            onclick={wsStore.toggleConnection}
            title={wsStore.isConnected ? "Disconnect feed" : "Connect feed"}
            aria-label={wsStore.isConnected
                ? "Disconnect token feed"
                : "Connect token feed"}
        >
            {#if wsStore.isConnected}
                <Wifi size={16} aria-hidden="true" />
            {:else}
                <WifiOff size={16} aria-hidden="true" />
            {/if}
            <span class="ml-2 max-[600px]:ml-1">
                {#if wsStore.isConnected}
                    {wsStore.ping}ms
                {:else if wsStore.isConnecting}
                    ...
                {:else}
                    Offline
                {/if}
            </span>
        </button>

        <div
            class="inline-flex h-[42px] cursor-default items-center justify-center rounded-lg border border-[#de93c8]/20 bg-[#1b1e28] px-3 text-[13px] font-medium tracking-[0.1px] text-[#e696c2] shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] max-[600px]:px-2.5 max-[600px]:text-xs"
            aria-label={`Solana price ${formatSolPrice(wsStore.solPrice)}`}
        >
            <img
                class="size-[17px] max-[600px]:size-4"
                src="/icons/solana.svg"
                alt=""
                aria-hidden="true"
            />
            <span class="ml-2 max-[600px]:ml-1">
                {wsStore.isConnected ? formatSolPrice(wsStore.solPrice) : "-"}
            </span>
        </div>

        <div
            class="inline-flex h-[42px] cursor-default items-center justify-center rounded-lg border border-[#a4adcf]/20 bg-[#1b1e28] px-3 text-[13px] font-medium tracking-[0.1px] text-[#b5bbd6] shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] max-[600px]:px-2.5 max-[600px]:text-xs"
            aria-label={`${wsStore.tokenFeedCount} accepted of ${wsStore.tokenFeedTotalCount} incoming tokens`}
        >
            # {wsStore.tokenFeedCount}/{wsStore.tokenFeedTotalCount}
        </div>

        <button
            class="hover:text-foreground focus-visible:ring-accent-purple focus-visible:ring-offset-canvas ml-auto inline-flex size-[42px] cursor-pointer items-center justify-center rounded-lg border border-white/[0.09] bg-[#1b1e28] text-[#a0aec0] shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] transition-colors duration-150 hover:border-white/15 hover:bg-[#242832] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:bg-[#171a23]"
            type="button"
            bind:this={settingsButton}
            onclick={() => (settingsOpen = true)}
            title="Settings"
            aria-label="Open settings"
        >
            <Settings2 size={16} aria-hidden="true" />
        </button>

        <button
            class="hover:border-danger/35 hover:text-danger focus-visible:ring-danger focus-visible:ring-offset-canvas inline-flex size-[42px] cursor-pointer items-center justify-center rounded-lg border border-white/[0.09] bg-[#1b1e28] text-[#a0aec0] shadow-[inset_0_1px_0_rgba(255,255,255,0.035)] transition-colors duration-150 hover:bg-red-400/[0.06] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:bg-red-400/[0.09] disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:border-white/[0.09] disabled:hover:bg-[#1b1e28] disabled:hover:text-[#a0aec0]"
            type="button"
            onclick={wsStore.clearTokens}
            disabled={wsStore.tokenFeeds.length === 0}
            title="Clear visible tokens"
            aria-label="Clear visible tokens"
        >
            <Trash2 size={16} aria-hidden="true" />
        </button>
    </div>
</header>

<SettingsDialog bind:open={settingsOpen} trigger={settingsButton} />
