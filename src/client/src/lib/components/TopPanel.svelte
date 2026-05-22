<script>
    import { onDestroy } from "svelte";
    import { wsStore } from "$lib/stores/websocket.svelte.js";
    import { filtersStore } from "$lib/stores/filters.svelte.js";
    import {
        DEFAULT_FILTERS,
        LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    } from "$lib/config/constants.js";

    let showSettings = false;
    let importJson = "";
    let actionMessage = "";
    let actionError = "";

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
    let localFeesMode = filtersStore.feesMode ?? DEFAULT_FILTERS.feesMode;
    let localMinLastTokenFees = Number(
        filtersStore.minLastTokenFees ?? DEFAULT_FILTERS.minLastTokenFees,
    );
    let localMinLastTokenAthMcap = Number(
        filtersStore.minLastTokenAthMcap ?? DEFAULT_FILTERS.minLastTokenAthMcap,
    );
    let localLastTokensRequiredCount = Number(
        filtersStore.lastTokensRequiredCount ??
            DEFAULT_FILTERS.lastTokensRequiredCount,
    );
    let localTerminal = filtersStore.terminal ?? DEFAULT_FILTERS.terminal;
    let localAutoOpenInNewTab = Boolean(
        filtersStore.autoOpenInNewTab ?? DEFAULT_FILTERS.autoOpenInNewTab,
    );
    let localAggressiveAutoOpen = Boolean(
        filtersStore.aggressiveAutoOpen ?? DEFAULT_FILTERS.aggressiveAutoOpen,
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
        localFeesMode = filtersStore.feesMode ?? DEFAULT_FILTERS.feesMode;
        localMinLastTokenFees = Number(
            filtersStore.minLastTokenFees ?? DEFAULT_FILTERS.minLastTokenFees,
        );
        localMinLastTokenAthMcap = Number(
            filtersStore.minLastTokenAthMcap ??
                DEFAULT_FILTERS.minLastTokenAthMcap,
        );
        localLastTokensRequiredCount = Number(
            filtersStore.lastTokensRequiredCount ??
                DEFAULT_FILTERS.lastTokensRequiredCount,
        );
        localTerminal = filtersStore.terminal ?? DEFAULT_FILTERS.terminal;
        localAutoOpenInNewTab = Boolean(
            filtersStore.autoOpenInNewTab ?? DEFAULT_FILTERS.autoOpenInNewTab,
        );
        localAggressiveAutoOpen = Boolean(
            filtersStore.aggressiveAutoOpen ??
                DEFAULT_FILTERS.aggressiveAutoOpen,
        );
        importJson = "";
        actionMessage = "";
        actionError = "";
        showSettings = true;
    };

    const closeSettings = () => {
        showSettings = false;
    };

    const saveSettings = () => {
        // ensure bounds
        if (localMinDev > localMaxDev) localMinDev = localMaxDev;
        if (localMaxDev < localMinDev) localMaxDev = localMinDev;

        filtersStore.updateFilters({
            minDevHoldsPercent: Number(localMinDev),
            maxDevHoldsPercent: Number(localMaxDev),
            minMigrationPercent: Number(localMinMigration),
            feesMode: localFeesMode,
            minLastTokenFees: Number(localMinLastTokenFees),
            minLastTokenAthMcap: Number(localMinLastTokenAthMcap),
            lastTokensRequiredCount: Number(localLastTokensRequiredCount),
            terminal: localTerminal,
            autoOpenInNewTab: localAutoOpenInNewTab,
            aggressiveAutoOpen: localAggressiveAutoOpen,
        });

        actionMessage = "Settings saved.";
        actionError = "";
        showSettings = false;
    };

    const exportSettings = async () => {
        try {
            const exportedJson = filtersStore.exportToJson();

            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(exportedJson);
            } else {
                const fallbackElement = document.createElement("textarea");
                fallbackElement.value = exportedJson;
                fallbackElement.setAttribute("readonly", "true");
                fallbackElement.style.position = "absolute";
                fallbackElement.style.left = "-9999px";
                document.body.appendChild(fallbackElement);
                fallbackElement.select();
                document.execCommand("copy");
                document.body.removeChild(fallbackElement);
            }

            actionMessage = "Settings copied to clipboard.";
            actionError = "";
        } catch (error) {
            actionError =
                error instanceof Error ? error.message : String(error);
            actionMessage = "";
        }
    };

    const importSettings = () => {
        actionMessage = "";
        actionError = "";

        try {
            filtersStore.importFromJson(importJson);

            localMinDev = Number(filtersStore.minDevHoldsPercent);
            localMaxDev = Number(filtersStore.maxDevHoldsPercent);
            localMinMigration = Number(filtersStore.minMigrationPercent);
            localFeesMode = filtersStore.feesMode;
            localMinLastTokenFees = Number(filtersStore.minLastTokenFees);
            localMinLastTokenAthMcap = Number(filtersStore.minLastTokenAthMcap);
            localLastTokensRequiredCount = Number(
                filtersStore.lastTokensRequiredCount,
            );
            localTerminal = filtersStore.terminal;
            localAutoOpenInNewTab = Boolean(filtersStore.autoOpenInNewTab);
            localAggressiveAutoOpen = Boolean(filtersStore.aggressiveAutoOpen);

            actionMessage = "Settings imported.";
            actionError = "";
        } catch (error) {
            actionError =
                error instanceof Error ? error.message : String(error);
            actionMessage = "";
        }
    };

    function onMinDevInput(e) {
        const v = Number(e.target.value);
        localMinDev = Math.min(v, localMaxDev);
    }

    function onMaxDevInput(e) {
        const v = Number(e.target.value);
        localMaxDev = Math.max(v, localMinDev);
    }

    function getDevHoldsRangeBackground() {
        const min = DEFAULT_FILTERS.minDevHoldsPercent;
        const max = 100;
        const minPercent = ((Number(localMinDev) - min) / (max - min)) * 100;
        const maxPercent = ((Number(localMaxDev) - min) / (max - min)) * 100;

        return `linear-gradient(to right,
            rgba(37, 99, 235, 0.18) 0%,
            rgba(37, 99, 235, 0.18) ${minPercent}%,
            rgba(59, 130, 246, 0.98) ${minPercent}%,
            rgba(59, 130, 246, 0.98) ${maxPercent}%,
            rgba(37, 99, 235, 0.24) ${maxPercent}%,
            rgba(37, 99, 235, 0.24) 100%)`;
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
                <div class="settings-header">
                    <div>
                        <h3>Settings</h3>
                        <p class="subtitle">
                            Saved locally on this device. Export copies JSON to
                            the clipboard, Import reads JSON from the field
                            below.
                        </p>
                    </div>
                </div>

                <div class="settings-scroll">
                    <div class="settings-grid">
                        <section class="settings-card settings-card-span-2">
                            <div class="card-head">
                                <h4>Auto open new token</h4>
                                <span class="card-meta">Selected terminal</span>
                            </div>

                            <button
                                type="button"
                                class="toggle-card {localAutoOpenInNewTab
                                    ? 'toggle-card-on'
                                    : 'toggle-card-off'}"
                                aria-pressed={localAutoOpenInNewTab}
                                onclick={() =>
                                    (localAutoOpenInNewTab =
                                        !localAutoOpenInNewTab)}
                            >
                                <span class="toggle-card-title">
                                    Auto open in new tab
                                </span>
                                <span class="toggle-card-status">
                                    {localAutoOpenInNewTab
                                        ? "Enabled"
                                        : "Disabled"}
                                </span>
                            </button>

                            <p class="instruction toggle-instruction">
                                When a token passes filters, open its link in
                                the terminal selected below. Last token cards
                                stay manual.
                            </p>

                            <button
                                type="button"
                                class="toggle-card {localAggressiveAutoOpen
                                    ? 'toggle-card-on'
                                    : 'toggle-card-off'}"
                                aria-pressed={localAggressiveAutoOpen}
                                onclick={() =>
                                    (localAggressiveAutoOpen =
                                        !localAggressiveAutoOpen)}
                            >
                                <span class="toggle-card-title">
                                    Aggressive mode
                                </span>
                                <span class="toggle-card-status">
                                    {localAggressiveAutoOpen
                                        ? "Enabled"
                                        : "Disabled"}
                                </span>
                            </button>

                            <p class="instruction toggle-instruction">
                                Open the browser first, then insert the card.
                                Use this when you want opening to win over
                                rendering latency.
                            </p>
                        </section>

                        <section class="settings-card settings-card-span-2">
                            <div class="card-head">
                                <h4>Dev holds range</h4>
                                <span class="card-meta"
                                    >{localMinDev}% — {localMaxDev}%</span
                                >
                            </div>
                            <div class="field field-tight">
                                <div class="range-wrap">
                                    <input
                                        id="minDevRange"
                                        class="range-input range-min"
                                        type="range"
                                        min={DEFAULT_FILTERS.minDevHoldsPercent}
                                        max="100"
                                        step="0.1"
                                        value={localMinDev}
                                        style={`background: ${getDevHoldsRangeBackground()};`}
                                        oninput={onMinDevInput}
                                    />
                                    <input
                                        id="maxDevRange"
                                        class="range-input range-max"
                                        type="range"
                                        min={DEFAULT_FILTERS.minDevHoldsPercent}
                                        max="100"
                                        step="0.1"
                                        value={localMaxDev}
                                        style={`background: ${getDevHoldsRangeBackground()};`}
                                        oninput={onMaxDevInput}
                                    />
                                </div>
                            </div>
                        </section>

                        <section class="settings-card">
                            <div class="card-head">
                                <h4>Trading filter</h4>
                                <span class="card-meta">Core thresholds</span>
                            </div>

                            <div class="field">
                                <label for="minMigrationInput"
                                    >Min migration %</label
                                >
                                <input
                                    id="minMigrationInput"
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="1"
                                    value={localMinMigration}
                                    oninput={(e) =>
                                        (localMinMigration = Number(
                                            e.target.value,
                                        ))}
                                />
                            </div>

                            <div class="field">
                                <label for="feesModeSelect"
                                    >Last Tokens Fees Mode</label
                                >
                                <select
                                    id="feesModeSelect"
                                    value={localFeesMode}
                                    oninput={(e) =>
                                        (localFeesMode = e.target.value)}
                                >
                                    <option value="avg">avg</option>
                                    <option value="total">total</option>
                                    <option value="fixed">fixed</option>
                                </select>
                            </div>

                            <div class="field">
                                <label for="minLastTokenFeesInput"
                                    >Min last token fees</label
                                >
                                <input
                                    id="minLastTokenFeesInput"
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    value={localMinLastTokenFees}
                                    oninput={(e) =>
                                        (localMinLastTokenFees = Number(
                                            e.target.value,
                                        ))}
                                />
                                <small class="helper-text">
                                    Tokens older than {LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS}
                                    days are ignored when their fees are below the
                                    threshold.
                                </small>
                            </div>

                            <div class="field">
                                <label for="minLastTokenAthMcapInput"
                                    >Min last token ATH mcap</label
                                >
                                <input
                                    id="minLastTokenAthMcapInput"
                                    type="number"
                                    min="0"
                                    step="1"
                                    value={localMinLastTokenAthMcap}
                                    oninput={(e) =>
                                        (localMinLastTokenAthMcap = Number(
                                            e.target.value,
                                        ))}
                                />
                            </div>

                            <div class="field">
                                <label for="lastTokensRequiredCountInput"
                                    >Required last tokens</label
                                >
                                <input
                                    id="lastTokensRequiredCountInput"
                                    type="number"
                                    min="0"
                                    max="3"
                                    step="1"
                                    value={localLastTokensRequiredCount}
                                    oninput={(e) =>
                                        (localLastTokensRequiredCount = Number(
                                            e.target.value,
                                        ))}
                                />
                                <small class="helper-text">
                                    Passes when at least this many of the last 3
                                    tokens have ATH mcap at or above the
                                    threshold. Set to 0 to disable the override.
                                </small>
                            </div>
                        </section>

                        <section class="settings-card">
                            <div class="card-head">
                                <h4>Terminal source</h4>
                                <span class="card-meta">Token provider</span>
                            </div>

                            <div class="field">
                                <label for="terminalSelect"
                                    >Token terminal</label
                                >
                                <select
                                    id="terminalSelect"
                                    value={localTerminal}
                                    oninput={(e) =>
                                        (localTerminal = e.target.value)}
                                >
                                    <option value="axiom">Axiom</option>
                                    <option value="gmgn">GMGN</option>
                                </select>
                            </div>
                        </section>

                        <section class="settings-card settings-card-span-2">
                            <div class="card-head">
                                <h4>Transfer settings</h4>
                                <span class="card-meta">Clipboard / paste</span>
                            </div>

                            <p class="instruction">
                                Export copies JSON to clipboard. Paste it below,
                                then press Import.
                            </p>

                            <div class="transfer-actions">
                                <button
                                    class="pill-btn secondary"
                                    onclick={exportSettings}
                                >
                                    Export
                                </button>
                                <button
                                    class="pill-btn secondary"
                                    onclick={importSettings}
                                >
                                    Import
                                </button>
                            </div>

                            <div class="field field-tight">
                                <label for="importJsonInput">Import JSON</label>
                                <textarea
                                    id="importJsonInput"
                                    bind:value={importJson}
                                    rows="8"
                                    spellcheck="false"
                                    placeholder="Paste the exported JSON here"
                                ></textarea>
                                <small class="helper-text">
                                    You can paste the new format with {`"schema"`}
                                    and {`"settings"`}, or the legacy flat JSON
                                    with filter fields.
                                </small>
                            </div>
                        </section>
                    </div>

                    {#if actionMessage}
                        <p class="feedback success">{actionMessage}</p>
                    {/if}

                    {#if actionError}
                        <p class="feedback error">{actionError}</p>
                    {/if}
                </div>

                <div class="settings-footer">
                    <button class="pill-btn ghost" onclick={closeSettings}
                        >Cancel</button
                    >
                    <button class="pill-btn primary" onclick={saveSettings}
                        >Save</button
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
        background: radial-gradient(
                circle at top,
                rgba(59, 130, 246, 0.18),
                transparent 42%
            ),
            rgba(4, 7, 14, 0.76);
        backdrop-filter: blur(10px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 50;
        padding: 12px;
        box-sizing: border-box;
    }

    .settings-modal {
        width: min(620px, 100%);
        max-height: min(84vh, 680px);
        background: linear-gradient(
                180deg,
                rgba(18, 22, 34, 0.98),
                rgba(13, 16, 26, 0.98)
            ),
            #0d1018;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        box-shadow:
            0 24px 80px rgba(0, 0, 0, 0.55),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .settings-header {
        padding: 14px 14px 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        background: linear-gradient(
            180deg,
            rgba(255, 255, 255, 0.03),
            transparent
        );
    }

    .settings-header h3 {
        margin: 0;
        font-size: 16px;
        letter-spacing: 0.2px;
    }

    .subtitle {
        margin: 6px 0 0;
        color: #94a3b8;
        font-size: 11px;
        line-height: 1.5;
        max-width: 56ch;
    }

    .settings-scroll {
        overflow-y: auto;
        overscroll-behavior: contain;
        padding: 12px 14px 14px;
    }

    .settings-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
    }

    .settings-card {
        background: linear-gradient(
                180deg,
                rgba(255, 255, 255, 0.03),
                rgba(255, 255, 255, 0.015)
            ),
            rgba(10, 13, 22, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 12px;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.03),
            0 10px 26px rgba(0, 0, 0, 0.18);
    }

    .settings-card-span-2 {
        grid-column: span 2;
    }

    .card-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 10px;
    }

    .card-head h4 {
        margin: 0;
        font-size: 12px;
        letter-spacing: 0.24px;
        text-transform: uppercase;
        color: #e5e7eb;
    }

    .card-meta {
        color: #64748b;
        font-size: 10px;
        white-space: nowrap;
    }

    .field {
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }

    .field:last-child {
        margin-bottom: 0;
    }

    .field-tight {
        margin-bottom: 0;
    }

    .field label {
        color: #dbe4f0;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.15px;
    }

    .field input,
    .field select {
        background: rgba(12, 15, 24, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.09);
        color: #e5eefb;
        border-radius: 10px;
        height: 38px;
        padding: 0 10px;
        outline: none;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }

    .field textarea {
        background: rgba(12, 15, 24, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.09);
        color: #e5eefb;
        border-radius: 10px;
        padding: 10px;
        outline: none;
        resize: vertical;
        font-family: inherit;
        line-height: 1.4;
        min-height: 128px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }

    .field input:focus,
    .field select:focus,
    .field textarea:focus {
        border-color: rgba(96, 165, 250, 0.42);
        box-shadow:
            0 0 0 3px rgba(96, 165, 250, 0.11),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }

    .instruction {
        margin: 0 0 10px;
        color: #b8c4da;
        font-size: 11px;
        line-height: 1.45;
    }

    .toggle-instruction {
        margin-top: 10px;
        margin-bottom: 0;
    }

    .toggle-card {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        border-radius: 12px;
        padding: 12px 14px;
        cursor: pointer;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(12, 15, 24, 0.92);
        color: #e5eefb;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        transition:
            transform 160ms ease,
            border-color 160ms ease,
            background 160ms ease,
            box-shadow 160ms ease;
    }

    .toggle-card:hover {
        transform: translateY(-1px);
    }

    .toggle-card-on {
        border-color: rgba(74, 222, 128, 0.38);
        background: linear-gradient(
                135deg,
                rgba(34, 197, 94, 0.18),
                rgba(12, 15, 24, 0.92)
            ),
            rgba(12, 15, 24, 0.92);
        box-shadow:
            0 0 0 1px rgba(74, 222, 128, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }

    .toggle-card-off {
        border-color: rgba(255, 255, 255, 0.08);
        background: rgba(12, 15, 24, 0.92);
    }

    .toggle-card-title {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.15px;
    }

    .toggle-card-status {
        font-size: 11px;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        white-space: nowrap;
    }

    .toggle-card-on .toggle-card-status {
        color: #86efac;
    }

    .helper-text {
        color: #91a0b7;
        font-size: 10px;
        line-height: 1.35;
    }

    .range-wrap {
        position: relative;
        width: 100%;
        max-width: 100%;
        min-width: 0;
        height: 30px;
        margin-top: 4px;
        overflow: visible;
    }

    .range-wrap input[type="range"] {
        position: absolute;
        left: 0;
        right: 0;
        width: 100%;
        max-width: 100%;
        min-width: 0;
        height: 30px;
        margin: 0;
        padding: 0;
        appearance: none;
        -webkit-appearance: none;
        background: transparent;
        pointer-events: auto;
        cursor: pointer;
        outline: none;
    }

    .range-wrap input[type="range"]::-webkit-slider-runnable-track {
        height: 8px;
        border-radius: 999px;
        background: transparent;
    }

    .range-wrap input[type="range"]::-moz-range-track {
        height: 8px;
        border-radius: 999px;
        background: transparent;
    }

    .range-wrap input[type="range"]::-webkit-slider-thumb {
        appearance: none;
        -webkit-appearance: none;
        width: 19px;
        height: 19px;
        border-radius: 50%;
        border: 2px solid rgba(239, 246, 255, 0.96);
        background: linear-gradient(180deg, #93c5fd, #2563eb);
        box-shadow:
            0 0 0 4px rgba(59, 130, 246, 0.16),
            0 8px 18px rgba(0, 0, 0, 0.35);
        margin-top: -5px;
    }

    .range-wrap input[type="range"]::-moz-range-thumb {
        width: 19px;
        height: 19px;
        border-radius: 50%;
        border: 2px solid rgba(239, 246, 255, 0.96);
        background: linear-gradient(180deg, #93c5fd, #2563eb);
        box-shadow:
            0 0 0 4px rgba(59, 130, 246, 0.16),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-wrap input[type="range"]:focus-visible::-webkit-slider-thumb {
        box-shadow:
            0 0 0 5px rgba(96, 165, 250, 0.2),
            0 0 0 9px rgba(37, 99, 235, 0.12),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-wrap input[type="range"]:focus-visible::-moz-range-thumb {
        box-shadow:
            0 0 0 5px rgba(96, 165, 250, 0.2),
            0 0 0 9px rgba(37, 99, 235, 0.12),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-input.range-min {
        z-index: 2;
    }

    .range-input.range-max {
        z-index: 1;
    }

    .transfer-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }

    .feedback {
        margin: 10px 0 0;
        font-size: 11px;
        line-height: 1.4;
    }

    .feedback.success {
        color: #93c5fd;
    }

    .feedback.error {
        color: #fca5a5;
    }

    .settings-footer {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding: 12px 14px 14px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        background: linear-gradient(
            180deg,
            transparent,
            rgba(255, 255, 255, 0.025)
        );
    }

    .pill-btn {
        transition:
            background-color 160ms ease,
            border-color 160ms ease,
            box-shadow 160ms ease,
            color 160ms ease,
            transform 160ms ease;
    }

    .pill-btn:hover,
    .icon-btn:hover {
        transform: translateY(-1px);
    }

    .pill-btn.secondary {
        min-width: 80px;
        background: rgba(22, 26, 38, 0.92);
        color: #dbe4f0;
        border-color: rgba(255, 255, 255, 0.08);
    }

    .pill-btn.primary {
        min-width: 94px;
        background: linear-gradient(135deg, #2f7cf6, #2563eb);
        border-color: rgba(96, 165, 250, 0.3);
        color: #f8fbff;
    }

    .pill-btn.ghost {
        min-width: 84px;
        background: rgba(22, 26, 38, 0.72);
        color: #cbd5e1;
        border-color: rgba(255, 255, 255, 0.08);
    }

    .settings-scroll::-webkit-scrollbar {
        width: 10px;
    }

    .settings-scroll::-webkit-scrollbar-track {
        background: transparent;
    }

    .settings-scroll::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.25);
        border-radius: 999px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }

    .settings-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(148, 163, 184, 0.42);
        border: 2px solid transparent;
        background-clip: padding-box;
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

        .settings-overlay {
            padding: 10px;
        }

        .settings-modal {
            max-height: calc(100vh - 20px);
            border-radius: 16px;
        }

        .settings-header,
        .settings-scroll,
        .settings-footer {
            padding-left: 12px;
            padding-right: 12px;
        }

        .settings-grid {
            grid-template-columns: 1fr;
            gap: 8px;
        }

        .settings-card-span-2 {
            grid-column: auto;
        }

        .settings-footer {
            justify-content: stretch;
            flex-direction: column-reverse;
        }

        .settings-footer .pill-btn {
            width: 100%;
        }

        .transfer-actions {
            flex-direction: column;
        }

        .transfer-actions .pill-btn {
            width: 100%;
        }

        .card-head {
            align-items: flex-start;
            flex-direction: column;
        }
    }
</style>
