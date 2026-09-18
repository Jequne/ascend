<script lang="ts">
    import { developerLabelsStore } from "$lib/stores/developerLabels.svelte";
    import { Check, Tag, X } from "@lucide/svelte";
    import { tick } from "svelte";

    let { wallet }: { wallet: string } = $props();

    let editing = $state(false);
    let draft = $state("");
    let input = $state<HTMLInputElement>();
    let savedLabel = $derived(developerLabelsStore.getLabel(wallet));

    const savedLabelClass = [
        "border-indigo-400/35 bg-indigo-400/12 text-indigo-200",
        "hover:border-indigo-300/50 hover:bg-indigo-400/18",
    ].join(" ");
    const emptyLabelClass = [
        "border-dashed border-white/10 bg-white/[0.025] text-slate-500",
        "hover:border-indigo-400/30 hover:bg-indigo-400/[0.07] hover:text-indigo-300",
    ].join(" ");

    function startEditing(event: MouseEvent): void {
        event.stopPropagation();
        draft = savedLabel;
        editing = true;
        void tick().then(() => {
            input?.focus();
            input?.select();
        });
    }

    function saveDraft(): void {
        developerLabelsStore.setLabel(wallet, draft);
    }

    function finishEditing(): void {
        saveDraft();
        editing = false;
    }

    function handleKeydown(event: KeyboardEvent): void {
        event.stopPropagation();
        if (event.key === "Enter") {
            event.preventDefault();
            finishEditing();
        } else if (event.key === "Escape") {
            event.preventDefault();
            editing = false;
        }
    }

    function clearLabel(event: MouseEvent): void {
        event.stopPropagation();
        developerLabelsStore.removeLabel(wallet);
        editing = false;
    }
</script>

{#if wallet.trim()}
    {#if editing}
        <span
            class={[
                "flex h-7 min-w-0 items-center gap-1 rounded-lg border",
                "border-indigo-400/35 bg-indigo-400/10 p-0.5 pl-2",
                "shadow-[0_0_0_1px_rgba(129,140,248,0.05)]",
            ]}
            data-testid="developer-label-editor"
        >
            <Tag
                class="shrink-0 text-indigo-300"
                size={12}
                aria-hidden="true"
            />
            <input
                class={[
                    "h-6 w-28 min-w-0 border-0 bg-transparent p-0 text-[0.68rem]",
                    "font-semibold text-indigo-100 outline-none placeholder:text-indigo-300/45",
                ]}
                bind:this={input}
                bind:value={draft}
                maxlength="48"
                placeholder="Name this dev"
                aria-label={`Label for developer wallet ${wallet}`}
                autocomplete="off"
                oninput={saveDraft}
                onblur={finishEditing}
                onkeydown={handleKeydown}
                onclick={(event) => event.stopPropagation()}
            />
            {#if savedLabel}
                <button
                    class={[
                        "inline-flex size-6 shrink-0 items-center justify-center rounded-md",
                        "text-indigo-300/65 transition-colors hover:bg-red-500/15",
                        "hover:text-red-300 focus-visible:ring-1 focus-visible:ring-red-300",
                        "focus-visible:outline-none",
                    ]}
                    type="button"
                    title="Remove developer label"
                    aria-label="Remove developer label"
                    onmousedown={(event) => event.preventDefault()}
                    onclick={clearLabel}
                >
                    <X size={12} aria-hidden="true" />
                </button>
            {:else}
                <button
                    class={[
                        "inline-flex size-6 shrink-0 items-center justify-center rounded-md",
                        "text-indigo-300 transition-colors hover:bg-indigo-400/15",
                        "focus-visible:ring-1 focus-visible:ring-indigo-300",
                        "focus-visible:outline-none",
                    ]}
                    type="button"
                    title="Finish editing"
                    aria-label="Finish editing developer label"
                    onmousedown={(event) => event.preventDefault()}
                    onclick={(event) => {
                        event.stopPropagation();
                        finishEditing();
                    }}
                >
                    <Check size={12} aria-hidden="true" />
                </button>
            {/if}
        </span>
    {:else}
        <button
            class={[
                "inline-flex h-7 max-w-40 min-w-0 shrink-0 items-center gap-1",
                "rounded-lg border px-2 text-[0.68rem] font-semibold",
                "transition-[background-color,border-color,color,box-shadow]",
                "focus-visible:ring-2 focus-visible:ring-indigo-400",
                "focus-visible:outline-none",
                savedLabel ? savedLabelClass : emptyLabelClass,
            ]}
            type="button"
            title={savedLabel
                ? `${savedLabel} — click to edit`
                : `Add a label for ${wallet}`}
            aria-label={savedLabel
                ? `Edit developer label ${savedLabel}`
                : "Add developer label"}
            onclick={startEditing}
        >
            <Tag size={11} aria-hidden="true" />
            <span class="truncate">{savedLabel || "Add dev label"}</span>
        </button>
    {/if}
{/if}
