<script lang="ts">
    import type { Terminal } from "$lib/types";

    export let value: Terminal;

    let terminalButtons: HTMLButtonElement[] = [];

    const terminals = [
        {
            value: "axiom",
            label: "Axiom.trade",
            description: "Pair view",
            icon: "/icons/axiom.svg",
        },
        {
            value: "gmgn",
            label: "GMGN",
            description: "Token view",
            icon: "/icons/gmgn.svg",
        },
    ] as const;

    function selectTerminal(index: number): void {
        const normalizedIndex = (index + terminals.length) % terminals.length;
        const terminal = terminals[normalizedIndex];
        if (!terminal) return;
        value = terminal.value;
        terminalButtons[normalizedIndex]?.focus();
    }

    function handleKeydown(event: KeyboardEvent, index: number): void {
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            event.preventDefault();
            selectTerminal(index + 1);
        } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
            event.preventDefault();
            selectTerminal(index - 1);
        } else if (event.key === "Home") {
            event.preventDefault();
            selectTerminal(0);
        } else if (event.key === "End") {
            event.preventDefault();
            selectTerminal(terminals.length - 1);
        }
    }
</script>

<div
    class="relative grid grid-cols-2 gap-1 rounded-xl border border-white/[0.08] bg-black/20 p-1 shadow-[inset_0_1px_2px_rgba(0,0,0,0.28)]"
    role="radiogroup"
    aria-label="Token terminal"
>
    <span
        class="border-accent-blue/35 bg-accent-blue/12 pointer-events-none absolute top-1 bottom-1 left-1 w-[calc(50%-6px)] rounded-[9px] border shadow-[inset_0_1px_0_rgba(255,255,255,0.045)] transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none {value ===
        'gmgn'
            ? 'translate-x-[calc(100%+4px)]'
            : 'translate-x-0'}"
        aria-hidden="true"
    ></span>

    {#each terminals as terminal, index (terminal.value)}
        <button
            class="focus-visible:ring-accent-blue relative z-10 flex h-[52px] min-w-0 cursor-pointer items-center justify-center gap-2 rounded-[9px] px-3 text-left transition-colors duration-200 outline-none hover:bg-white/[0.035] focus-visible:ring-2 {value ===
            terminal.value
                ? 'text-foreground'
                : 'text-slate-400 hover:text-slate-200'}"
            type="button"
            role="radio"
            aria-checked={value === terminal.value}
            tabindex={value === terminal.value ? 0 : -1}
            bind:this={terminalButtons[index]}
            onclick={() => (value = terminal.value)}
            onkeydown={(event) => handleKeydown(event, index)}
        >
            <img
                class="size-7 shrink-0 object-contain"
                src={terminal.icon}
                alt=""
                aria-hidden="true"
            />
            <span class="min-w-0">
                <span class="block truncate text-xs font-bold"
                    >{terminal.label}</span
                >
                <span class="text-muted block text-[0.58rem] max-[500px]:hidden"
                    >{terminal.description}</span
                >
            </span>
        </button>
    {/each}
</div>
