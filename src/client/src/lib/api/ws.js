import { getApiKey } from '../auth/storage';
import { API_CONFIG } from '../config/api';

/**
 * @typedef {Object} WsOptions
 * @property {function} [onMessage] - Callback for incoming messages
 * @property {function} [onOpen] - Callback when connection is established
 * @property {function} [onClose] - Callback when connection is closed
 * @property {function} [onError] - Callback when an error occurs
 */

let socket = null;

/**
 * Connects to the WebSocket endpoint
 * @param {WsOptions} options 
 */
export function connectWs(options = {}) {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        console.warn('WebSocket is already connecting or open');
        return socket;
    }

    const apiKey = getApiKey();
    if (!apiKey) {
        console.error('No API key found for WebSocket connection');
        options.onError?.(new Error('Unauthorized'));
        return null;
    }

    // Convert http/https to ws/wss
    const wsUrl = API_CONFIG.baseUrl.replace(/^http/, 'ws') + '/ws';

    // Server expects the key in query parameter "api_key" (not "key")
    // as seen in ws_auth.py: websocket.query_params.get("api_key")
    const urlWithKey = `${wsUrl}?api_key=${encodeURIComponent(apiKey)}`;

    socket = new WebSocket(urlWithKey);

    socket.onopen = (event) => {
        console.log('WebSocket connected');
        options.onOpen?.(event);

        // Keep-alive: Send ping every 20 seconds to prevent timeout
        const pingInterval = setInterval(() => {
            if (isWsConnected()) {
                socket.send('ping');
            } else {
                clearInterval(pingInterval);
            }
        }, 20000);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            options.onMessage?.(data);
        } catch (e) {
            // Handle plain text messages (like "pong")
            options.onMessage?.(event.data);
        }
    };

    socket.onclose = (event) => {
        console.log('WebSocket disconnected', event.reason);
        socket = null;
        options.onClose?.(event);
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        options.onError?.(error);
    };

    return socket;
}

/**
 * Disconnects the WebSocket
 */
export function disconnectWs() {
    if (socket) {
        socket.close();
        socket = null;
    }
}

/**
 * Checks if the WebSocket is connected
 * @returns {boolean}
 */
export function isWsConnected() {
    return socket !== null && socket.readyState === WebSocket.OPEN;
}

/**
 * Sends a message via WebSocket
 * @param {any} data 
 */
export function sendWsMessage(data) {
    if (isWsConnected()) {
        const message = typeof data === 'string' ? data : JSON.stringify(data);
        socket.send(message);
    } else {
        console.warn('Cannot send message: WebSocket is not connected');
    }
}
