<script>
    import { getApiKey, clearApiKey } from "$lib/auth/storage.js";
    import ConnectionStatus from "./ConnectionStatus.svelte";
    import SettingsMenu from "./SettingsMenu.svelte";
    import { feedState } from "$lib/core/tokenFeed/store.svelte.js";

    let apiKey = $state("");
    let isConnected = $state(false);
    let isSettingsOpen = $state(false);

    function loadApiKey() {
        apiKey = getApiKey() || "";
    }

    if (typeof window !== "undefined") {
        loadApiKey();
    }

    function handleLogout() {
        clearApiKey();
        window.location.reload();
    }

    function clearFead() {}
</script>

<div class="main-container">
    <div class="info-block">
        <div class="left-group">
            <ConnectionStatus
                connected={isConnected}
                onAuthError={handleLogout}
            />
            <div class="passed-filters-counter">
                <img
                    src="/icons/filters.svg"
                    alt="Filters"
                    class="icon blue-icon"
                />
                <!-- Формат: отфильтровано / всего получено -->
                <span
                    >{feedState.filteredTokens.length} / {feedState.rawTokens
                        .length}</span
                >
            </div>
        </div>

        <div class="right-group">
            <button
                class="settings-button"
                title="Settings"
                onclick={() => (isSettingsOpen = true)}
            >
                <img src="/icons/settings.svg" alt="Settings" class="icon" />
            </button>
            <button
                class="clear-feed-button"
                title="Clear Feed"
                onclick={clearFead}
            >
                <img src="/icons/trash.svg" alt="Clear Feed" class="icon" />
            </button>
        </div>
    </div>

    <div class="feed-block">
        <!-- Feed tokens will be here -->
    </div>
</div>

{#if isSettingsOpen}
    <SettingsMenu onClose={() => (isSettingsOpen = false)} />
{/if}

<style>
    .main-container {
        width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: #0f1117;
        color: #e5e7eb;
        overflow: hidden;
    }

    .info-block {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 20px;
        background-color: #161922;
        border-bottom: 1px solid #232733;
        flex-wrap: wrap;
        gap: 12px;
    }

    .left-group,
    .right-group {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }

    .passed-filters-counter {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0 16px;
        height: 40px;
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 8px;
        color: #60a5fa;
        font-size: 14px;
        font-weight: 500;
        white-space: nowrap;
    }

    .settings-button,
    .clear-feed-button {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #1e2330;
        border: 1px solid #2e3547;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
    }

    .settings-button .icon,
    .clear-feed-button .icon {
        filter: invert(74%) sepia(8%) saturate(1001%) hue-rotate(182deg)
            brightness(88%) contrast(85%); /* #9ca3af */
    }

    .settings-button:hover,
    .clear-feed-button:hover {
        background-color: #2e3547;
    }

    .settings-button:hover .icon,
    .clear-feed-button:hover .icon {
        filter: invert(100%);
    }

    .clear-feed-button:hover {
        border-color: rgba(239, 68, 68, 0.4);
    }

    .clear-feed-button:hover .icon {
        filter: invert(36%) sepia(85%) saturate(1209%) hue-rotate(323deg)
            brightness(97%) contrast(93%); /* #ef4444 */
    }

    .icon {
        width: 20px;
        height: 20px;
    }

    .blue-icon {
        filter: invert(61%) sepia(93%) saturate(1178%) hue-rotate(188deg)
            brightness(101%) contrast(97%); /* #60a5fa */
    }

    .feed-block {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        min-height: 200px;
    }

    @media (max-width: 480px) {
        .info-block {
            padding: 8px 12px;
        }

        .passed-filters-counter {
            padding: 0 10px;
            font-size: 12px;
        }
    }
</style>
