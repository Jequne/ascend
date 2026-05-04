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

    // Using sub-protocols to pass the API key since standard WebSocket browser API 
    // doesn't support custom headers. The server can extract this from 'Sec-WebSocket-Protocol'.
    // Alternatively, if your server is specifically configured to handle it via query params 
    // or you are using a proxy, we use query param 'api_key' because it's most compatible.
    // However, per your request to move away from params, the most common way for 
    // native WebSockets in browsers to "send headers" is using the protocols argument 
    // or continuing with query params if headers are strictly required by the server logic.

    // If you want to use X-API-Key, standard browser WebSocket API DOES NOT SUPPORT custom headers.
    // The most reliable way for browser-based WS is still query params.
    // If the server now expects X-API-Key, let's keep it in query for now as a fallback 
    // or use the protocol field if the server is ready for it.

    // I will keep the URL as is but update the comment/structure if you have a proxy 
    // that transforms this, but standard WebSockets in JS can't send headers.
    const urlWithKey = `${wsUrl}?api_key=${encodeURIComponent(apiKey)}`;

    socket = new WebSocket(urlWithKey);

    socket.onopen = (event) => {
        console.log('WebSocket connected');
        options.onOpen?.(event);
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
        console.log('WebSocket disconnected', event.code, event.reason);
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
