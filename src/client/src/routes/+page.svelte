<script>
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import AuthBox from "$lib/components/AuthBox.svelte";
  import TopPanel from "$lib/components/TopPanel.svelte";
  import { validateKey, getStoredKey } from "$lib/api/auth.js";

  let isLoading = $state(true);
  let isAuthenticated = $state(false);

  onMount(async () => {
    const storedKey = getStoredKey();
    if (storedKey) {
      const isValid = await validateKey(storedKey);
      if (isValid) {
        isAuthenticated = true;
      }
    }
    isLoading = false;
  });

  function handleActivate() {
    isAuthenticated = true;
  }
</script>

<main class="container">
  {#if isLoading}
    <div class="loading" in:fade>Verifying license...</div>
  {:else if isAuthenticated}
    <div class="dashboard" in:fade>
      <TopPanel />
    </div>
  {:else}
    <div class="auth-wrapper" in:fade>
      <AuthBox onActivate={handleActivate} />
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
