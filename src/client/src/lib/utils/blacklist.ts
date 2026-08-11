import type { BlacklistMatcher, BlacklistToken } from "$lib/types";

interface TrieNode {
    children: Map<string, TrieNode>;
    failure: TrieNode | null;
    output: boolean;
}

export function normalizeBlacklistEntries(value: unknown): string[] {
    const rawEntries = Array.isArray(value)
        ? value
        : typeof value === "string"
          ? value.split(/[\n,]+/)
          : [];
    const entries: string[] = [];
    const seen = new Set<string>();

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

export function blacklistEntriesToText(value: unknown): string {
    return normalizeBlacklistEntries(value).join("\n");
}

function createTrieNode(): TrieNode {
    return {
        children: new Map<string, TrieNode>(),
        failure: null,
        output: false,
    };
}

export function createBlacklistMatcher(
    blacklistEntries: unknown = [],
): BlacklistMatcher | null {
    const normalizedEntries = normalizeBlacklistEntries(blacklistEntries).map(
        (entry) => entry.toLowerCase(),
    );

    if (!normalizedEntries.length) return null;

    const root = createTrieNode();

    for (const entry of normalizedEntries) {
        let node = root;

        for (const character of entry) {
            let child = node.children.get(character);
            if (!child) {
                child = createTrieNode();
                node.children.set(character, child);
            }
            node = child;
        }

        node.output = true;
    }

    const queue: TrieNode[] = [];

    for (const child of root.children.values()) {
        child.failure = root;
        queue.push(child);
    }

    for (let index = 0; index < queue.length; index += 1) {
        const current = queue[index];
        if (!current) continue;

        for (const [character, child] of current.children.entries()) {
            let failure = current.failure;

            while (failure && !failure.children.has(character)) {
                failure = failure.failure;
            }

            child.failure = failure?.children.get(character) ?? root;
            child.output = child.output || child.failure.output;
            queue.push(child);
        }
    }

    const matchesText = (text: string): boolean => {
        if (!text) return false;

        let node = root;

        for (const character of text) {
            while (node !== root && !node.children.has(character)) {
                node = node.failure ?? root;
            }

            node = node.children.get(character) ?? node;
            if (node.output) return true;
        }

        return false;
    };

    const matchesToken = (token: BlacklistToken): boolean => {
        const fields = [
            token.dev_wallet,
            token.token_name,
            token.token_ticker,
            token.twitter_admin_nickname,
        ];

        return fields.some((field) => {
            const normalizedField = String(field ?? "")
                .trim()
                .toLowerCase();
            return normalizedField ? matchesText(normalizedField) : false;
        });
    };

    return {
        entries: normalizedEntries,
        matchesText,
        matchesToken,
    };
}

export function tokenMatchesBlacklist(
    token: BlacklistToken,
    blacklist: readonly string[] | BlacklistMatcher | null,
): boolean {
    if (!blacklist) return false;
    if ("matchesToken" in blacklist) return blacklist.matchesToken(token);

    const matcher = createBlacklistMatcher(blacklist);
    return matcher ? matcher.matchesToken(token) : false;
}
