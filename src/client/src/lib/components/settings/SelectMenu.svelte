<script lang="ts">
    import { Check, ChevronDown } from "@lucide/svelte";
    import type { FeesMode, Terminal } from "$lib/types";
    import { onDestroy, onMount, tick } from "svelte";

    type SelectValue = FeesMode | Terminal;

    interface SelectOption {
        value: SelectValue;
        label: string;
        description?: string;
    }

    export let id: string;
    export let label: string;
    export let value: SelectValue;
    export let options: readonly SelectOption[];
    export let disabled = false;

    let root: HTMLDivElement;
    let trigger: HTMLButtonElement;
    let optionButtons: HTMLButtonElement[] = [];
    let open = false;

    $: selectedOption =
        options.find((option) => option.value === value) ?? options[0];

    function focusOption(index: number): void {
        const normalizedIndex = (index + options.length) % options.length;
        optionButtons[normalizedIndex]?.focus();
    }

    function openMenu(): void {
        if (disabled) return;
        open = true;
        const selectedIndex = Math.max(
            0,
            options.findIndex((option) => option.value === value),
        );
        void tick().then(() => focusOption(selectedIndex));
    }

    function closeMenu(restoreFocus = true): void {
        open = false;
        if (restoreFocus) void tick().then(() => trigger?.focus());
    }

    function selectOption(nextValue: SelectValue): void {
        value = nextValue;
        closeMenu();
    }

    function handleTriggerKeydown(event: KeyboardEvent): void {
        if (
            event.key === "ArrowDown" ||
            event.key === "ArrowUp" ||
            event.key === "Enter" ||
            event.key === " "
        ) {
            event.preventDefault();
            openMenu();
        }
    }

    function handleOptionKeydown(event: KeyboardEvent, index: number): void {
        if (event.key === "ArrowDown") {
            event.preventDefault();
            focusOption(index + 1);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            focusOption(index - 1);
        } else if (event.key === "Home") {
            event.preventDefault();
            focusOption(0);
        } else if (event.key === "End") {
            event.preventDefault();
            focusOption(options.length - 1);
        } else if (event.key === "Escape" || event.key === "Tab") {
            closeMenu(event.key === "Escape");
        }
    }

    function handleDocumentPointerDown(event: PointerEvent): void {
        if (
            open &&
            event.target instanceof Node &&
            !root.contains(event.target)
        ) {
            closeMenu(false);
        }
    }

    onMount(() => {
        document.addEventListener("pointerdown", handleDocumentPointerDown);
    });

    onDestroy(() => {
        document.removeEventListener("pointerdown", handleDocumentPointerDown);
    });
</script>

<div class="relative min-w-0" bind:this={root}>
    <button
        class="text-foreground focus:border-accent-blue/60 focus:ring-accent-blue/15 flex h-9 w-full items-center justify-between gap-2 rounded-[10px] border border-white/10 bg-[#11141d] px-2.5 text-left text-xs font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.025),0_3px_10px_rgba(0,0,0,0.12)] transition-[border-color,background-color,box-shadow] outline-none hover:border-white/20 hover:bg-[#151924] focus:ring-2 disabled:cursor-not-allowed disabled:opacity-40"
        type="button"
        role="combobox"
        aria-label={label}
        aria-controls={`${id}-listbox`}
        aria-expanded={open}
        aria-haspopup="listbox"
        {disabled}
        bind:this={trigger}
        onclick={() => (open ? closeMenu() : openMenu())}
        onkeydown={handleTriggerKeydown}
    >
        <span class="min-w-0 truncate">{selectedOption?.label ?? value}</span>
        <ChevronDown
            class="text-muted shrink-0 transition-transform duration-150 motion-reduce:transition-none {open
                ? 'rotate-180'
                : ''}"
            size={15}
            aria-hidden="true"
        />
    </button>

    {#if open}
        <div
            class="absolute top-full right-0 left-0 z-50 mt-1 overflow-hidden rounded-[11px] border border-white/10 bg-[#171a23] p-1 shadow-[0_16px_38px_rgba(0,0,0,0.48),inset_0_1px_0_rgba(255,255,255,0.04)]"
            id={`${id}-listbox`}
            role="listbox"
            aria-label={label}
        >
            {#each options as option, index (option.value)}
                <button
                    class="focus:bg-accent-blue/15 flex min-h-9 w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs transition-colors outline-none hover:bg-white/[0.055] {value ===
                    option.value
                        ? 'bg-accent-blue/12 text-foreground'
                        : 'text-slate-300'}"
                    type="button"
                    role="option"
                    aria-selected={value === option.value}
                    bind:this={optionButtons[index]}
                    onclick={() => selectOption(option.value)}
                    onkeydown={(event) => handleOptionKeydown(event, index)}
                >
                    <span class="min-w-0 grow">
                        <span class="block font-semibold">{option.label}</span>
                        {#if option.description}
                            <span
                                class="text-muted mt-0.5 block text-[0.58rem] leading-snug"
                                >{option.description}</span
                            >
                        {/if}
                    </span>
                    {#if value === option.value}
                        <Check
                            class="text-accent-blue shrink-0"
                            size={14}
                            aria-hidden="true"
                        />
                    {/if}
                </button>
            {/each}
        </div>
    {/if}
</div>
