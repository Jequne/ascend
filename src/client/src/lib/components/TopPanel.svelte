<script>
    import { onDestroy } from "svelte";
    import { wsStore } from "$lib/stores/websocket.svelte.js";

    onDestroy(() => {
        wsStore.disconnect();
    });
</script>

<div class="top-panel">
    <div class="panel-content">
        <!-- Connect / Ping Button -->
        <button
            type="button"
            class="pill-btn ws-btn {wsStore.isConnected
                ? 'connected'
                : 'disconnected'}"
            onclick={wsStore.toggleConnection}
        >
            <img
                src={wsStore.isConnected
                    ? "/icons/wifi-connected.svg"
                    : "/icons/wifi-disconnected.svg"}
                alt="Connection Status"
                class="icon"
            />
            <span class="text">
                {#if wsStore.isConnected}
                    {wsStore.ping}ms
                {:else if wsStore.isConnecting}
                    ...
                {:else}
                    Offline
                {/if}
            </span>
        </button>

        <!-- Placeholder Buttons for Design -->
        <div class="pill-btn purple-btn">
            <img src="/icons/solana.svg" alt="Solana Logo" class="icon" />
            <span class="text">
                {#if wsStore.isConnected && wsStore.solPrice !== null}
                    ${typeof wsStore.solPrice === "number"
                        ? wsStore.solPrice.toFixed(1)
                        : parseFloat(wsStore.solPrice).toFixed(1)}
                {:else}
                    -
                {/if}
            </span>
        </div>

        <div class="pill-btn blue-btn">
            <span class="text"># .../{wsStore.tokenFeedCount}</span>
        </div>

        <!-- Setting and Trash Icons pushed to the right -->
        <button class="icon-btn" style="margin-left: auto;">
            <img src="/icons/settings.svg" alt="Settings" class="icon" />
        </button>

        <button class="icon-btn">
            <img src="/icons/trash.svg" alt="Trash" class="icon" />
        </button>
    </div>
</div>

<style>
    .top-panel {
        width: 100%;
        height: 15vh;
        background: linear-gradient(
            180deg,
            rgba(15, 17, 26, 0.8) 0%,
            transparent 100%
        );
        display: flex;
        align-items: center;
        padding: 0 24px;
        box-sizing: border-box;
        flex-shrink: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
        position: relative;
        z-index: 10;
    }

    .panel-content {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        backdrop-filter: blur(10px);
    }

    .pill-btn,
    .icon-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(145deg, #1e2029, #252835);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0 16px;
        height: 48px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: #fff;
        font-weight: 600;
        font-size: 15px;
        user-select: none;
        letter-spacing: 0.2px;
        box-shadow:
            0 4px 15px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .pill-btn:hover,
    .icon-btn:hover {
        transform: translateY(-2px);
        box-shadow:
            0 6px 20px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .pill-btn:active,
    .icon-btn:active {
        transform: translateY(0);
    }

    .icon-btn {
        padding: 0;
        width: 48px;
        color: #a0aec0;
    }

    .icon-btn:hover {
        background: linear-gradient(145deg, #272a35, #2f3342);
        border-color: rgba(255, 255, 255, 0.15);
    }

    .icon {
        width: 20px;
        height: 20px;
        transition: filter 0.3s ease;
    }

    .icon-btn:hover .icon {
        filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.4)) brightness(1.2);
    }

    .pill-btn .text {
        margin-left: 8px;
    }

    .pill-btn.blue-btn .text {
        margin-left: 0;
    }

    /* Connection Button Details */
    .ws-btn {
        min-width: 110px;
    }

    .ws-btn.disconnected {
        background: linear-gradient(
            145deg,
            rgba(236, 101, 114, 0.1),
            rgba(236, 101, 114, 0.02)
        );
        color: #eb6976;
        border-color: rgba(236, 101, 114, 0.2);
        box-shadow:
            0 4px 15px rgba(236, 101, 114, 0.1),
            inset 0 1px 0 rgba(236, 101, 114, 0.1);
    }

    .ws-btn.disconnected:hover {
        background: linear-gradient(
            145deg,
            rgba(236, 101, 114, 0.15),
            rgba(236, 101, 114, 0.05)
        );
        box-shadow:
            0 6px 20px rgba(236, 101, 114, 0.2),
            inset 0 1px 0 rgba(236, 101, 114, 0.15);
    }

    .ws-btn.disconnected:hover .icon {
        filter: drop-shadow(0 0 6px rgba(236, 101, 114, 0.6)) brightness(1.2);
    }

    .ws-btn.connected {
        background: linear-gradient(
            145deg,
            rgba(62, 223, 167, 0.1),
            rgba(62, 223, 167, 0.02)
        );
        color: #4ade80;
        border-color: rgba(74, 222, 128, 0.2);
        box-shadow:
            0 4px 15px rgba(62, 223, 167, 0.1),
            inset 0 1px 0 rgba(62, 223, 167, 0.1);
    }

    .ws-btn.connected:hover {
        background: linear-gradient(
            145deg,
            rgba(62, 223, 167, 0.15),
            rgba(62, 223, 167, 0.05)
        );
        box-shadow:
            0 6px 20px rgba(62, 223, 167, 0.2),
            inset 0 1px 0 rgba(62, 223, 167, 0.15);
    }

    .ws-btn.connected:hover .icon {
        filter: drop-shadow(0 0 6px rgba(62, 223, 167, 0.6)) brightness(1.2);
    }

    /* Second Button Purple (Decorative) */
    .purple-btn {
        background: linear-gradient(
            145deg,
            rgba(222, 147, 200, 0.1),
            rgba(222, 147, 200, 0.02)
        );
        color: #e696c2;
        border-color: rgba(222, 147, 200, 0.2);
        box-shadow:
            0 4px 15px rgba(222, 147, 200, 0.1),
            inset 0 1px 0 rgba(222, 147, 200, 0.1);
        cursor: default;
    }

    .purple-btn:hover {
        transform: translateY(-2px);
        background: linear-gradient(
            145deg,
            rgba(222, 147, 200, 0.15),
            rgba(222, 147, 200, 0.05)
        );
        box-shadow:
            0 6px 20px rgba(222, 147, 200, 0.2),
            inset 0 1px 0 rgba(222, 147, 200, 0.15);
    }

    .purple-btn:hover .icon {
        filter: drop-shadow(0 0 6px rgba(222, 147, 200, 0.6)) brightness(1.1);
    }

    /* Third Button Blueish (Decorative) */
    .blue-btn {
        background: linear-gradient(
            145deg,
            rgba(164, 173, 207, 0.1),
            rgba(164, 173, 207, 0.02)
        );
        color: #a7accc;
        border-color: rgba(164, 173, 207, 0.2);
        box-shadow:
            0 4px 15px rgba(164, 173, 207, 0.1),
            inset 0 1px 0 rgba(164, 173, 207, 0.1);
        cursor: default;
    }

    .blue-btn:hover {
        transform: translateY(-2px);
        background: linear-gradient(
            145deg,
            rgba(164, 173, 207, 0.15),
            rgba(164, 173, 207, 0.05)
        );
        box-shadow:
            0 6px 20px rgba(164, 173, 207, 0.2),
            inset 0 1px 0 rgba(164, 173, 207, 0.15);
    }

    /* Media queries for responsiveness */
    @media (max-width: 600px) {
        .top-panel {
            padding: 0 12px;
        }

        .panel-content {
            gap: 8px;
        }

        .pill-btn,
        .icon-btn {
            height: 40px;
            padding: 0 10px;
            font-size: 13px;
        }

        .icon-btn {
            width: 40px;
        }

        .icon {
            width: 18px;
            height: 18px;
        }

        .pill-btn .text {
            margin-left: 6px;
        }

        .ws-btn {
            min-width: 90px;
        }
    }
</style>
