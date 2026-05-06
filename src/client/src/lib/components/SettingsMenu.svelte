<script>
    import { feedState } from "$lib/core/tokenFeed/store.svelte.js";

    /**
     * @typedef {Object} Props
     * @property {function} onClose
     */

    /** @type {Props} */
    let { onClose } = $props();

    // Инициализируем локальное состояние из глобального,
    // если значений нет (null), ставим крайние 0 и 100
    let minDev = $state(feedState.filters.minDevHoldsPercent ?? 0.1);
    let maxDev = $state(feedState.filters.maxDevHoldsPercent ?? 100);

    function handleMinChange(e) {
        let val = parseFloat(e.target.value);
        // Не даем минимальному ползунку зайти за максимальный
        if (val > maxDev) val = maxDev;
        minDev = val;
    }

    function handleMaxChange(e) {
        let val = parseFloat(e.target.value);
        // Не даем максимальному ползунку зайти за минимальный
        if (val < minDev) val = minDev;
        maxDev = val;
    }

    function applyFilters() {
        feedState.updateFilters({
            // Передаем значения. Можно сохранить и null, если выбран фулл диапазон (0.1-100),
            // но будем сохранять как есть, чтобы фильтр работал явно.
            minDevHoldsPercent:
                minDev === 0.1 && maxDev === 100 ? null : minDev,
            maxDevHoldsPercent:
                minDev === 0.1 && maxDev === 100 ? null : maxDev,
        });
        onClose();
    }

    function resetFilters() {
        minDev = 0.1;
        maxDev = 100;
        // Можем сразу применить, или просто сбросить ползунки
    }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={onClose}>
    <div class="modal-content" onclick={(e) => e.stopPropagation()}>
        <div class="modal-header">
            <h2>Settings</h2>
            <button class="close-button" onclick={onClose}>&times;</button>
        </div>

        <div class="modal-body">
            <div class="setting-group">
                <div class="setting-header">
                    <span class="label-text"
                        >Dev Holds</span
                    >
                    <span class="value-display">{minDev}% — {maxDev}%</span>
                </div>

                <div class="range-container">
                    <div class="track"></div>
                    <div
                        class="track-active"
                        style="left: {minDev}%; width: {maxDev - minDev}%;"
                    ></div>
                    <input
                        type="range"
                        min="0.1"
                        max="100"
                        step="0.1"
                        value={minDev}
                        oninput={handleMinChange}
                    />
                    <input
                        type="range"
                        min="0.1"
                        max="100"
                        step="0.1"
                        value={maxDev}
                        oninput={handleMaxChange}
                    />
                </div>
                <div class="range-labels">
                    <span>0.1%</span>
                    <span>100%</span>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="reset-button" onclick={resetFilters}>Reset</button
            >
            <button class="apply-button" onclick={applyFilters}
                >Save</button
            >
        </div>
    </div>
</div>

<style>
    .modal-overlay {
        position: fixed;
        inset: 0;
        background-color: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 20px;
    }

    .modal-content {
        background-color: #161922;
        border: 1px solid #232733;
        border-radius: 12px;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        color: #e5e7eb;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #2e3547;
    }

    .modal-header h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #f3f4f6;
    }

    .close-button {
        background: transparent;
        border: none;
        color: #9ca3af;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
        transition: color 0.2s;
    }

    .close-button:hover {
        color: #ef4444;
    }

    .modal-body {
        padding: 24px 20px;
    }

    .setting-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .setting-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .label-text {
        font-size: 14px;
        font-weight: 500;
        color: #9ca3af;
    }

    .value-display {
        font-size: 14px;
        font-weight: 600;
        color: #60a5fa;
        background: rgba(59, 130, 246, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
    }

    .range-container {
        position: relative;
        width: 100%;
        height: 24px;
        display: flex;
        align-items: center;
        margin-top: 8px;
    }

    .track {
        position: absolute;
        width: 100%;
        height: 6px;
        background-color: #2e3547;
        border-radius: 4px;
        z-index: 1;
    }

    .track-active {
        position: absolute;
        height: 6px;
        background-color: #3b82f6; /* Синий цвет фильтра */
        border-radius: 4px;
        z-index: 2;
    }

    input[type="range"] {
        position: absolute;
        width: 100%;
        appearance: none;
        background: none;
        pointer-events: none;
        z-index: 3;
        margin: 0;
    }

    input[type="range"]::-webkit-slider-thumb {
        pointer-events: all;
        appearance: none;
        width: 18px;
        height: 18px;
        background-color: #f3f4f6;
        border: 2px solid #3b82f6;
        border-radius: 50%;
        cursor: grab;
        transition: transform 0.1s;
    }

    input[type="range"]::-webkit-slider-thumb:hover {
        transform: scale(1.1);
    }

    input[type="range"]::-webkit-slider-thumb:active {
        cursor: grabbing;
        transform: scale(1.1);
        background-color: #60a5fa;
    }

    input[type="range"]::-moz-range-thumb {
        pointer-events: all;
        width: 18px;
        height: 18px;
        background-color: #f3f4f6;
        border: 2px solid #3b82f6;
        border-radius: 50%;
        cursor: grab;
        transition: transform 0.1s;
    }

    input[type="range"]::-moz-range-thumb:hover {
        transform: scale(1.1);
    }

    input[type="range"]::-moz-range-thumb:active {
        cursor: grabbing;
        transform: scale(1.1);
        background-color: #60a5fa;
    }

    .range-labels {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #6b7280;
    }

    .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 16px 20px;
        border-top: 1px solid #2e3547;
    }

    .reset-button,
    .apply-button {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }

    .reset-button {
        background: transparent;
        color: #9ca3af;
        border: 1px solid #2e3547;
    }

    .reset-button:hover {
        background: #2e3547;
        color: #e5e7eb;
    }

    .apply-button {
        background: #3b82f6;
        color: #ffffff;
        border: 1px solid #3b82f6;
    }

    .apply-button:hover {
        background: #2563eb;
        border-color: #2563eb;
    }
</style>
