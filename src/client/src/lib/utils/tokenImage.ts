import type { TokenFeed } from "$lib/types";

type ImageToken = Pick<
    TokenFeed,
    "blockchain" | "token_address" | "token_image"
>;

const SOLANA_ADDRESS_PATTERN = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const AXIOM_IMAGE_BASE_URL =
    "https://axiomtrading.sfo3.cdn.digitaloceanspaces.com";

export function resolveTokenImageUrl(token: ImageToken): string | null {
    const suppliedImage = token.token_image?.trim();
    if (suppliedImage) return suppliedImage;

    const tokenAddress = token.token_address.trim();
    if (
        token.blockchain !== "sol" ||
        !SOLANA_ADDRESS_PATTERN.test(tokenAddress)
    ) {
        return null;
    }

    return `${AXIOM_IMAGE_BASE_URL}/${tokenAddress}.webp`;
}
