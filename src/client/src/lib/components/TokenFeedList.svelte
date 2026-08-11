<script lang="ts">
    import TokenCard from "./TokenCard.svelte";
    import { wsStore } from "$lib/stores/websocket.svelte";
</script>

<div class="feed-container">
    {#if wsStore.tokenFeeds && wsStore.tokenFeeds.length > 0}
        {#each wsStore.tokenFeeds as feed (feed.clientKey)}
            <TokenCard {feed} />
        {/each}
    {:else if !wsStore.isConnected}
        <div class="empty-state">
            <p>Connecting to feed...</p>
        </div>
    {:else}
        <div class="empty-state">
            <p>Waiting for tokens...</p>
        </div>
    {/if}
</div>

<style>
    .feed-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
        padding: 8px 12px;
        overflow-y: auto;
        flex-grow: 1;
        box-sizing: border-box;
    }

    .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        color: #64748b;
        font-size: 1rem;
        flex-grow: 1;
    }
</style>
