<script lang="ts">
    import AuthBox from "$lib/components/AuthBox.svelte";
    import TokenFeedList from "$lib/components/TokenFeedList.svelte";
    import TopPanel from "$lib/components/TopPanel.svelte";
    import { authStore } from "$lib/stores/auth.svelte";
    import { filtersStore } from "$lib/stores/filters.svelte";
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";

    onMount(() => {
        filtersStore.init();
        void authStore.init();
    });
</script>

<main class="container">
    {#if authStore.isLoading}
        <div class="loading" in:fade>Verifying license...</div>
    {:else if authStore.isAuthenticated}
        <div class="dashboard" in:fade>
            <TopPanel />
            <TokenFeedList />
        </div>
    {:else}
        <div class="auth-wrapper" in:fade>
            <AuthBox />
        </div>
    {/if}
</main>

<style>
    .container {
        width: 100%;
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .auth-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
    }

    .loading {
        color: #a0aec0;
    }

    .dashboard {
        width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
</style>
