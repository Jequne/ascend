<script>
    import { getApiKey, clearApiKey } from "$lib/auth/storage.js";

    let apiKey = $state("");

    function loadApiKey() {
        apiKey = getApiKey() || "";
    }

    // Load API key on component mount
    if (typeof window !== "undefined") {
        loadApiKey();
    }

    function handleLogout() {
        clearApiKey();
        window.location.reload();
    }
</script>

<div class="main-container">
    <header class="header">
        <div class="header-content">
            <h1>Ascend Trenches</h1>
            <button class="logout-btn" onclick={handleLogout}> Logout </button>
        </div>
    </header>

    <main class="content">
        <section class="welcome-section">
            <h2>Welcome to Ascend Trenches</h2>
            <p>Token feed monitoring system</p>
        </section>

        <section class="main-section">
            <!-- Main interface content will be added here -->
            <div class="placeholder">
                <p>Main interface content coming soon...</p>
            </div>
        </section>
    </main>
</div>

<style>
    .main-container {
        width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: #12141c;
        color: white;
    }

    .header {
        background-color: #1e2029;
        padding: 16px 24px;
        border-bottom: 1px solid #2a2d35;
    }

    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        width: 100%;
    }

    h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
    }

    .logout-btn {
        background-color: #ef4444;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }

    .logout-btn:hover {
        background-color: #dc2626;
    }

    .logout-btn:active {
        background-color: #b91c1c;
    }

    .content {
        flex: 1;
        padding: 40px 24px;
        overflow-y: auto;
    }

    .welcome-section {
        text-align: center;
        margin-bottom: 40px;
    }

    .welcome-section h2 {
        font-size: 28px;
        font-weight: 600;
        margin: 0 0 8px;
    }

    .welcome-section p {
        font-size: 16px;
        color: #9ca3af;
        margin: 0;
    }

    .main-section {
        max-width: 1200px;
        margin: 0 auto;
        width: 100%;
    }

    .placeholder {
        background-color: #1e2029;
        border: 1px solid #2a2d35;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        color: #6b7280;
    }

    .placeholder p {
        margin: 0;
        font-size: 16px;
    }
</style>
