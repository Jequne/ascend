<script>
    import { createEventDispatcher } from "svelte";

    export let label = "Submit";
    export let loadingLabel = "Loading...";
    export let loading = false;
    export let disabled = false;

    const dispatch = createEventDispatcher();

    function handleClick(event) {
        dispatch("click", event);
    }
</script>

<button class="primary-button" {disabled} onclick={handleClick}>
    {loading ? loadingLabel : label}
</button>

<style>
    .primary-button {
        width: 100%;
        background-color: #3f4494;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        padding: 12px;
        color: #fff;
        font-weight: 600;
        transition: background-color 0.2s;
    }

    .primary-button:hover:not(:disabled) {
        background-color: #4c52ab;
    }

    .primary-button:disabled {
        background-color: #2a2d64;
        color: #6b7280;
        cursor: not-allowed;
    }
</style>
