<script lang="ts">
    export let checked: boolean;
</script>

<section
    class="flex items-center justify-center gap-4 px-4 py-2.5 text-center"
    aria-labelledby="auto-open-title"
>
    <div class="max-w-[34ch]">
        <h3 id="auto-open-title" class="text-foreground m-0 text-xs font-bold">
            Auto open new token
        </h3>
        <p class="text-muted mt-0.5 mb-0 text-[0.64rem] leading-snug">
            Opens accepted tokens in the selected terminal. Last token cards
            stay manual.
        </p>
    </div>

    <button
        class="focus-visible:ring-accent-purple focus-visible:ring-offset-canvas relative h-6 w-11 shrink-0 rounded-full border transition-[background-color,border-color,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none {checked
            ? 'border-success/50 bg-success/30'
            : 'border-white/15 bg-white/[0.07]'}"
        type="button"
        role="switch"
        aria-label="Automatically open accepted tokens"
        aria-checked={checked}
        onclick={() => (checked = !checked)}
    >
        <span
            class="bg-foreground absolute top-0.5 left-0.5 size-[18px] rounded-full shadow-[0_2px_6px_rgba(0,0,0,0.35)] transition-transform duration-150 motion-reduce:transition-none {checked
                ? 'translate-x-5'
                : 'translate-x-0'}"
            aria-hidden="true"
        ></span>
    </button>
</section>
