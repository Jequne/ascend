<script>
    import { validateApiKey } from "$lib/api/auth.js";
    import { parseErrorMessage } from "$lib/core/errors/index.js";
    import { TextInput, PrimaryButton } from "$lib/components/index.js";

    let apiKey = $state("");
    let isLoading = $state(false);
    let errorMessage = $state("");
    let isDisabled = $state(false);

    async function handleActivate() {
        if (!apiKey.trim()) {
            errorMessage = "Please enter a valid API key.";
            return;
        }

        isLoading = true;
        isDisabled = true;
        errorMessage = "";

        try {
            const response = await validateApiKey(apiKey);
            console.log("Authorization response:", response);
        } catch (error) {
            errorMessage = parseErrorMessage(
                error,
                "Invalid API key. Please try again.",
            );
        } finally {
            isLoading = false;
            isDisabled = false;
        }
    }

    function handleEnter() {
        if (!isLoading && apiKey.trim()) {
            handleActivate();
        }
    }
</script>

<div class="auth-menu">
    <div class="auth-menu-title">
        <div class="icon-box">
            <img src="/key.png" alt="License key icon" />
        </div>
        <h1>License Required</h1>
        <p>Enter your API key to activate the application</p>
    </div>

    <div class="auth-menu-input-field">
        <TextInput
            placeholder="XXXXXXXX-XXXX-XXXXXXXX-XXXX"
            bind:value={apiKey}
            on:enter={handleEnter}
            disabled={isDisabled}
            ariaLabel="API key input"
        />
        <PrimaryButton
            label="Activate"
            loadingLabel="Activating..."
            loading={isLoading}
            disabled={isDisabled || !apiKey.trim()}
            on:click={handleActivate}
        />

        {#if errorMessage}
            <div class="error-text" role="alert">{errorMessage}</div>
        {/if}
    </div>
</div>

<style>
    .auth-menu {
        width: 400px;
        text-align: center;
        color: white;
    }

    .icon-box {
        width: 60px;
        height: 60px;
        background-color: #1e2029;
        border-radius: 16px;
        margin: 0 auto 20px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 24px;
    }

    .icon-box img {
        width: 32px;
        height: 32px;
        object-fit: contain;
    }

    h1 {
        font-weight: 600;
        font-size: 20px;
        margin-bottom: 8px;
    }

    p {
        font-size: 14px;
        color: #9ca3af;
        margin-bottom: 24px;
    }

    .auth-menu-input-field :global(.primary-button) {
        margin-top: 15px;
    }

    .error-text {
        color: #ef4444;
        font-size: 13px;
        margin-top: 12px;
        font-weight: 500;
    }
</style>
