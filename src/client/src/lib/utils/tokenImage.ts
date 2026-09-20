import { API_BASE_URL } from "$lib/config/constants";

interface ImageToken {
    blockchain: string;
    token_address: string;
    token_image: string | null;
}

const SOLANA_ADDRESS_PATTERN = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const AXIOM_IMAGE_BASE_URL =
    "https://axiomtrading.sfo3.cdn.digitaloceanspaces.com";

function buildServerImageUrl(tokenAddress: string): string {
    return `${API_BASE_URL.replace(/\/$/, "")}/token-images/${tokenAddress}`;
}

export function resolveTokenImageUrls(token: ImageToken): string[] {
    const candidates: string[] = [];
    const suppliedImage = token.token_image?.trim();
    if (suppliedImage) candidates.push(suppliedImage);

    const tokenAddress = token.token_address.trim();
    if (
        token.blockchain === "sol" &&
        SOLANA_ADDRESS_PATTERN.test(tokenAddress)
    ) {
        candidates.push(`${AXIOM_IMAGE_BASE_URL}/${tokenAddress}.webp`);
        candidates.push(buildServerImageUrl(tokenAddress));
    }

    return [...new Set(candidates)];
}
