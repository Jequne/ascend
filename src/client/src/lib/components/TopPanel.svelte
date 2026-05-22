<script>
    import { onDestroy } from "svelte";
    import { wsStore } from "$lib/stores/websocket.svelte.js";
    import { filtersStore } from "$lib/stores/filters.svelte.js";
    import { DEFAULT_FILTERS } from "$lib/config/constants.js";

    let showSettings = false;

    // Local editable copies (so user can cancel)
    let localMinDev = Number(
        filtersStore.minDevHoldsPercent ?? DEFAULT_FILTERS.minDevHoldsPercent,
    );
    let localMaxDev = Number(
        filtersStore.maxDevHoldsPercent ?? DEFAULT_FILTERS.maxDevHoldsPercent,
    );
    let localMinMigration = Number(
        filtersStore.minMigrationPercent ?? DEFAULT_FILTERS.minMigrationPercent,
    );

    const openSettings = () => {
        // sync from store when opening
        localMinDev = Number(
            filtersStore.minDevHoldsPercent ??
                DEFAULT_FILTERS.minDevHoldsPercent,
        );
        localMaxDev = Number(
            filtersStore.maxDevHoldsPercent ??
                DEFAULT_FILTERS.maxDevHoldsPercent,
        );
        localMinMigration = Number(
            filtersStore.minMigrationPercent ??
                DEFAULT_FILTERS.minMigrationPercent,
        );
        showSettings = true;
    };

    const closeSettings = () => {
        showSettings = false;
    };

    const saveSettings = () => {
        // ensure bounds
        if (localMinDev > localMaxDev) localMinDev = localMaxDev;
        if (localMaxDev < localMinDev) localMaxDev = localMinDev;

        filtersStore.minDevHoldsPercent = Number(localMinDev);
        filtersStore.maxDevHoldsPercent = Number(localMaxDev);
        filtersStore.minMigrationPercent = Number(localMinMigration);

        showSettings = false;
    };

    function onMinDevInput(e) {
        const v = Number(e.target.value);
        localMinDev = Math.min(v, localMaxDev);
    }

    function onMaxDevInput(e) {
        const v = Number(e.target.value);
        localMaxDev = Math.max(v, localMinDev);
    }

    function overlayKeydown(e) {
        if (e.key === "Escape") closeSettings();
    }
    function modalKeydown(e) {
        e.stopPropagation();
    }

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
            <span class="text"
                ># {wsStore.tokenFeedCount}/{wsStore.tokenFeedTotalCount}</span
            >
        </div>

        <!-- Setting and Trash Icons pushed to the right -->
        <button
            class="icon-btn"
            style="margin-left: auto;"
            onclick={openSettings}
        >
            <img src="/icons/settings.svg" alt="Settings" class="icon" />
        </button>

        <button class="icon-btn" onclick={wsStore.clearTokens}>
            <img src="/icons/trash.svg" alt="Trash" class="icon" />
        </button>
    </div>

    {#if showSettings}
        <div
            class="settings-overlay"
            onclick={closeSettings}
            onkeydown={overlayKeydown}
            tabindex="0"
            role="button"
        >
            <div
                class="settings-modal"
                onclick={(e) => e.stopPropagation()}
                onkeydown={modalKeydown}
                role="dialog"
                aria-modal="true"
                tabindex="0"
            >
                <h3>Filters Settings</h3>

                <div class="field">
                    <label for="minDevRange"
                        >Dev Holds Range: {localMinDev}% — {localMaxDev}%</label
                    >
                    <div class="range-wrap">
                        <input
                            id="minDevRange"
                            type="range"
                            min={DEFAULT_FILTERS.minDevHoldsPercent}
                            max="100"
                            step="0.1"
                            value={localMinDev}
                            oninput={onMinDevInput}
                        />
                        <input
                            id="maxDevRange"
                            type="range"
                            min={DEFAULT_FILTERS.minDevHoldsPercent}
                            max="100"
                            step="0.1"
                            value={localMaxDev}
                            oninput={onMaxDevInput}
                        />
                    </div>
                </div>

                <div class="field">
                    <label for="minMigrationInput">Min Migration %</label>
                    <input
                        id="minMigrationInput"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={localMinMigration}
                        oninput={(e) =>
                            (localMinMigration = Number(e.target.value))}
                    />
                </div>

                <div class="actions">
                    <button class="pill-btn" onclick={saveSettings}>Save</button
                    >
                    <button class="pill-btn" onclick={closeSettings}
                        >Cancel</button
                    >
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .top-panel {
        width: 100%;
        height: auto;
        min-height: 10vh;
        background: linear-gradient(
            180deg,
            rgba(15, 17, 26, 0.8) 0%,
            transparent 100%
        );
        display: flex;
        align-items: center;
        padding: 12px 16px;
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
        gap: 8px;
        width: 100%;
        backdrop-filter: blur(10px);
        flex-wrap: wrap;
    }

    .pill-btn,
    .icon-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(145deg, #1e2029, #252835);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0 12px;
        height: 40px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: #fff;
        font-weight: 600;
        font-size: 13px;
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
        width: 40px;
        color: #a0aec0;
    }

    .icon-btn:hover {
        background: linear-gradient(145deg, #272a35, #2f3342);
        border-color: rgba(255, 255, 255, 0.15);
    }

    .icon {
        width: 16px;
        height: 16px;
        transition: filter 0.3s ease;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
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

    /* Settings modal */
    .settings-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 50;
    }

    .settings-modal {
        background: #0f111a;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 16px;
        border-radius: 12px;
        width: 360px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
    }

    .settings-modal h3 {
        margin: 0 0 12px 0;
        font-size: 16px;
    }

    .field {
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .range-wrap {
        position: relative;
        height: 28px;
    }

    .range-wrap input[type="range"] {
        position: absolute;
        left: 0;
        right: 0;
        width: 100%;
        background: transparent;
        pointer-events: auto;
    }

    .actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
    }

    /* Media queries for responsiveness */
    @media (max-width: 600px) {
        .top-panel {
            padding: 8px 12px;
        }

        .panel-content {
            gap: 6px;
        }

        .pill-btn,
        .icon-btn {
            height: 36px;
            padding: 0 8px;
            font-size: 12px;
        }

        .icon-btn {
            width: 36px;
        }

        .icon {
            width: 14px;
            height: 14px;
        }

        .pill-btn .text {
            margin-left: 4px;
        }

        .ws-btn {
            min-width: 80px;
        }
    }
</style>
