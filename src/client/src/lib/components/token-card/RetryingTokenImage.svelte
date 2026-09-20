<script lang="ts">
    import { onDestroy } from "svelte";

    export let sources: readonly string[];
    export let alt: string;
    export let className = "";
    export let retryFinalSource = true;

    const retryDelays = [1_000, 2_000, 4_000] as const;

    let activeSources = [...sources];
    let activeSignature = sources.join("\0");
    let sourceIndex = 0;
    let imageSource = activeSources[0] ?? "";
    let retryCount = 0;
    let loaded = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    function retrySource(source: string, attempt: number): string {
        const hashIndex = source.indexOf("#");
        const base = hashIndex === -1 ? source : source.slice(0, hashIndex);
        const hash = hashIndex === -1 ? "" : source.slice(hashIndex);
        const separator = base.includes("?") ? "&" : "?";

        return `${base}${separator}_ascend_retry=${attempt}${hash}`;
    }

    function clearRetry(): void {
        if (retryTimer === undefined) return;
        clearTimeout(retryTimer);
        retryTimer = undefined;
    }

    function reset(nextSources: readonly string[], signature: string): void {
        clearRetry();
        activeSources = [...nextSources];
        activeSignature = signature;
        sourceIndex = 0;
        imageSource = activeSources[0] ?? "";
        retryCount = 0;
        loaded = false;
    }

    function handleLoad(): void {
        clearRetry();
        loaded = true;
    }

    function handleError(): void {
        loaded = false;
        clearRetry();

        const nextSource = activeSources[sourceIndex + 1];
        if (nextSource !== undefined) {
            sourceIndex += 1;
            retryCount = 0;
            imageSource = nextSource;
            return;
        }

        if (!retryFinalSource) return;

        const delay = retryDelays[retryCount];
        if (delay === undefined) return;

        retryTimer = setTimeout(() => {
            retryCount += 1;
            imageSource = retrySource(
                activeSources[sourceIndex] ?? "",
                retryCount,
            );
            retryTimer = undefined;
        }, delay);
    }

    $: sourceSignature = sources.join("\0");
    $: if (sourceSignature !== activeSignature) {
        reset(sources, sourceSignature);
    }

    onDestroy(clearRetry);
</script>

<img
    class={className}
    class:opacity-0={!loaded}
    src={imageSource}
    {alt}
    onload={handleLoad}
    onerror={handleError}
/>
