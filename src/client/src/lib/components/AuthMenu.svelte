<script>
    import { validateApiKey } from "$lib/api/auth.js";
    import { parseErrorMessage } from "$lib/core/errors/index.js";

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
            console.log("Authorization successful:", response);

            // TODO: Store auth state and redirect user to main application
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

    function handleKeyPress(event) {
        if (event.key === "Enter" && !isLoading && apiKey.trim()) {
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
        <input
            type="text"
            placeholder="XXXXXXXX-XXXX-XXXXXXXX-XXXX"
            bind:value={apiKey}
            onkeypress={handleKeyPress}
            disabled={isDisabled}
            aria-label="API Key input"
        />
        <button
            onclick={handleActivate}
            disabled={isDisabled || !apiKey.trim()}
        >
            {isLoading ? "Activating..." : "Activate"}
        </button>

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

    .auth-menu-input-field input {
        width: 100%;
        padding: 12px;
        background-color: #1e2029;
        border: 1px solid #333;
        border-radius: 8px;
        color: #fff;
        text-align: center;
        outline: none;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }

    .auth-menu-input-field input:focus {
        border-color: #3f4494;
    }

    .auth-menu-input-field input:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }

    .auth-menu-input-field button {
        width: 100%;
        background-color: #3f4494;
        border: none;
        border-radius: 8px;
        margin-top: 15px;
        cursor: pointer;
        padding: 12px;
        color: #fff;
        font-weight: 600;
        transition: background-color 0.2s;
    }

    .auth-menu-input-field button:hover:not(:disabled) {
        background-color: #4c52ab;
    }

    .auth-menu-input-field button:disabled {
        background-color: #2a2d64;
        color: #6b7280;
        cursor: not-allowed;
    }

    .error-text {
        color: #ef4444;
        font-size: 13px;
        margin-top: 12px;
        font-weight: 500;
    }
</style>
