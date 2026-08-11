<script lang="ts">
    import SwitchControl from "$lib/components/settings/SwitchControl.svelte";
    import TerminalSelector from "$lib/components/settings/TerminalSelector.svelte";
    import type { Terminal } from "$lib/types";

    export let checked: boolean;
    export let terminal: Terminal;
</script>

<section
    class="border-b border-white/[0.06] px-3 py-3"
    aria-labelledby="auto-open-title"
>
    <div class="mx-auto flex w-full max-w-[560px] flex-col gap-2">
        <div
            class="flex items-center justify-between gap-4 rounded-xl border border-white/[0.07] bg-white/[0.018] px-3 py-2.5"
        >
            <div class="min-w-0 text-left">
                <h3
                    id="auto-open-title"
                    class="text-foreground m-0 text-xs font-bold"
                >
                    Auto-open new tokens
                </h3>
                <p class="text-muted mt-0.5 mb-0 text-[0.64rem] leading-snug">
                    Open accepted tokens immediately. Previous-token cards stay
                    manual.
                </p>
            </div>
            <SwitchControl
                bind:checked
                label="Automatically open accepted tokens"
            />
        </div>

        <div class="flex flex-col gap-1">
            <span class="px-1 text-[0.62rem] font-semibold text-slate-400"
                >Open with</span
            >
            <TerminalSelector bind:value={terminal} />
        </div>
    </div>
</section>
