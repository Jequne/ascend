<script>
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import AuthBox from "$lib/components/AuthBox.svelte";
  import TopPanel from "$lib/components/TopPanel.svelte";
  import TokenFeedList from "$lib/components/TokenFeedList.svelte";
  import { authStore } from "$lib/stores/auth.svelte.js";
  import { filtersStore } from "$lib/stores/filters.svelte.js";

  onMount(() => {
    filtersStore.init();
    authStore.init();
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
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      Helvetica, Arial, sans-serif;
    background-color: #171821;
    color: #e2e8f0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
  }

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
