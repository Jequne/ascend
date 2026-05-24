export function normalizeBlacklistEntries(value) {
    const rawEntries = Array.isArray(value)
        ? value
        : typeof value === "string"
            ? value.split(/[\n,]+/)
            : [];

    const entries = [];
    const seen = new Set();

    for (const entry of rawEntries) {
        const normalizedEntry = String(entry ?? "").trim();
        if (!normalizedEntry) continue;

        const dedupeKey = normalizedEntry.toLowerCase();
        if (seen.has(dedupeKey)) continue;

        seen.add(dedupeKey);
        entries.push(normalizedEntry);
    }

    return entries;
}

export function blacklistEntriesToText(value) {
    return normalizeBlacklistEntries(value).join("\n");
}

function createTrieNode() {
    return {
        children: new Map(),
        failure: null,
        output: false,
    };
}

export function createBlacklistMatcher(blacklistEntries = []) {
    const normalizedEntries = normalizeBlacklistEntries(blacklistEntries).map(
        (entry) => entry.toLowerCase(),
    );

    if (!normalizedEntries.length) return null;

    const root = createTrieNode();

    for (const entry of normalizedEntries) {
        let node = root;

        for (const character of entry) {
            if (!node.children.has(character)) {
                node.children.set(character, createTrieNode());
            }

            node = node.children.get(character);
        }

        node.output = true;
    }

    const queue = [];

    for (const child of root.children.values()) {
        child.failure = root;
        queue.push(child);
    }

    for (let index = 0; index < queue.length; index += 1) {
        const current = queue[index];

        for (const [character, child] of current.children.entries()) {
            let failure = current.failure;

            while (failure && !failure.children.has(character)) {
                failure = failure.failure;
            }

            child.failure = failure ? failure.children.get(character) : root;
            child.output = child.output || Boolean(child.failure?.output);
            queue.push(child);
        }
    }

    function matchesText(text) {
        if (!text) return false;

        let node = root;

        for (const character of text) {
            while (node !== root && !node.children.has(character)) {
                node = node.failure ?? root;
            }

            if (node.children.has(character)) {
                node = node.children.get(character);
            }

            if (node.output) {
                return true;
            }
        }

        return false;
    }

    function matchesToken(token = {}) {
        const fields = [
            token.dev_wallet,
            token.token_name,
            token.token_ticker,
            token.twitter_admin_nickname,
        ];

        for (const field of fields) {
            const normalizedField = String(field ?? "").trim().toLowerCase();
            if (normalizedField && matchesText(normalizedField)) {
                return true;
            }
        }

        return false;
    }

    return {
        entries: normalizedEntries,
        matchesText,
        matchesToken,
    };
}

export function tokenMatchesBlacklist(token = {}, blacklistEntries = []) {
    const matcher = Array.isArray(blacklistEntries)
        ? createBlacklistMatcher(blacklistEntries)
        : blacklistEntries;

    if (!matcher) return false;

    return matcher.matchesToken(token);
}