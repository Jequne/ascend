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
            class="focus-visible:ring-accent-purple focus-visible:ring-offset-canvas inline-flex h-10 min-w-[110px] cursor-pointer items-center justify-center rounded-[10px] border px-3 text-[13px] font-semibold tracking-[0.2px] shadow-[0_4px_15px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)] transition-[transform,background-color,border-color,box-shadow] duration-200 hover:-translate-y-px focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:translate-y-0 motion-reduce:transform-none max-[600px]:h-9 max-[600px]:min-w-20 max-[600px]:px-2 max-[600px]:text-xs {wsStore.isConnected
                ? 'border-green-400/20 bg-[linear-gradient(145deg,rgba(62,223,167,0.1),rgba(62,223,167,0.02))] text-green-400 hover:border-green-400/35 hover:bg-[linear-gradient(145deg,rgba(62,223,167,0.15),rgba(62,223,167,0.05))]'
                : 'text-danger border-[#ec6572]/20 bg-[linear-gradient(145deg,rgba(236,101,114,0.1),rgba(236,101,114,0.02))] hover:border-[#ec6572]/35 hover:bg-[linear-gradient(145deg,rgba(236,101,114,0.15),rgba(236,101,114,0.05))]'}"
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
            class="inline-flex h-10 cursor-default items-center justify-center rounded-[10px] border border-[#de93c8]/20 bg-[linear-gradient(145deg,rgba(222,147,200,0.1),rgba(222,147,200,0.02))] px-3 text-[13px] font-semibold tracking-[0.2px] text-[#e696c2] shadow-[0_4px_15px_rgba(222,147,200,0.1),inset_0_1px_0_rgba(222,147,200,0.1)] max-[600px]:h-9 max-[600px]:px-2 max-[600px]:text-xs"
            aria-label={`Solana price ${formatSolPrice(wsStore.solPrice)}`}
        >
            <img
                class="size-4 max-[600px]:size-3.5"
                src="/icons/solana.svg"
                alt=""
                aria-hidden="true"
            />
            <span class="ml-2 max-[600px]:ml-1">
                {wsStore.isConnected ? formatSolPrice(wsStore.solPrice) : "-"}
            </span>
        </div>

        <div
            class="inline-flex h-10 cursor-default items-center justify-center rounded-[10px] border border-[#a4adcf]/20 bg-[linear-gradient(145deg,rgba(164,173,207,0.1),rgba(164,173,207,0.02))] px-3 text-[13px] font-semibold tracking-[0.2px] text-[#a7accc] shadow-[0_4px_15px_rgba(164,173,207,0.1),inset_0_1px_0_rgba(164,173,207,0.1)] max-[600px]:h-9 max-[600px]:px-2 max-[600px]:text-xs"
            aria-label={`${wsStore.tokenFeedCount} accepted of ${wsStore.tokenFeedTotalCount} incoming tokens`}
        >
            # {wsStore.tokenFeedCount}/{wsStore.tokenFeedTotalCount}
        </div>

        <button
            class="hover:text-foreground focus-visible:ring-accent-purple focus-visible:ring-offset-canvas ml-auto inline-flex size-10 cursor-pointer items-center justify-center rounded-[10px] border border-white/[0.08] bg-[linear-gradient(145deg,#1e2029,#252835)] text-[#a0aec0] shadow-[0_4px_15px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)] transition-[transform,background-color,border-color,color,box-shadow] duration-200 hover:-translate-y-px hover:border-white/15 hover:bg-[linear-gradient(145deg,#272a35,#2f3342)] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:translate-y-0 motion-reduce:transform-none max-[600px]:size-9"
            type="button"
            bind:this={settingsButton}
            onclick={() => (settingsOpen = true)}
            title="Settings"
            aria-label="Open settings"
        >
            <Settings2 size={16} aria-hidden="true" />
        </button>

        <button
            class="hover:border-danger/35 hover:text-danger focus-visible:ring-danger focus-visible:ring-offset-canvas inline-flex size-10 cursor-pointer items-center justify-center rounded-[10px] border border-white/[0.08] bg-[linear-gradient(145deg,#1e2029,#252835)] text-[#a0aec0] shadow-[0_4px_15px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)] transition-[transform,background-color,border-color,color,box-shadow] duration-200 hover:-translate-y-px hover:bg-[linear-gradient(145deg,rgba(235,105,118,0.14),rgba(235,105,118,0.04))] focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0 disabled:hover:border-white/[0.08] disabled:hover:text-[#a0aec0] motion-reduce:transform-none max-[600px]:size-9"
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
