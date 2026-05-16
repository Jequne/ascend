<script>
    import { validateKey, storeKey } from "$lib/api/auth.js";

    // Пропсы Svelte 5 для передачи эвентов наружу
    let { onActivate } = $props();

    let key = $state("");
    let isActivating = $state(false);
    let errorMessage = $state("");

    async function activate(event) {
        event.preventDefault();
        if (!key.trim()) {
            errorMessage = "Please enter a key.";
            return;
        }

        isActivating = true;
        errorMessage = "";

        // Вызов бизнес логики API
        const isValid = await validateKey(key);

        if (isValid) {
            storeKey(key);
            onActivate(); // Сигнализируем родительскому компоненту об успехе
        } else {
            errorMessage = "Invalid key. Please try again.";
        }
        isActivating = false;
    }
</script>

<div class="auth-box">
    <div class="icon-container">
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="key-icon"
        >
            <path
                d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"
            />
            <path d="m21 2-9.6 9.6" />
            <circle cx="7.5" cy="15.5" r="5.5" />
        </svg>
    </div>

    <h1>License Required</h1>
    <p>Enter your license key to activate the application.</p>

    <form onsubmit={activate}>
        <input
            type="text"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            bind:value={key}
            disabled={isActivating}
        />
        {#if errorMessage}
            <div class="error">{errorMessage}</div>
        {/if}
        <button type="submit" disabled={isActivating} class="btn-activate">
            {isActivating ? "Activating..." : "Activate"}
        </button>
    </form>
</div>

<style>
    .auth-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        max-width: 450px;
        padding: 2rem;
    }

    .icon-container {
        background-color: #212530;
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 24px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .key-icon {
        color: #a0aec0;
    }

    h1 {
        margin-top: 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
    }

    p {
        color: #a0aec0;
        margin-bottom: 32px;
        font-size: 0.95rem;
        text-align: center;
    }

    form {
        display: flex;
        flex-direction: column;
        gap: 16px;
        width: 100%;
    }

    input {
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #2d3748;
        background: #1e202c;
        color: #a0aec0;
        font-size: 0.95rem;
        font-family: monospace;
        text-align: center;
        outline: none;
        transition: border-color 0.2s;
    }

    input::placeholder {
        color: #4a5568;
    }

    input:focus {
        border-color: #4c51bf;
    }

    input:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }

    .btn-activate {
        padding: 14px;
        border-radius: 8px;
        border: none;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
        background-color: #434190;
        color: white;
        width: 100%;
    }

    .btn-activate:hover:not(:disabled) {
        background-color: #4c51bf;
    }

    .btn-activate:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }

    .error {
        color: #fc8181;
        font-size: 0.85rem;
        text-align: center;
    }
</style>
