<script lang="ts">
    import SelectMenu from "$lib/components/settings/SelectMenu.svelte";
    import SwitchControl from "$lib/components/settings/SwitchControl.svelte";
    import type { Terminal } from "$lib/types";

    export let checked: boolean;
    export let terminal: Terminal;

    const terminalOptions = [
        {
            value: "axiom",
            label: "Axiom",
            description: "Open the pair view in Axiom",
        },
        {
            value: "gmgn",
            label: "GMGN",
            description: "Open the token view in GMGN",
        },
    ] as const;
</script>

<section
    class="border-b border-white/[0.06] px-3 py-3"
    aria-labelledby="auto-open-title"
>
    <div class="mx-auto flex w-full max-w-[430px] flex-col gap-2.5">
        <div
            class="grid grid-cols-[44px_minmax(0,1fr)_44px] items-center gap-3"
        >
            <span aria-hidden="true"></span>
            <div class="text-center">
                <h3
                    id="auto-open-title"
                    class="text-foreground m-0 text-xs font-bold"
                >
                    Auto-open new tokens
                </h3>
                <p class="text-muted mt-0.5 mb-0 text-[0.64rem] leading-snug">
                    Open accepted tokens immediately in your preferred terminal.
                    Previous-token cards stay manual.
                </p>
            </div>
            <SwitchControl
                bind:checked
                label="Automatically open accepted tokens"
            />
        </div>

        <div
            class="mx-auto grid w-[min(290px,100%)] grid-cols-[auto_minmax(0,1fr)] items-center gap-2"
        >
            <span class="text-[0.66rem] font-semibold text-slate-300"
                >Token terminal</span
            >
            <SelectMenu
                id="token-terminal"
                label="Token terminal"
                options={terminalOptions}
                bind:value={terminal}
            />
        </div>
    </div>
</section>
