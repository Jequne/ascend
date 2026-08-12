<script lang="ts">
    import { onDestroy } from "svelte";

    export let src: string;
    export let alt: string;
    export let className = "";

    const retryDelays = [1_000, 2_000, 4_000] as const;

    let activeSource = src;
    let imageSource = src;
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

    function reset(source: string): void {
        clearRetry();
        activeSource = source;
        imageSource = source;
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

        const delay = retryDelays[retryCount];
        if (delay === undefined) return;

        retryTimer = setTimeout(() => {
            retryCount += 1;
            imageSource = retrySource(activeSource, retryCount);
            retryTimer = undefined;
        }, delay);
    }

    $: if (src !== activeSource) reset(src);

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
