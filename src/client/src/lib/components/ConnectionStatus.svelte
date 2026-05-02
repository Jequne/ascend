<script>
    import { connectWs, disconnectWs, isWsConnected } from "$lib/api/ws";
    import { onMount } from "svelte";

    /**
     * @typedef {Object} Props
     * @property {boolean} connected
     */

    /** @type {Props} */
    let { connected = $bindable(false) } = $props();

    function handleToggle() {
        if (connected) {
            disconnectWs();
        } else {
            connectWs({
                onOpen: () => {
                    connected = true;
                },
                onClose: () => {
                    connected = false;
                },
                onError: () => {
                    connected = false;
                },
            });
        }
    }

    onMount(() => {
        // Update local state if already connected
        connected = isWsConnected();
    });
</script>

<button
    class="connection-status {connected ? 'connected' : 'disconnected'}"
    onclick={handleToggle}
    title={connected ? "Disconnect" : "Connect"}
>
    <img
        src={connected ? "/icons/wifi.svg" : "/icons/wifi-off.svg"}
        alt="Connection status"
        class="icon"
    />
</button>

<style>
    .connection-status {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
        padding: 8px;
        background: transparent;
    }

    .disconnected {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .disconnected .icon {
        filter: invert(36%) sepia(85%) saturate(1209%) hue-rotate(323deg)
            brightness(97%) contrast(93%); /* #ef4444 */
    }

    .disconnected:hover {
        background-color: rgba(239, 68, 68, 0.2);
        border-color: rgba(239, 68, 68, 0.5);
    }

    .connected {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .connected .icon {
        filter: invert(61%) sepia(88%) saturate(398%) hue-rotate(93deg)
            brightness(96%) contrast(88%); /* #22c55e */
    }

    .connected:hover {
        background-color: rgba(34, 197, 94, 0.2);
        border-color: rgba(34, 197, 94, 0.5);
    }

    .icon {
        width: 100%;
        height: 100%;
    }
</style>
