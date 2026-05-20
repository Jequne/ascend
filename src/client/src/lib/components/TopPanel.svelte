<script>
    import { onDestroy } from "svelte";
    import { getStoredKey } from "$lib/api/auth.js";

    let ws = null;
    let isConnected = $state(false);
    let isConnecting = $state(false);
    let ping = $state(0);
    let shouldReconnect = $state(false);
    let reconnectTimeout = null;

    const WS_URL = "ws://localhost:8000/ws";

    function connect() {
        if (ws) return;

        isConnecting = true;
        shouldReconnect = true;
        const key = getStoredKey();

        try {
            ws = new WebSocket(`${WS_URL}?api_key=${key}`);

            ws.onopen = () => {
                isConnected = true;
                isConnecting = false;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "ping" && data.payload?.timestamp) {
                        const serverTime = new Date(
                            data.payload.timestamp,
                        ).getTime();
                        const clientTime = Date.now();
                        // Вычисляем задержку
                        ping = Math.abs(clientTime - serverTime);
                    }
                } catch (e) {}
            };

            ws.onclose = () => {
                isConnected = false;
                isConnecting = false;
                ws = null;
                ping = 0;

                if (shouldReconnect) {
                    reconnectTimeout = setTimeout(() => {
                        connect();
                    }, 3000);
                }
            };

            ws.onerror = (err) => {
                console.error("WS error:", err);
            };
        } catch (e) {
            console.error("Failed to create WS:", e);
            isConnecting = false;
        }
    }

    function disconnect() {
        shouldReconnect = false;
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
        if (ws) {
            ws.close();
            ws = null;
        }
        isConnected = false;
        isConnecting = false;
        ping = 0;
    }

    function toggleConnection() {
        if (isConnected || isConnecting || shouldReconnect) {
            disconnect();
        } else {
            connect();
        }
    }

    onDestroy(() => {
        disconnect();
    });
</script>

<div class="top-panel">
    <div class="panel-content">
        <!-- Connect / Ping Button -->
        <button
            type="button"
            class="pill-btn ws-btn {isConnected ? 'connected' : 'disconnected'}"
            onclick={toggleConnection}
        >
            <svg viewBox="0 0 24 24" fill="none" class="icon">
                <path
                    d="M4 19.5A1.5 1.5 0 0 1 2.5 18A1.5 1.5 0 0 1 4 16.5A1.5 1.5 0 0 1 5.5 18A1.5 1.5 0 0 1 4 19.5ZM4 12C7.31 12 10 14.69 10 18H8C8 15.79 6.21 14 4 14V12ZM4 6C10.63 6 16 11.37 16 18H14C14 12.48 9.52 8 4 8V6Z"
                    fill="currentColor"
                />
            </svg>
            <span class="text">
                {#if isConnected}
                    {ping}ms
                {:else if isConnecting}
                    ...
                {:else}
                    Offline
                {/if}
            </span>
        </button>

        <!-- Placeholder Buttons for Design -->
        <div class="pill-btn purple-btn">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                class="icon"
                stroke="currentColor"
                stroke-width="2"
            >
                <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"
                ></polygon>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
            <span class="text">$86.5</span>
        </div>

        <div class="pill-btn blue-btn">
            <span class="text"># 1</span>
        </div>

        <!-- Setting and Trash Icons pushed to the right -->
        <button class="icon-btn" style="margin-left: auto;">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="icon"
            >
                <line x1="4" y1="21" x2="4" y2="14"></line>
                <line x1="4" y1="10" x2="4" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12" y2="3"></line>
                <line x1="20" y1="21" x2="20" y2="16"></line>
                <line x1="20" y1="12" x2="20" y2="3"></line>
                <line x1="1" y1="14" x2="7" y2="14"></line>
                <line x1="9" y1="8" x2="15" y2="8"></line>
                <line x1="17" y1="16" x2="23" y2="16"></line>
            </svg>
        </button>

        <button class="icon-btn">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="icon"
            >
                <polyline points="3 6 5 6 21 6"></polyline>
                <path
                    d="M19 6L17.5 20.5A2 2 0 0115.5 22h-7A2 2 0 016.5 20.5L5 6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"
                ></path>
                <line x1="10" y1="11" x2="10" y2="17"></line>
                <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
        </button>
    </div>
</div>

<style>
    .top-panel {
        width: 100%;
        height: 15vh;
        background-color: transparent;
        display: flex;
        align-items: center;
        padding: 0 24px;
        box-sizing: border-box;
        flex-shrink: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
    }

    .panel-content {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
    }

    .pill-btn,
    .icon-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #1e2029;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px; /* Smooth rounded corners */
        padding: 0 16px;
        height: 48px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        color: #fff;
        font-weight: 600;
        font-size: 15px;
        user-select: none;
        letter-spacing: 0.2px;
    }

    .icon-btn {
        padding: 0;
        width: 48px;
        color: #a0aec0;
    }

    .icon-btn:hover {
        background-color: #272a35;
        color: #e2e8f0;
        border-color: rgba(255, 255, 255, 0.1);
    }

    .icon {
        width: 20px;
        height: 20px;
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
        background-color: rgba(236, 101, 114, 0.05);
        color: #eb6976;
        border-color: rgba(236, 101, 114, 0.15);
    }
    .ws-btn.disconnected:hover {
        background-color: rgba(236, 101, 114, 0.1);
    }

    .ws-btn.connected {
        background-color: rgba(62, 223, 167, 0.08);
        color: #4ade80;
        border-color: rgba(74, 222, 128, 0.2);
    }

    .ws-btn.connected:hover {
        background-color: rgba(62, 223, 167, 0.12);
        box-shadow: 0 0 15px rgba(62, 223, 167, 0.15);
    }

    /* Second Button Purple (Decorative) */
    .purple-btn {
        background-color: rgba(222, 147, 200, 0.05);
        color: #e696c2;
        border-color: rgba(222, 147, 200, 0.15);
        cursor: default;
    }

    /* Third Button Blueish (Decorative) */
    .blue-btn {
        background-color: rgba(164, 173, 207, 0.05);
        color: #a7accc;
        border-color: rgba(164, 173, 207, 0.15);
        cursor: default;
    }
</style>
