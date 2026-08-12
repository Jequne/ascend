<script lang="ts">
    import type { TokenFeed } from "$lib/types";
    import { CircleCheck, Database, TrendingUp } from "@lucide/svelte";

    export let feed: TokenFeed;

    $: migratedRatio = feed.all_tokens_count
        ? ((feed.migrated_tokens_count / feed.all_tokens_count) * 100).toFixed(
              1,
          )
        : "0";
</script>

<div class="mt-0.5 flex flex-col gap-1.5">
    <div class="flex w-full items-center gap-2">
        <div class="flex min-w-0 flex-wrap items-center gap-1.5">
            {#each feed.indicators as indicator (indicator)}
                <span
                    class="rounded border px-1.5 py-0.5 text-[0.7rem] font-semibold whitespace-nowrap uppercase {indicator
                        .trim()
                        .toLowerCase() === 'last tokens'
                        ? 'border-[#d6b94a]/35 bg-[#d6b94a]/15 text-[#e2ca67]'
                        : 'text-success border-emerald-500/30 bg-emerald-500/15'}"
                    >{indicator}</span
                >
            {/each}
            <span
                class="rounded border border-purple-500/30 bg-purple-500/15 px-1.5 py-0.5 text-[0.7rem] font-semibold whitespace-nowrap text-purple-400 uppercase"
                >{feed.blockchain || "sol"}</span
            >
        </div>

        {#if feed.dev_holds_percent !== null}
            <span
                class="ml-auto inline-flex h-6 shrink-0 items-center rounded border border-amber-500/30 bg-amber-500/15 px-1.5 text-[0.7rem] font-semibold tracking-[0.02em] whitespace-nowrap text-amber-400 shadow-[0_2px_4px_rgba(0,0,0,0.1)]"
            >
                DH: {feed.dev_holds_percent.toFixed(1)}%
            </span>
        {/if}
    </div>

    <div
        class="flex flex-wrap items-center gap-2 rounded-lg border border-white/[0.045] bg-black/10 px-2 py-1.5 text-[0.8rem] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]"
    >
        <span
            class="text-foreground inline-flex items-center gap-1"
            title="Total Tokens"
        >
            <Database size={10} strokeWidth={2} aria-hidden="true" />
            {feed.all_tokens_count} tokens
        </span>
        <span class="size-1 rounded-full bg-white/20" aria-hidden="true"></span>
        <span
            class="text-success inline-flex items-center gap-1"
            title="Migrated Tokens"
        >
            <CircleCheck size={10} strokeWidth={2} aria-hidden="true" />
            {feed.migrated_tokens_count} migrated
        </span>
        <span class="size-1 rounded-full bg-white/20" aria-hidden="true"></span>
        <span
            class="text-accent-blue inline-flex items-center gap-1 font-medium"
            title="Migration Rate"
        >
            <TrendingUp size={10} strokeWidth={2} aria-hidden="true" />
            {migratedRatio}% rate
        </span>
        {#if feed.is_migrated}
            <span title="Migrated" aria-label="Migrated">
                <CircleCheck size={10} strokeWidth={2} aria-hidden="true" />
            </span>
        {/if}
    </div>
</div>
