<script lang="ts">
    export let checked: boolean;
    export let label: string;
    export let onChange: (nextValue: boolean) => void = (nextValue) =>
        (checked = nextValue);
</script>

<button
    class="focus-visible:ring-accent-purple focus-visible:ring-offset-canvas relative h-6 w-11 shrink-0 rounded-full border shadow-[inset_0_1px_2px_rgba(0,0,0,0.35)] transition-[background-color,border-color,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none {checked
        ? 'border-success/60 bg-success/35'
        : 'border-white/15 bg-white/[0.07]'}"
    type="button"
    role="switch"
    aria-label={label}
    aria-checked={checked}
    onclick={() => onChange(!checked)}
>
    <span
        class="bg-foreground absolute top-0.5 left-0.5 size-[18px] rounded-full border border-white/60 shadow-[0_2px_6px_rgba(0,0,0,0.4)] transition-transform duration-150 motion-reduce:transition-none {checked
            ? 'translate-x-5'
            : 'translate-x-0'}"
        aria-hidden="true"
    ></span>
</button>
