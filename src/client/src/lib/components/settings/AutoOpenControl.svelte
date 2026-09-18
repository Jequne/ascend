<script lang="ts">
    import ExtensionSetup from "$lib/components/settings/ExtensionSetup.svelte";
    import SwitchControl from "$lib/components/settings/SwitchControl.svelte";
    import TerminalSelector from "$lib/components/settings/TerminalSelector.svelte";
    import { extensionBridgeStore } from "$lib/stores/extensionBridge.svelte";
    import type { AutoOpenMode, Terminal } from "$lib/types";

    export let mode: AutoOpenMode;
    export let terminal: Terminal;
    export let highlightMigratedTokens: boolean;

    const modes: ReadonlyArray<{
        value: AutoOpenMode;
        title: string;
        description: string;
    }> = [
        {
            value: "off",
            title: "Off",
            description: "Do not open accepted tokens.",
        },
        {
            value: "new_tab",
            title: "New tab",
            description:
                "Use the selected terminal and existing system opener.",
        },
        {
            value: "current_axiom_tab",
            title: "Current Axiom tab",
            description:
                "Axiom only — requires a paired extension and selected tab.",
        },
    ];

    function bridgeStatus(): string {
        const state = extensionBridgeStore.state;
        if (state.listenerStatus === "port_in_use")
            return "Bridge unavailable — port in use";
        if (state.listenerStatus === "unavailable") return "Bridge unavailable";
        if (state.listenerStatus === "starting") return "Connecting";
        if (state.connectionStatus !== "connected")
            return "Not installed / not paired";
        return state.targetStatus === "selected"
            ? "Connected — target selected"
            : "Connected — select an Axiom tab";
    }

    function handleModeKeydown(event: KeyboardEvent, index: number): void {
        const keyOffsets: Record<string, number> = {
            ArrowRight: 1,
            ArrowDown: 1,
            ArrowLeft: -1,
            ArrowUp: -1,
        };
        let nextIndex: number;
        if (event.key === "Home") nextIndex = 0;
        else if (event.key === "End") nextIndex = modes.length - 1;
        else if (event.key in keyOffsets) {
            nextIndex =
                (index + (keyOffsets[event.key] ?? 0) + modes.length) %
                modes.length;
        } else return;

        event.preventDefault();
        const nextMode = modes[nextIndex];
        if (!nextMode) return;
        mode = nextMode.value;
        const group = (event.currentTarget as HTMLElement).parentElement;
        group
            ?.querySelectorAll<HTMLButtonElement>('[role="radio"]')
            [nextIndex]?.focus();
    }
</script>

<section
    class="border-b border-white/[0.06] px-3 py-3"
    aria-labelledby="auto-open-title"
>
    <div class="mx-auto flex w-full max-w-[560px] flex-col gap-2">
        <div class="rounded-xl border border-white/[0.07] bg-white/[0.018] p-3">
            <div class="flex items-center justify-between gap-3">
                <div>
                    <h3
                        id="auto-open-title"
                        class="text-foreground m-0 text-xs font-bold"
                    >
                        Auto-open accepted tokens
                    </h3>
                    <p
                        class="text-muted mt-0.5 mb-0 text-[0.64rem] leading-snug"
                    >
                        Choose exactly one destination for accepted feed tokens.
                    </p>
                </div>
                <span
                    class="text-muted rounded-full border border-white/10 bg-white/[0.035] px-2 py-1 text-[0.6rem]"
                    aria-live="polite">{bridgeStatus()}</span
                >
            </div>

            <div
                class="mt-3 grid gap-1.5"
                role="radiogroup"
                aria-label="Auto-open mode"
            >
                {#each modes as option, index (option.value)}
                    <button
                        type="button"
                        role="radio"
                        aria-checked={mode === option.value}
                        tabindex={mode === option.value ? 0 : -1}
                        class={`focus-visible:ring-accent-blue min-h-11 rounded-lg border px-3 py-2 text-left transition-colors hover:bg-white/[0.05] focus-visible:ring-2 focus-visible:outline-none ${mode === option.value ? "border-blue-400/45 bg-blue-500/10" : "border-white/[0.07] bg-white/[0.02]"}`}
                        onclick={() => (mode = option.value)}
                        onkeydown={(event) => handleModeKeydown(event, index)}
                    >
                        <span class="text-foreground block text-xs font-bold"
                            >{option.title}</span
                        >
                        <span
                            class="text-muted mt-0.5 block text-[0.61rem] leading-snug"
                            >{option.description}</span
                        >
                    </button>
                {/each}
            </div>
        </div>

        <div class="flex flex-col gap-1">
            <span class="px-1 text-[0.62rem] font-semibold text-slate-400"
                >Open manual links and new tabs with</span
            >
            <TerminalSelector bind:value={terminal} />
        </div>

        <ExtensionSetup />

        <div
            class="flex items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-white/[0.018] px-3 py-2"
        >
            <div class="flex min-w-0 items-center gap-2.5">
                <span
                    class="text-success border-success/25 bg-success/10 inline-flex size-6 shrink-0 items-center justify-center rounded-md border text-[0.68rem] font-black"
                    aria-hidden="true">M</span
                >
                <div class="min-w-0">
                    <p class="text-foreground m-0 text-xs font-bold">
                        Highlight migrated tokens
                    </p>
                    <p
                        class="text-muted mt-0.5 mb-0 text-[0.61rem] leading-snug"
                    >
                        Add a subtle tint to migrated rows in Last Tokens.
                    </p>
                </div>
            </div>
            <SwitchControl
                bind:checked={highlightMigratedTokens}
                label="Highlight migrated previous tokens"
            />
        </div>
    </div>
</section>
