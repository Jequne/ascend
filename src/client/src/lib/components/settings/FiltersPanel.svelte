<script lang="ts">
    import Disclosure from "$lib/components/settings/Disclosure.svelte";
    import SelectMenu from "$lib/components/settings/SelectMenu.svelte";
    import SwitchControl from "$lib/components/settings/SwitchControl.svelte";
    import {
        DEFAULT_FILTERS,
        LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    } from "$lib/config/constants";
    import type { FilterSettings } from "$lib/types";
    import { Gauge, ShieldCheck, SlidersHorizontal } from "@lucide/svelte";

    export let settings: FilterSettings;

    const feeModeOptions = [
        {
            value: "avg",
            label: "Average fees",
            description: "Compare the average across recent tokens",
        },
        {
            value: "total",
            label: "Total fees",
            description: "Compare the combined fee amount",
        },
        {
            value: "fixed",
            label: "Every token",
            description: "Require each recent token to pass",
        },
    ] as const;
    const rangeMarks = Array.from({ length: 11 }, (_, index) => index * 10);

    let previousRequiredCount = Math.max(
        1,
        settings.lastTokensRequiredCount || 1,
    );

    $: overrideEnabled = settings.lastTokensRequiredCount > 0;
    $: if (settings.lastTokensRequiredCount > 0) {
        previousRequiredCount = settings.lastTokensRequiredCount;
    }

    function inputNumber(event: Event): number {
        return Number((event.currentTarget as HTMLInputElement).value);
    }

    function update<K extends keyof FilterSettings>(
        key: K,
        value: FilterSettings[K],
    ): void {
        settings = { ...settings, [key]: value };
    }

    function updateMinDev(event: Event): void {
        update(
            "minDevHoldsPercent",
            Math.min(inputNumber(event), settings.maxDevHoldsPercent),
        );
    }

    function updateMaxDev(event: Event): void {
        update(
            "maxDevHoldsPercent",
            Math.max(inputNumber(event), settings.minDevHoldsPercent),
        );
    }

    function setOverrideEnabled(enabled: boolean): void {
        update(
            "lastTokensRequiredCount",
            enabled ? Math.max(1, previousRequiredCount) : 0,
        );
    }

    function updateRequiredTokens(event: Event): void {
        const input = event.currentTarget as HTMLInputElement;
        if (!input.value) return;
        update("lastTokensRequiredCount", Number(input.value));
    }

    function rangeStart(): number {
        return Math.max(0, Math.min(100, settings.minDevHoldsPercent));
    }

    function rangeEnd(): number {
        return Math.max(0, Math.min(100, settings.maxDevHoldsPercent));
    }

    function formatPercent(value: number): string {
        return Number.isInteger(value) ? String(value) : value.toFixed(1);
    }
</script>

<div class="flex flex-col gap-2.5 p-3">
    <section
        class="rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))] p-3 shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]"
    >
        <div class="mb-2.5 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
                <span
                    class="text-accent-blue bg-accent-blue/10 flex size-7 items-center justify-center rounded-lg border border-blue-400/15"
                >
                    <Gauge size={15} aria-hidden="true" />
                </span>
                <div>
                    <h3
                        class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                    >
                        Developer holds
                    </h3>
                    <p class="text-muted mt-0.5 mb-0 text-[0.62rem]">
                        Accept tokens inside this ownership range.
                    </p>
                </div>
            </div>
            <output
                class="border-accent-blue/20 bg-accent-blue/10 shrink-0 rounded-full border px-2 py-1 text-[0.64rem] font-bold text-blue-200"
            >
                {formatPercent(settings.minDevHoldsPercent)}–{formatPercent(
                    settings.maxDevHoldsPercent,
                )}%
            </output>
        </div>

        <div
            class="dev-range relative mt-1 h-8 w-full min-w-0"
            style={`--range-start: ${rangeStart()}%; --range-end: ${rangeEnd()}%;`}
        >
            <div
                class="absolute top-1/2 right-1 left-1 h-[7px] -translate-y-1/2 overflow-hidden rounded-full bg-white/[0.09] shadow-[inset_0_1px_2px_rgba(0,0,0,0.45)]"
                aria-hidden="true"
            >
                <span class="range-selection absolute inset-y-0 rounded-full"
                ></span>
            </div>
            <input
                class="range-input range-min"
                id="minimum-developer-holds"
                name="minimumDeveloperHolds"
                aria-label="Minimum developer holds percent"
                type="range"
                min={DEFAULT_FILTERS.minDevHoldsPercent}
                max="100"
                step="0.1"
                value={settings.minDevHoldsPercent}
                oninput={updateMinDev}
            />
            <input
                class="range-input range-max"
                id="maximum-developer-holds"
                name="maximumDeveloperHolds"
                aria-label="Maximum developer holds percent"
                type="range"
                min={DEFAULT_FILTERS.minDevHoldsPercent}
                max="100"
                step="0.1"
                value={settings.maxDevHoldsPercent}
                oninput={updateMaxDev}
            />
        </div>
        <div
            class="grid grid-cols-11 px-0.5 text-center text-[0.55rem] text-slate-500"
            aria-hidden="true"
        >
            {#each rangeMarks as mark (mark)}
                <span>{mark}</span>
            {/each}
        </div>
    </section>

    <section
        class="rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))] shadow-[0_8px_24px_rgba(0,0,0,0.16),inset_0_1px_0_rgba(255,255,255,0.035)]"
        aria-labelledby="filters-heading"
    >
        <div class="flex items-start gap-2.5 border-b border-white/[0.06] p-3">
            <span
                class="text-accent-purple bg-accent-purple/10 flex size-7 shrink-0 items-center justify-center rounded-lg border border-indigo-400/15"
            >
                <SlidersHorizontal size={15} aria-hidden="true" />
            </span>
            <div>
                <h3
                    id="filters-heading"
                    class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                >
                    Filters
                </h3>
                <p class="text-muted mt-0.5 mb-0 text-[0.62rem] leading-snug">
                    Core rules must pass together. The performance override is
                    optional and evaluated separately.
                </p>
            </div>
        </div>

        <div class="grid gap-3 p-3 min-[560px]:grid-cols-2">
            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Minimum migration rate
                <div class="relative">
                    <input
                        class="text-foreground focus:border-accent-blue/55 focus:ring-accent-blue/15 h-9 w-full rounded-[10px] border border-white/10 bg-[#11141d] px-2.5 pr-8 transition-colors outline-none focus:ring-2"
                        id="minimum-migration-rate"
                        name="minimumMigrationRate"
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={settings.minMigrationPercent}
                        oninput={(event) =>
                            update("minMigrationPercent", inputNumber(event))}
                    />
                    <span
                        class="text-muted pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-[0.65rem]"
                        >%</span
                    >
                </div>
                <span class="text-muted text-[0.6rem] leading-snug font-normal">
                    Minimum share of the developer's tokens that migrated.
                </span>
            </label>

            <div class="flex flex-col gap-1">
                <span class="text-xs font-semibold text-slate-200"
                    >Recent-token fee mode</span
                >
                <SelectMenu
                    id="fees-mode"
                    label="Recent-token fee mode"
                    options={feeModeOptions}
                    bind:value={settings.feesMode}
                />
                <span class="text-muted text-[0.6rem] leading-snug">
                    Choose how fees from recent deployments are compared.
                </span>
            </div>

            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200 min-[560px]:col-span-2"
            >
                Minimum recent-token fees
                <div class="relative">
                    <input
                        class="text-foreground focus:border-accent-blue/55 focus:ring-accent-blue/15 h-9 w-full rounded-[10px] border border-white/10 bg-[#11141d] px-2.5 pr-10 transition-colors outline-none focus:ring-2"
                        id="minimum-recent-token-fees"
                        name="minimumRecentTokenFees"
                        type="number"
                        min="0"
                        step="0.1"
                        value={settings.minLastTokenFees}
                        oninput={(event) =>
                            update("minLastTokenFees", inputNumber(event))}
                    />
                    <span
                        class="text-muted pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-[0.62rem]"
                        >SOL</span
                    >
                </div>
            </label>

            <div class="min-[560px]:col-span-2">
                <Disclosure label="How recent-token fee filtering works">
                    <p class="m-0">
                        Average compares the mean, Total compares the combined
                        amount, and Every token requires each recent token to
                        meet the threshold. Low-fee tokens older than
                        {LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS} days are excluded.
                    </p>
                </Disclosure>
            </div>
        </div>

        <div class="border-t border-white/[0.07] p-3">
            <div class="flex items-center justify-between gap-3">
                <div class="flex min-w-0 items-start gap-2.5">
                    <span
                        class="text-success bg-success/10 flex size-7 shrink-0 items-center justify-center rounded-lg border border-emerald-400/15"
                    >
                        <ShieldCheck size={15} aria-hidden="true" />
                    </span>
                    <div>
                        <h4 class="text-foreground m-0 text-xs font-bold">
                            Previous-token performance override
                        </h4>
                        <p
                            class="text-muted mt-0.5 mb-0 text-[0.62rem] leading-snug"
                        >
                            Accept a token when enough previous deployments hit
                            the target ATH, even if migration is below the core
                            threshold.
                        </p>
                    </div>
                </div>
                <SwitchControl
                    checked={overrideEnabled}
                    label="Enable previous-token performance override"
                    onChange={setOverrideEnabled}
                />
            </div>

            {#if overrideEnabled}
                <div
                    class="mt-3 grid gap-3 rounded-[10px] border border-emerald-400/10 bg-emerald-400/[0.035] p-3 min-[560px]:grid-cols-2"
                >
                    <label
                        class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
                    >
                        Minimum previous-token ATH market cap
                        <div class="relative">
                            <input
                                class="text-foreground focus:border-accent-blue/55 focus:ring-accent-blue/15 h-9 w-full rounded-[10px] border border-white/10 bg-[#11141d] px-2.5 pr-10 transition-colors outline-none focus:ring-2"
                                id="minimum-previous-token-ath-market-cap"
                                name="minimumPreviousTokenAthMarketCap"
                                type="number"
                                min="0"
                                step="1"
                                value={settings.minLastTokenAthMcap}
                                oninput={(event) =>
                                    update(
                                        "minLastTokenAthMcap",
                                        inputNumber(event),
                                    )}
                            />
                            <span
                                class="text-muted pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-[0.62rem]"
                                >USD</span
                            >
                        </div>
                    </label>

                    <label
                        class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
                    >
                        Required previous tokens
                        <input
                            class="text-foreground focus:border-accent-blue/55 focus:ring-accent-blue/15 h-9 rounded-[10px] border border-white/10 bg-[#11141d] px-2.5 transition-colors outline-none focus:ring-2"
                            id="required-previous-tokens"
                            name="requiredPreviousTokens"
                            type="number"
                            min="1"
                            max="3"
                            step="1"
                            value={settings.lastTokensRequiredCount}
                            oninput={updateRequiredTokens}
                        />
                    </label>
                </div>
            {/if}
        </div>
    </section>
</div>

<style>
    .range-selection {
        left: var(--range-start);
        right: calc(100% - var(--range-end));
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
    }

    .range-input {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 32px;
        margin: 0;
        padding: 0;
        appearance: none;
        background: transparent;
        pointer-events: none;
        outline: none;
    }

    .range-input::-webkit-slider-runnable-track {
        height: 7px;
        background: transparent;
    }

    .range-input::-moz-range-track {
        height: 7px;
        background: transparent;
    }

    .range-input::-webkit-slider-thumb {
        width: 18px;
        height: 18px;
        margin-top: -5.5px;
        appearance: none;
        border: 2px solid rgba(239, 246, 255, 0.98);
        border-radius: 50%;
        background: #3b82f6;
        box-shadow:
            0 0 0 3px rgba(59, 130, 246, 0.16),
            0 4px 10px rgba(0, 0, 0, 0.45);
        pointer-events: auto;
        cursor: grab;
    }

    .range-input::-moz-range-thumb {
        width: 15px;
        height: 15px;
        border: 2px solid rgba(239, 246, 255, 0.98);
        border-radius: 50%;
        background: #3b82f6;
        box-shadow:
            0 0 0 3px rgba(59, 130, 246, 0.16),
            0 4px 10px rgba(0, 0, 0, 0.45);
        pointer-events: auto;
        cursor: grab;
    }

    .range-input:active::-webkit-slider-thumb {
        cursor: grabbing;
    }

    .range-input:focus-visible::-webkit-slider-thumb {
        box-shadow:
            0 0 0 4px rgba(96, 165, 250, 0.22),
            0 0 0 8px rgba(37, 99, 235, 0.12),
            0 4px 10px rgba(0, 0, 0, 0.45);
    }

    .range-input:focus-visible::-moz-range-thumb {
        box-shadow:
            0 0 0 4px rgba(96, 165, 250, 0.22),
            0 0 0 8px rgba(37, 99, 235, 0.12),
            0 4px 10px rgba(0, 0, 0, 0.45);
    }

    .range-min {
        z-index: 2;
    }

    .range-max {
        z-index: 3;
    }
</style>
