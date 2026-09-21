<script lang="ts">
    import { onDestroy } from "svelte";

    export let sources: readonly string[];
    export let alt: string;
    export let className = "";
    const retryDelays = [
        1_000, 2_000, 4_000, 8_000, 16_000, 30_000, 60_000, 300_000,
    ] as const;

    let activeSources = [...sources];
    let activeSignature = sources.join("\0");
    let sourceIndex = 0;
    let imageSource = activeSources[0] ?? "";
    let retryCount = 0;
    let imageVisible = true;
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
        imageVisible = true;
    }

    function handleLoad(): void {
        clearRetry();
        imageVisible = true;
    }

    function handleError(): void {
        imageVisible = false;
        clearRetry();

        const nextSource = activeSources[sourceIndex + 1];
        if (nextSource !== undefined) {
            sourceIndex += 1;
            imageVisible = true;
            imageSource =
                retryCount === 0
                    ? nextSource
                    : retrySource(nextSource, retryCount);
            return;
        }

        const delay = retryDelays[Math.min(retryCount, retryDelays.length - 1)];

        retryTimer = setTimeout(() => {
            retryCount += 1;
            sourceIndex = 0;
            imageVisible = true;
            imageSource = retrySource(activeSources[0] ?? "", retryCount);
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
    class:opacity-0={!imageVisible}
    src={imageSource}
    {alt}
    onload={handleLoad}
    onerror={handleError}
/>
