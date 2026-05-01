<script>
    import AuthMenu from "$lib/components/AuthMenu.svelte";
    import MainInterface from "$lib/components/MainInterface.svelte";
    import { getApiKey } from "$lib/auth/storage.js";

    let isAuthenticated = $state(false);

    if (typeof window !== "undefined") {
        isAuthenticated = !!getApiKey();
    }
</script>

{#if isAuthenticated}
    <MainInterface />
{:else}
    <AuthMenu />
{/if}
