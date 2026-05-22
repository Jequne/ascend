<script>
    export let feed = {};

    function copyToClipboard(text) {
        if (text) {
            navigator.clipboard.writeText(text);
        }
    }

    function formatNumber(value) {
        if (value === null || value === undefined) return "N/A";
        if (value >= 1e9) return (value / 1e9).toFixed(1) + "B";
        if (value >= 1e6) return (value / 1e6).toFixed(1) + "M";
        if (value >= 1e3) return (value / 1e3).toFixed(1) + "K";
        return value.toFixed(1);
    }

    function timeAgo(dateString) {
        if (!dateString) return "";
        const date = new Date(dateString);
        const seconds = Math.floor((new Date() - date) / 1000);

        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + "y";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + "mo";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + "d";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + "h";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + "m";
        return Math.floor(seconds) + "s";
    }

    $: migratedRatio = feed.all_tokens_count
        ? ((feed.migrated_tokens_count / feed.all_tokens_count) * 100).toFixed(
              1,
          )
        : 0;
</script>

<div class="token-card">
    <div class="block new-token-block">
        <div class="row main-info">
            <div class="image-container">
                <div class="image-placeholder">
                    {feed.token_ticker?.substring(0, 2) || "?"}
                </div>
                {#if feed.token_image}
                    <img
                        src={feed.token_image}
                        alt={feed.token_ticker}
                        class="token-image"
                        on:error={(e) => (e.target.style.display = "none")}
                    />
                {/if}
            </div>

            <div class="token-details-wrapper">
                <div class="token-details-top">
                    <button
                        class="token-name-header"
                        title="Click to copy address"
                        on:click={() => copyToClipboard(feed.token_address)}
                    >
                        <span class="ticker">${feed.token_ticker}</span>
                        <span class="name-text">{feed.token_name}</span>
                    </button>

                    <div class="token-top-stats">
                        {#if feed.dev_holds_percent !== null}
                            <span class="dh-stat"
                                >DH: {Number(feed.dev_holds_percent).toFixed(
                                    1,
                                )}%</span
                            >
                        {/if}
                    </div>
                </div>

                <div class="token-details-bottom">
                    <div class="socials">
                        {#if feed.website}
                            <a
                                href={feed.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                ><img
                                    src="/icons/website.svg"
                                    alt="Website"
                                    class="icon"
                                /></a
                            >
                        {/if}
                        {#if feed.twitter}
                            <a
                                href={feed.twitter}
                                target="_blank"
                                rel="noopener noreferrer"
                                ><img
                                    src="/icons/twitter.svg"
                                    alt="Twitter"
                                    class="icon"
                                /></a
                            >
                        {/if}
                        {#if feed.telegram}
                            <a
                                href={feed.telegram}
                                target="_blank"
                                rel="noopener noreferrer"
                                ><img
                                    src="/icons/telegram.svg"
                                    alt="Telegram"
                                    class="icon"
                                /></a
                            >
                        {/if}
                        {#if feed.discord}
                            <a
                                href={feed.discord}
                                target="_blank"
                                rel="noopener noreferrer"
                                ><img
                                    src="/icons/discord.svg"
                                    alt="Discord"
                                    class="icon"
                                /></a
                            >
                        {/if}
                    </div>
                </div>
            </div>
        </div>

        <!-- Dev stats row matching inspiration card -->
        <div class="dev-stats-row">
            <div class="stats-left">
                {#if feed.indicator}
                    <span class="badge indicator-badge">{feed.indicator}</span>
                {/if}
                <span class="badge blockchain-badge"
                    >{feed.blockchain || "sol"}</span
                >
            </div>
            <div class="stats-right">
                <span class="stat-item total" title="Total Tokens">
                    <img
                        src="/icons/database.svg"
                        alt="Total"
                        class="tiny-icon"
                    />
                    {feed.all_tokens_count} tokens
                </span>
                <span class="stat-divider"></span>
                <span class="stat-item migrated-count" title="Migrated Tokens">
                    <img
                        src="/icons/migrated.svg"
                        alt="Migrated"
                        class="tiny-icon"
                    />
                    {feed.migrated_tokens_count} migrated
                </span>
                <span class="stat-divider"></span>
                <span class="stat-item percent" title="Migration Rate">
                    <img
                        src="/icons/trending-up.svg"
                        alt="Rate"
                        class="tiny-icon"
                    />
                    {migratedRatio}% rate
                </span>
                {#if feed.is_migrated}
                    <span class="migrated-badge">
                        <img
                            src="/icons/migrated.svg"
                            alt="Migrated"
                            class="tiny-icon"
                        />
                    </span>
                {/if}
            </div>
        </div>
    </div>

    <!-- Last Deployed Tokens Block -->
    {#if feed.last_deployed_tokens && feed.last_deployed_tokens.length > 0}
        <div class="block last-deployed-block">
            <h4 class="section-title">Last Tokens</h4>
            <div class="last-tokens-list">
                {#each feed.last_deployed_tokens as lastToken, j (lastToken.token_address + "_" + j)}
                    <div class="last-token-item">
                        <div class="last-token-lhs">
                            <div class="last-image-container">
                                <div class="last-image-placeholder">
                                    {lastToken.token_ticker?.substring(0, 2) ||
                                        "?"}
                                </div>
                                {#if lastToken.token_image}
                                    <img
                                        src={lastToken.token_image}
                                        alt={lastToken.token_ticker}
                                        class="last-token-image"
                                        on:error={(e) =>
                                            (e.target.style.display = "none")}
                                    />
                                {/if}
                            </div>
                            <div class="last-token-info">
                                <div class="last-token-title">
                                    <span class="last-ticker"
                                        >${lastToken.token_ticker}</span
                                    >
                                    <span class="last-name"
                                        >{lastToken.token_name}</span
                                    >
                                </div>
                                <div class="last-token-metrics">
                                    <span class="time-ago"
                                        >🕒 {timeAgo(lastToken.created_at)} ago</span
                                    >
                                    {#if lastToken.ath_mcap_in_usd}
                                        <span class="mcap"
                                            >📈 ${formatNumber(
                                                lastToken.ath_mcap_in_usd,
                                            )}</span
                                        >
                                    {/if}
                                    {#if lastToken.total_pair_fees_paid}
                                        <span class="fees"
                                            >⚡ {lastToken.total_pair_fees_paid.toFixed(
                                                1,
                                            )} SOL</span
                                        >
                                    {/if}
                                    {#if lastToken.dex_paid}
                                        <span class="dex-paid" title="Dex paid"
                                            ><img
                                                src="/icons/dexscreener_logo.svg"
                                                alt="Dex"
                                                class="small-icon"
                                            /></span
                                        >
                                    {/if}
                                    {#if lastToken.is_migrated}
                                        <span
                                            class="migrated-icon"
                                            title="Migrated"
                                            ><img
                                                src="/icons/migrated.svg"
                                                alt="Migrated"
                                                class="small-icon"
                                            /></span
                                        >
                                    {/if}
                                </div>
                            </div>
                        </div>

                        <div class="last-socials">
                            {#if lastToken.website}
                                <a
                                    href={lastToken.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    ><img
                                        src="/icons/website.svg"
                                        alt="Website"
                                        class="icon"
                                    /></a
                                >
                            {/if}
                            {#if lastToken.twitter}
                                <a
                                    href={lastToken.twitter}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    ><img
                                        src="/icons/twitter.svg"
                                        alt="Twitter"
                                        class="icon"
                                    /></a
                                >
                            {/if}
                            {#if lastToken.telegram}
                                <a
                                    href={lastToken.telegram}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    ><img
                                        src="/icons/telegram.svg"
                                        alt="Telegram"
                                        class="icon"
                                    /></a
                                >
                            {/if}
                            {#if lastToken.discord}
                                <a
                                    href={lastToken.discord}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    ><img
                                        src="/icons/discord.svg"
                                        alt="Discord"
                                        class="icon"
                                    /></a
                                >
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>

<style>
    .token-card {
        background: #171821; /* Slightly darker to match image */
        border-radius: 10px;
        margin: 4px 8px;
        padding: 6px 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        flex-direction: column;
        gap: 6px;
        width: calc(100% - 16px);
        box-sizing: border-box;
        transition: transform 0.2s;
        max-width: 100%;
    }

    .token-card:hover {
        border-color: rgba(255, 255, 255, 0.1);
    }

    .block {
        display: flex;
        flex-direction: column;
        width: 100%;
    }

    .new-token-block {
        gap: 8px;
        padding-bottom: 10px;
        border-bottom: 1px solid #2d2e3d;
    }

    .dev-stats-row {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 2px;
    }

    .stats-left {
        display: flex;
        gap: 6px;
        align-items: center;
        flex-wrap: wrap;
    }

    .stats-right {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        flex-wrap: wrap;
    }

    .token-top-stats {
        margin-top: 2px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }

    .dh-stat {
        background: rgba(234, 179, 8, 0.15); /* amber tint */
        color: #fbbf24;
        border: 1px solid rgba(234, 179, 8, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .token-details-top {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .token-details-wrapper {
        display: flex;
        flex-direction: column;
        gap: 6px;
        flex-grow: 1;
        min-width: 0;
    }

    .row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }

    .badge {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .indicator-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .blockchain-badge {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    .stat-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .stat-divider {
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        display: inline-block;
    }

    .stat-item.percent {
        color: #3b82f6; /* Blueish for rate */
        font-weight: 500;
    }

    .stat-item.total {
        color: #e2e8f0;
    }

    .stat-item.migrated-count {
        color: #10b981;
    }

    .tiny-icon {
        width: 10px;
        height: 10px;
        opacity: 0.9;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
    }

    .main-info {
        justify-content: flex-start;
        gap: 8px;
        flex-wrap: nowrap;
    }

    .image-container,
    .last-image-container {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        background: #2d2e3d;
        overflow: hidden;
        flex-shrink: 0;
        position: relative;
    }

    .last-image-container {
        width: 26px;
        height: 26px;
    }

    .token-image,
    .last-token-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        position: absolute;
        top: 0;
        left: 0;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: high-quality;
    }

    .image-placeholder,
    .last-image-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #64748b;
        font-size: 1rem;
        position: absolute;
        top: 0;
        left: 0;
    }

    .last-image-placeholder {
        font-size: 0.8rem;
    }

    .token-name-header {
        margin: 0;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: color 0.15s;
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
        background: transparent;
        border: none;
        padding: 0;
        color: inherit;
        font-family: inherit;
        text-align: left;
    }

    .token-name-header:hover .name-text {
        color: #818cf8;
    }

    .name-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .ticker,
    .last-ticker {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: normal;
        background: rgba(255, 255, 255, 0.08);
        padding: 2px 4px;
        border-radius: 4px;
        flex-shrink: 0;
    }

    .socials,
    .last-socials {
        display: flex;
        gap: 6px;
        flex-shrink: 0;
        align-items: center;
    }

    .icon {
        width: 12px;
        height: 12px;
        opacity: 0.7;
        transition: opacity 0.15s;
        color: #94a3b8;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
    }

    .small-icon {
        width: 12px;
        height: 12px;
        opacity: 0.8;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
    }

    .socials a:hover .icon,
    .last-socials a:hover .icon {
        opacity: 1;
    }

    .section-title {
        margin: 0;
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .last-tokens-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .last-token-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(0, 0, 0, 0.15);
        padding: 6px 8px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.03);
        gap: 8px;
        flex-wrap: wrap;
    }

    .last-token-lhs {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-grow: 1;
        min-width: 0;
    }

    .last-token-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
        flex-grow: 1;
        min-width: 0;
    }

    .last-token-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
        font-size: 0.85rem;
        width: 100%;
        line-height: 1.2;
    }

    .last-name {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .last-token-metrics {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.7rem;
        color: #94a3b8;
        flex-wrap: wrap;
    }

    .time-ago {
        color: #818cf8;
    }

    .mcap {
        color: #10b981;
        font-weight: 500;
    }

    .fees {
        color: #fbbf24;
    }
</style>
