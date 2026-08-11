<script lang="ts">
    import {
        DEFAULT_FILTERS,
        LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    } from "$lib/config/constants";
    import type { FeesMode, FilterSettings, Terminal } from "$lib/types";

    export let settings: FilterSettings;

    function inputValue(event: Event): string {
        return (event.currentTarget as HTMLInputElement | HTMLSelectElement)
            .value;
    }

    function inputNumber(event: Event): number {
        return Number(inputValue(event));
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

    function rangeBackground(): string {
        const min = DEFAULT_FILTERS.minDevHoldsPercent;
        const minPercent =
            ((settings.minDevHoldsPercent - min) / (100 - min)) * 100;
        const maxPercent =
            ((settings.maxDevHoldsPercent - min) / (100 - min)) * 100;

        return `linear-gradient(to right, rgba(37, 99, 235, 0.18) 0%, rgba(37, 99, 235, 0.18) ${minPercent}%, rgba(59, 130, 246, 0.98) ${minPercent}%, rgba(59, 130, 246, 0.98) ${maxPercent}%, rgba(37, 99, 235, 0.24) ${maxPercent}%, rgba(37, 99, 235, 0.24) 100%)`;
    }
</script>

<div class="grid gap-2.5 p-3 sm:grid-cols-2">
    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)] sm:col-span-2"
    >
        <div class="mb-2.5 flex items-baseline justify-between gap-2">
            <h3
                class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
            >
                Dev holds range
            </h3>
            <span class="text-[0.64rem] whitespace-nowrap text-slate-500"
                >{settings.minDevHoldsPercent}% — {settings.maxDevHoldsPercent}%</span
            >
        </div>

        <div class="range-wrap relative mt-1 h-[30px] w-full min-w-0">
            <input
                class="range-input range-min"
                aria-label="Minimum developer holds percent"
                type="range"
                min={DEFAULT_FILTERS.minDevHoldsPercent}
                max="100"
                step="0.1"
                value={settings.minDevHoldsPercent}
                style:background={rangeBackground()}
                oninput={updateMinDev}
            />
            <input
                class="range-input range-max"
                aria-label="Maximum developer holds percent"
                type="range"
                min={DEFAULT_FILTERS.minDevHoldsPercent}
                max="100"
                step="0.1"
                value={settings.maxDevHoldsPercent}
                style:background={rangeBackground()}
                oninput={updateMaxDev}
            />
        </div>
    </section>

    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)]"
    >
        <div class="mb-2.5">
            <h3
                class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
            >
                Trading filter
            </h3>
            <p class="mt-1 mb-0 text-[0.64rem] text-slate-500">
                Core thresholds
            </p>
        </div>

        <div class="flex flex-col gap-2.5">
            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Min migration %
                <input
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-black/20 px-2.5 outline-none focus:ring-2"
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={settings.minMigrationPercent}
                    oninput={(event) =>
                        update("minMigrationPercent", inputNumber(event))}
                />
            </label>

            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Last Tokens Fees Mode
                <select
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-[#0c0f18] px-2.5 outline-none focus:ring-2"
                    value={settings.feesMode}
                    onchange={(event) =>
                        update("feesMode", inputValue(event) as FeesMode)}
                >
                    <option value="avg">avg</option>
                    <option value="total">total</option>
                    <option value="fixed">fixed</option>
                </select>
            </label>

            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Min last token fees
                <input
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-black/20 px-2.5 outline-none focus:ring-2"
                    type="number"
                    min="0"
                    step="0.1"
                    value={settings.minLastTokenFees}
                    oninput={(event) =>
                        update("minLastTokenFees", inputNumber(event))}
                />
                <span class="text-muted text-[0.6rem] leading-snug font-normal">
                    Low-fee tokens older than {LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS}
                    days are excluded from the fee calculation.
                </span>
            </label>
        </div>
    </section>

    <section
        class="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.025)]"
    >
        <div class="mb-2.5">
            <h3
                class="text-foreground m-0 text-xs font-bold tracking-[0.02em] uppercase"
            >
                Last token override
            </h3>
            <p class="mt-1 mb-0 text-[0.64rem] text-slate-500">
                ATH and terminal
            </p>
        </div>

        <div class="flex flex-col gap-2.5">
            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Min last token ATH mcap
                <input
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-black/20 px-2.5 outline-none focus:ring-2"
                    type="number"
                    min="0"
                    step="1"
                    value={settings.minLastTokenAthMcap}
                    oninput={(event) =>
                        update("minLastTokenAthMcap", inputNumber(event))}
                />
            </label>

            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Required last tokens
                <input
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-black/20 px-2.5 outline-none focus:ring-2"
                    type="number"
                    min="0"
                    max="3"
                    step="1"
                    value={settings.lastTokensRequiredCount}
                    oninput={(event) =>
                        update("lastTokensRequiredCount", inputNumber(event))}
                />
                <span class="text-muted text-[0.6rem] leading-snug font-normal">
                    Set to 0 to disable the last-token override.
                </span>
            </label>

            <label
                class="flex flex-col gap-1 text-xs font-semibold text-slate-200"
            >
                Token terminal
                <select
                    class="text-foreground focus:border-accent-blue/50 focus:ring-accent-blue/15 h-9 rounded-lg border border-white/10 bg-[#0c0f18] px-2.5 outline-none focus:ring-2"
                    value={settings.terminal}
                    onchange={(event) =>
                        update("terminal", inputValue(event) as Terminal)}
                >
                    <option value="axiom">Axiom</option>
                    <option value="gmgn">GMGN</option>
                </select>
            </label>
        </div>
    </section>
</div>

<style>
    .range-input {
        position: absolute;
        inset-inline: 0;
        width: 100%;
        height: 30px;
        margin: 0;
        padding: 0;
        appearance: none;
        background: transparent;
        cursor: pointer;
        outline: none;
    }

    .range-input::-webkit-slider-runnable-track {
        height: 8px;
        border-radius: 999px;
        background: transparent;
    }

    .range-input::-moz-range-track {
        height: 8px;
        border-radius: 999px;
        background: transparent;
    }

    .range-input::-webkit-slider-thumb {
        width: 19px;
        height: 19px;
        margin-top: -5px;
        appearance: none;
        border: 2px solid rgba(239, 246, 255, 0.96);
        border-radius: 50%;
        background: linear-gradient(180deg, #93c5fd, #2563eb);
        box-shadow:
            0 0 0 4px rgba(59, 130, 246, 0.16),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-input::-moz-range-thumb {
        width: 19px;
        height: 19px;
        border: 2px solid rgba(239, 246, 255, 0.96);
        border-radius: 50%;
        background: linear-gradient(180deg, #93c5fd, #2563eb);
        box-shadow:
            0 0 0 4px rgba(59, 130, 246, 0.16),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-input:focus-visible::-webkit-slider-thumb {
        box-shadow:
            0 0 0 5px rgba(96, 165, 250, 0.2),
            0 0 0 9px rgba(37, 99, 235, 0.12),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-input:focus-visible::-moz-range-thumb {
        box-shadow:
            0 0 0 5px rgba(96, 165, 250, 0.2),
            0 0 0 9px rgba(37, 99, 235, 0.12),
            0 8px 18px rgba(0, 0, 0, 0.35);
    }

    .range-min {
        z-index: 2;
    }

    .range-max {
        z-index: 1;
    }
</style>
