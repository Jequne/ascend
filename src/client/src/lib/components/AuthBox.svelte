<script lang="ts">
    import { authStore } from "$lib/stores/auth.svelte";
    import { KeyRound } from "@lucide/svelte";

    let key = $state("");
    let isActivating = $state(false);
    let errorMessage = $state("");

    async function activate(event: SubmitEvent) {
        event.preventDefault();
        if (!key.trim()) {
            errorMessage = "Please enter a key.";
            return;
        }

        isActivating = true;
        errorMessage = "";

        const success = await authStore.login(key);

        if (!success) {
            errorMessage = "Invalid key. Please try again.";
        }
        isActivating = false;
    }
</script>

<section
    class="mx-3 w-full max-w-[420px] overflow-hidden rounded-2xl border border-white/[0.08] bg-[linear-gradient(145deg,rgba(35,38,50,0.98),rgba(23,24,33,0.99))] shadow-[0_22px_60px_rgba(0,0,0,0.38),inset_0_1px_0_rgba(255,255,255,0.04)]"
    aria-labelledby="license-heading"
>
    <div class="flex items-start gap-3 border-b border-white/[0.07] p-4">
        <span
            class="text-accent-purple bg-accent-purple/10 flex size-10 shrink-0 items-center justify-center rounded-xl border border-indigo-400/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)]"
        >
            <KeyRound size={20} aria-hidden="true" />
        </span>
        <div>
            <h1
                id="license-heading"
                class="text-foreground m-0 text-base font-bold"
            >
                License Required
            </h1>
            <p class="text-muted mt-1 mb-0 text-sm leading-relaxed">
                Enter your license key to activate the application.
            </p>
        </div>
    </div>

    <form class="flex flex-col gap-3 p-4" onsubmit={activate}>
        <label
            class="flex flex-col gap-1.5 text-sm font-semibold text-slate-200"
        >
            License key
            <input
                class="text-foreground focus:border-accent-purple/60 focus:ring-accent-purple/15 h-11 rounded-[10px] border border-white/10 bg-[#11141d] px-3 font-mono text-sm outline-none placeholder:text-slate-600 focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
                type="text"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                bind:value={key}
                disabled={isActivating}
                autocomplete="off"
            />
        </label>
        {#if errorMessage}
            <div
                class="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-300"
                role="alert"
            >
                {errorMessage}
            </div>
        {/if}
        <button
            type="submit"
            disabled={isActivating}
            class="border-accent-blue/35 bg-accent-blue focus-visible:ring-accent-blue focus-visible:ring-offset-canvas mt-1 inline-flex h-11 w-full items-center justify-center rounded-[10px] border text-sm font-semibold text-white shadow-[0_8px_20px_rgba(37,99,235,0.22),inset_0_1px_0_rgba(255,255,255,0.15)] transition-[background-color,filter,box-shadow] hover:bg-blue-500 hover:brightness-105 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
        >
            {isActivating ? "Activating..." : "Activate"}
        </button>
    </form>
</section>
