<script>
    import { createEventDispatcher } from "svelte";

    export let value = "";
    export let type = "text";
    export let placeholder = "";
    export let disabled = false;
    export let ariaLabel = "Text input";

    const dispatch = createEventDispatcher();

    function handleKeydown(event) {
        if (event.key === "Enter") {
            dispatch("enter", event);
        }
    }
</script>

<input
    class="text-input"
    {type}
    {placeholder}
    bind:value
    {disabled}
    aria-label={ariaLabel}
    onkeydown={handleKeydown}
/>

<style>
    .text-input {
        width: 100%;
        padding: 12px;
        background-color: #1e2029;
        border: 1px solid #333;
        border-radius: 8px;
        color: #fff;
        text-align: center;
        outline: none;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }

    .text-input:focus {
        border-color: #3f4494;
    }

    .text-input:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
</style>
