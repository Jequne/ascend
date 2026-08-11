<script lang="ts">
    import { ChevronDown } from "@lucide/svelte";

    export let label: string;
    export let open = false;
</script>

<div class="border-t border-white/[0.06]">
    <button
        class="text-muted hover:text-foreground focus-visible:ring-accent-purple flex min-h-9 w-full items-center justify-between gap-2 rounded-md px-1 text-left text-[0.66rem] font-semibold transition-colors focus-visible:ring-2 focus-visible:outline-none"
        type="button"
        aria-expanded={open}
        onclick={() => (open = !open)}
    >
        {label}
        <ChevronDown
            class="shrink-0 transition-transform duration-150 motion-reduce:transition-none {open
                ? 'rotate-180'
                : ''}"
            size={14}
            aria-hidden="true"
        />
    </button>
    {#if open}
        <div class="text-muted px-1 pb-2 text-[0.62rem] leading-relaxed">
            <slot></slot>
        </div>
    {/if}
</div>
