const AXIOM_HOSTNAME = "axiom.trade";
const NETWORK_PARAMETER_NAMES = new Set([
    "chain",
    "chains",
    "pulseChains",
    "trackerChains",
    "discoverChains",
]);
const SAFE_ADDRESS = /^[A-Za-z0-9_-]{1,128}$/;

export type AxiomChain = "sol" | "bsc";

export type AxiomUrlValidation =
    | {
          ok: true;
          url: string;
          chain: AxiomChain;
          address: string;
      }
    | {
          ok: false;
          errorCode:
              | "invalid_type"
              | "invalid_url"
              | "invalid_origin"
              | "invalid_credentials"
              | "invalid_path"
              | "invalid_chain"
              | "invalid_query"
              | "fragment_not_allowed";
      };

export function isAxiomPageUrl(value: unknown): value is string {
    if (typeof value !== "string" || value.length === 0) return false;

    try {
        const url = new URL(value);
        return (
            url.protocol === "https:" &&
            url.hostname === AXIOM_HOSTNAME &&
            url.port === "" &&
            url.username === "" &&
            url.password === ""
        );
    } catch {
        return false;
    }
}

export function validateAxiomTokenUrl(value: unknown): AxiomUrlValidation {
    if (typeof value !== "string" || value.length === 0) {
        return { ok: false, errorCode: "invalid_type" };
    }

    let url: URL;
    try {
        url = new URL(value);
    } catch {
        return { ok: false, errorCode: "invalid_url" };
    }

    if (
        url.protocol !== "https:" ||
        url.hostname !== AXIOM_HOSTNAME ||
        url.port !== ""
    ) {
        return { ok: false, errorCode: "invalid_origin" };
    }
    if (url.username !== "" || url.password !== "") {
        return { ok: false, errorCode: "invalid_credentials" };
    }
    if (url.hash !== "") {
        return { ok: false, errorCode: "fragment_not_allowed" };
    }

    const pathMatch = /^\/meme\/([^/]+)$/.exec(url.pathname);
    const address = pathMatch?.[1];
    if (!address || !SAFE_ADDRESS.test(address)) {
        return { ok: false, errorCode: "invalid_path" };
    }

    const chains = url.searchParams.getAll("chain");
    if (chains.length !== 1 || !isAxiomChain(chains[0])) {
        return { ok: false, errorCode: "invalid_chain" };
    }

    for (const [name, parameterValue] of url.searchParams) {
        if (
            !NETWORK_PARAMETER_NAMES.has(name) ||
            !isNetworkParameter(parameterValue)
        ) {
            return { ok: false, errorCode: "invalid_query" };
        }
    }

    url.searchParams.sort();

    return {
        ok: true,
        url: url.toString(),
        chain: chains[0],
        address,
    };
}

function isAxiomChain(value: string | undefined): value is AxiomChain {
    return value === "sol" || value === "bsc";
}

function isNetworkParameter(value: string): boolean {
    const values = value.split(",");
    return values.length > 0 && values.every(isAxiomChain);
}
