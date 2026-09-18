<script lang="ts">
    import { extensionBridgeService } from "$lib/services/extensionBridge";
    import { extensionBridgeStore } from "$lib/stores/extensionBridge.svelte";
    import { tick } from "svelte";

    type BrowserName = "Chrome" | "Edge" | "Brave";
    const browserPages: Record<BrowserName, string> = {
        Chrome: "chrome://extensions",
        Edge: "edge://extensions",
        Brave: "brave://extensions",
    };

    let browser: BrowserName = "Chrome";
    let pairingCode = "";
    let message = "";
    let busy = false;
    let setupDialog: HTMLDialogElement;
    let trigger: HTMLButtonElement;

    function openSetup(): void {
        message = "";
        setupDialog.showModal();
        void tick().then(() =>
            setupDialog.querySelector<HTMLSelectElement>("select")?.focus(),
        );
    }

    function closeSetup(): void {
        setupDialog.close();
        void tick().then(() => trigger.focus());
    }

    function handleCancel(event: Event): void {
        event.preventDefault();
        closeSetup();
    }

    async function revealPairingCode(): Promise<void> {
        busy = true;
        message = "";
        try {
            pairingCode = await extensionBridgeService.getPairingCode();
        } catch {
            message =
                "Pairing code is unavailable while the desktop bridge is stopped.";
        } finally {
            busy = false;
        }
    }

    async function copy(value: string, confirmation: string): Promise<void> {
        try {
            await navigator.clipboard.writeText(value);
            message = confirmation;
        } catch {
            message = "Copy failed. Select the value and copy it manually.";
        }
    }
</script>

<button
    bind:this={trigger}
    type="button"
    class="focus-visible:ring-accent-blue min-h-10 rounded-xl border border-blue-400/25 bg-blue-500/10 px-3 text-xs font-semibold text-blue-200 focus-visible:ring-2 focus-visible:outline-none"
    onclick={openSetup}
>
    Install / connect extension
</button>

<dialog
    bind:this={setupDialog}
    class="text-foreground m-auto w-[min(440px,calc(100vw-24px))] max-w-none rounded-2xl border border-white/10 bg-[#0d1018] p-0 shadow-2xl backdrop:bg-black/70"
    aria-labelledby="extension-setup-title"
    oncancel={handleCancel}
>
    <div class="space-y-4 p-4">
        <header>
            <h3 id="extension-setup-title" class="text-sm font-bold">
                Connect Ascend ext
            </h3>
            <p class="text-muted mt-1 text-xs leading-relaxed">
                Load the unpacked extension, then pair it with this desktop
                client.
            </p>
        </header>

        <ol
            class="text-muted list-decimal space-y-3 pl-5 text-xs leading-relaxed"
        >
            <li>
                <label class="block">
                    <span class="mb-1 block font-semibold"
                        >Choose a browser</span
                    >
                    <select
                        bind:value={browser}
                        class="text-foreground focus-visible:ring-accent-blue h-10 w-full rounded-lg border border-white/10 bg-[#121827] px-2 focus-visible:ring-2 focus-visible:outline-none"
                    >
                        <option>Chrome</option>
                        <option>Edge</option>
                        <option>Brave</option>
                    </select>
                </label>
            </li>
            <li>
                Open the extensions page and enable Developer mode.
                <div class="mt-1 flex gap-2">
                    <code
                        class="text-foreground min-w-0 flex-1 rounded bg-black/20 px-2 py-2 select-all"
                        >{browserPages[browser]}</code
                    >
                    <button
                        type="button"
                        class="focus-visible:ring-accent-blue min-h-10 rounded-lg border border-white/10 px-3 focus-visible:ring-2 focus-visible:outline-none"
                        onclick={() =>
                            copy(
                                browserPages[browser],
                                "Extensions address copied.",
                            )}>Copy</button
                    >
                </div>
            </li>
            <li>
                Choose <strong class="text-foreground">Load unpacked</strong> and
                select the Ascend ext build folder.
            </li>
            <li>
                Copy the pairing code into the extension popup. Keep it private.
                {#if pairingCode}
                    <div class="mt-1 flex gap-2">
                        <code
                            class="text-foreground min-w-0 flex-1 overflow-hidden rounded bg-black/20 px-2 py-2 text-ellipsis select-all"
                            >{pairingCode}</code
                        >
                        <button
                            type="button"
                            class="focus-visible:ring-accent-blue min-h-10 rounded-lg border border-white/10 px-3 focus-visible:ring-2 focus-visible:outline-none"
                            onclick={() =>
                                copy(pairingCode, "Pairing code copied.")}
                            >Copy</button
                        >
                    </div>
                {:else}
                    <button
                        type="button"
                        class="focus-visible:ring-accent-blue mt-1 min-h-10 rounded-lg border border-blue-400/25 bg-blue-500/10 px-3 text-blue-200 focus-visible:ring-2 focus-visible:outline-none disabled:opacity-50"
                        disabled={busy}
                        onclick={revealPairingCode}
                        >{busy ? "Loading…" : "Show pairing code"}</button
                    >
                {/if}
            </li>
        </ol>

        <p class="text-muted text-xs" aria-live="polite">
            Status: {extensionBridgeStore.state.connectionStatus === "connected"
                ? "Connected"
                : "Waiting for extension"}
        </p>
        <p class="text-danger min-h-4 text-xs" aria-live="polite">{message}</p>

        <footer class="flex justify-end">
            <button
                type="button"
                class="focus-visible:ring-accent-blue min-h-10 rounded-lg border border-white/10 px-4 text-xs font-semibold focus-visible:ring-2 focus-visible:outline-none"
                onclick={closeSetup}>Close</button
            >
        </footer>
    </div>
</dialog>
