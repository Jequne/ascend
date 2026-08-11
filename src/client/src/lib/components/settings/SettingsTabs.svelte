<script lang="ts">
    import type { SettingsTab } from "$lib/types";

    export let activeTab: SettingsTab;
    export let onSelect: (tab: SettingsTab) => void;

    const tabs: Array<{
        id: SettingsTab;
        title: string;
        description: string;
    }> = [
        {
            id: "filters",
            title: "Filters",
            description: "Token selection rules",
        },
        {
            id: "blacklist",
            title: "Blacklist",
            description: "Hidden wallets and names",
        },
        {
            id: "transfer",
            title: "Import / Export",
            description: "Move your configuration",
        },
    ];

    let buttons: HTMLButtonElement[] = [];

    function selectAt(index: number): void {
        const normalizedIndex = (index + tabs.length) % tabs.length;
        const tab = tabs[normalizedIndex];
        const button = buttons[normalizedIndex];

        if (tab && button) {
            onSelect(tab.id);
            button.focus();
        }
    }

    function handleKeydown(event: KeyboardEvent, index: number): void {
        if (event.key === "ArrowLeft") {
            event.preventDefault();
            selectAt(index - 1);
        } else if (event.key === "ArrowRight") {
            event.preventDefault();
            selectAt(index + 1);
        } else if (event.key === "Home") {
            event.preventDefault();
            selectAt(0);
        } else if (event.key === "End") {
            event.preventDefault();
            selectAt(tabs.length - 1);
        }
    }
</script>

<div
    class="grid grid-cols-3 gap-1.5 border-y border-white/[0.06] bg-black/10 px-3 py-2"
    role="tablist"
    aria-label="Settings sections"
>
    {#each tabs as tab, index (tab.id)}
        <button
            class="focus-visible:ring-accent-purple focus-visible:ring-offset-canvas flex h-14 min-w-0 flex-col items-center justify-center rounded-lg border px-1.5 text-center transition-[background-color,border-color,color,box-shadow] duration-150 focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:outline-none {activeTab ===
            tab.id
                ? 'border-accent-blue/40 bg-accent-blue/15 text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]'
                : 'text-muted hover:text-foreground border-transparent bg-white/[0.025] hover:border-white/10 hover:bg-white/[0.05]'}"
            type="button"
            role="tab"
            id={`settings-tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`settings-panel-${tab.id}`}
            tabindex={activeTab === tab.id ? 0 : -1}
            bind:this={buttons[index]}
            onclick={() => onSelect(tab.id)}
            onkeydown={(event) => handleKeydown(event, index)}
        >
            <span class="text-[0.72rem] leading-tight font-bold"
                >{tab.title}</span
            >
            <span
                class="mt-1 line-clamp-2 text-[0.58rem] leading-[1.15] text-slate-500"
                >{tab.description}</span
            >
        </button>
    {/each}
</div>
