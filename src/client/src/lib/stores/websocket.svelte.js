import { getStoredKey } from "$lib/api/auth.js";
import { WS_BASE_URL } from "$lib/config/constants.js";

class WebSocketStore {
    ws = null;
    isConnected = $state(false);
    isConnecting = $state(false);
    ping = $state(0);
    solPrice = $state(null);
    tokenFeedCount = $state(0);
    tokenFeeds = $state([]);
    shouldReconnect = false;
    reconnectTimeout = null;

    connect = () => {
        if (this.ws) return;

        this.isConnecting = true;
        this.shouldReconnect = true;
        const key = getStoredKey();

        try {
            this.ws = new WebSocket(`${WS_BASE_URL}?api_key=${key}`);

            this.ws.onopen = () => {
                this.isConnected = true;
                this.isConnecting = false;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "ping" && data.payload?.timestamp) {
                        const serverTime = new Date(data.payload.timestamp).getTime();
                        const clientTime = Date.now();
                        this.ping = Math.abs(clientTime - serverTime);
                    } else if (data.type === "sol_price") {
                        this.solPrice = data.payload;
                    } else if (data.type === "token_feed") {
                        this.tokenFeedCount++;
                        // By using unshift or reassign, state will trigger update
                        this.tokenFeeds = [data.payload, ...this.tokenFeeds];
                    }
                } catch (e) { }
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                this.isConnecting = false;
                this.ws = null;
                this.ping = 0;
                this.solPrice = null;
                this.tokenFeedCount = 0;

                if (this.shouldReconnect) {
                    this.reconnectTimeout = setTimeout(() => {
                        this.connect();
                    }, 3000);
                }
            };

            this.ws.onerror = (err) => {
                console.error("WS error:", err);
            };
        } catch (e) {
            console.error("Failed to create WS:", e);
            this.isConnecting = false;
        }
    }

    disconnect = () => {
        this.shouldReconnect = false;
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.isConnecting = false;
        this.ping = 0;
        this.tokenFeedCount = 0;
    }

    toggleConnection = () => {
        if (this.isConnected || this.isConnecting || this.shouldReconnect) {
            this.disconnect();
        } else {
            this.connect();
        }
    }
}

export const wsStore = new WebSocketStore();