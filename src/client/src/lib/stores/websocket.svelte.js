import { getStoredKey } from "$lib/api/auth.js";
import { WS_BASE_URL } from "$lib/config/constants.js";

function createWebSocketStore() {
    let ws = null;
    let isConnected = $state(false);
    let isConnecting = $state(false);
    let ping = $state(0);
    let solPrice = $state(null);
    let tokenFeedCount = $state(0);
    let shouldReconnect = false;
    let reconnectTimeout = null;

    function connect() {
        if (ws) return;

        isConnecting = true;
        shouldReconnect = true;
        const key = getStoredKey();

        try {
            ws = new WebSocket(`${WS_BASE_URL}?api_key=${key}`);

            ws.onopen = () => {
                isConnected = true;
                isConnecting = false;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "ping" && data.payload?.timestamp) {
                        const serverTime = new Date(data.payload.timestamp).getTime();
                        const clientTime = Date.now();
                        ping = Math.abs(clientTime - serverTime);
                    } else if (data.type === "sol_price") {
                        solPrice = data.payload;
                    } else if (data.type === "token_feed") {
                        tokenFeedCount++;
                    }
                } catch (e) { }
            };

            ws.onclose = () => {
                isConnected = false;
                isConnecting = false;
                ws = null;
                ping = 0;
                solPrice = null;
                tokenFeedCount = 0;

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
        tokenFeedCount = 0;
    }

    function toggleConnection() {
        if (isConnected || isConnecting || shouldReconnect) {
            disconnect();
        } else {
            connect();
        }
    }

    return {
        get isConnected() { return isConnected; },
        get isConnecting() { return isConnecting; },
        get ping() { return ping; },
        get solPrice() { return solPrice; },
        get tokenFeedCount() { return tokenFeedCount; },
        connect,
        disconnect,
        toggleConnection
    };
}

export const wsStore = createWebSocketStore();