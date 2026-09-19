<script lang="ts">
    import {
        extensionBridgeService,
        type ExtensionBridgeState,
        type ExtensionInstallationInfo,
    } from "$lib/services/extensionBridge";
    import { extensionBridgeStore } from "$lib/stores/extensionBridge.svelte";
    import {
        CheckCircle2,
        CircleAlert,
        Copy,
        FolderOpen,
        KeyRound,
        Puzzle,
    } from "@lucide/svelte";
    import { tick } from "svelte";

    type SetupStatus = {
        title: string;
        detail: string;
        tone: "neutral" | "success" | "warning";
    };

    let installation: ExtensionInstallationInfo | null = null;
    let pairingCode = "";
    let message = "";
    let busy = false;
    let rotateArmed = false;
    let setupDialog: HTMLDialogElement;
    let trigger: HTMLButtonElement;

    const triggerClasses = [
        "focus-visible:ring-accent-blue inline-flex min-h-10 items-center",
        "justify-center gap-2 rounded-xl border border-blue-400/25",
        "bg-blue-500/10 px-3 text-xs font-semibold text-blue-200",
        "transition-colors hover:border-blue-300/40 hover:bg-blue-500/15",
        "focus-visible:ring-2 focus-visible:outline-none",
    ];
    const dialogClasses = [
        "text-foreground m-auto max-h-[calc(100dvh-24px)]",
        "w-[min(500px,calc(100vw-24px))] max-w-none overflow-y-auto",
        "rounded-2xl border border-white/10 bg-[#0d1018] p-0",
        "shadow-2xl backdrop:bg-black/70",
    ];
    const stepClasses = [
        "grid grid-cols-[24px_minmax(0,1fr)] gap-2.5 rounded-xl border",
        "border-white/[0.07] bg-white/[0.018] p-3",
    ];
    const stepNumberClasses = [
        "flex size-6 items-center justify-center rounded-full bg-blue-500/15",
        "text-[0.65rem] font-bold text-blue-200",
    ];
    const folderButtonClasses = [
        "focus-visible:ring-accent-blue inline-flex min-h-10 items-center gap-2",
        "rounded-lg border border-blue-400/25 bg-blue-500/10 px-3",
        "text-xs font-semibold text-blue-200 focus-visible:ring-2",
        "focus-visible:outline-none disabled:opacity-50",
    ];
    const secondaryButtonClasses = [
        "focus-visible:ring-accent-blue inline-flex min-h-10 items-center gap-2",
        "rounded-lg border border-white/10 px-3 text-xs",
        "focus-visible:ring-2 focus-visible:outline-none",
    ];
    const revealButtonClasses = [
        "focus-visible:ring-accent-blue mt-2 inline-flex min-h-10 items-center",
        "gap-2 rounded-lg border border-blue-400/25 bg-blue-500/10 px-3",
        "text-xs font-semibold text-blue-200 focus-visible:ring-2",
        "focus-visible:outline-none disabled:opacity-50",
    ];

    async function openSetup(): Promise<void> {
        message = "";
        rotateArmed = false;
        setupDialog.showModal();
        await prepareInstallation();
        await tick();
        setupDialog
            .querySelector<HTMLButtonElement>("[data-autofocus]")
            ?.focus();
    }

    function closeSetup(): void {
        setupDialog.close();
        void tick().then(() => trigger.focus());
    }

    function handleCancel(event: Event): void {
        event.preventDefault();
        closeSetup();
    }

    async function prepareInstallation(): Promise<void> {
        busy = true;
        message = "";
        try {
            installation = await extensionBridgeService.prepareInstallation();
        } catch {
            installation = null;
            message = [
                "Ascend could not prepare the extension files.",
                "Reinstall or update the desktop app, then try again.",
            ].join(" ");
        } finally {
            busy = false;
        }
    }

    async function openInstallationFolder(): Promise<void> {
        busy = true;
        message = "";
        try {
            installation =
                await extensionBridgeService.openInstallationFolder();
            message =
                "Extension folder opened. Return to your browser and choose this folder.";
        } catch {
            message =
                "The folder could not be opened. Copy the folder path and open it manually.";
        } finally {
            busy = false;
        }
    }

    async function revealPairingCode(): Promise<void> {
        busy = true;
        message = "";
        try {
            pairingCode = await extensionBridgeService.getPairingCode();
        } catch {
            message =
                "The pairing code is unavailable. Restart Ascend and try again.";
        } finally {
            busy = false;
        }
    }

    async function regeneratePairingCode(): Promise<void> {
        if (!rotateArmed) {
            rotateArmed = true;
            message = [
                "Resetting the code disconnects the current extension.",
                "Press Reset pairing code again to confirm.",
            ].join(" ");
            return;
        }
        busy = true;
        message = "";
        try {
            pairingCode = await extensionBridgeService.rotatePairingCode();
            rotateArmed = false;
            message =
                "Pairing code reset. Replace the saved code in the extension popup.";
        } catch {
            message = "The pairing code could not be reset.";
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

    function setupStatus(state: ExtensionBridgeState): SetupStatus {
        if (state.listenerStatus === "port_in_use") {
            return {
                title: "Ascend cannot start the extension connection",
                detail: "Close any other running Ascend instance, then reopen this app.",
                tone: "warning",
            };
        }
        if (state.listenerStatus === "unavailable") {
            return {
                title: "Extension connection unavailable",
                detail: "Restart Ascend, then open this setup again.",
                tone: "warning",
            };
        }
        if (state.connectionStatus === "version_mismatch") {
            return {
                title: "Extension update required",
                detail: "Remove the old unpacked extension and load the folder below again.",
                tone: "warning",
            };
        }
        if (state.connectionStatus === "pairing_rejected") {
            return {
                title: "Pairing code was not accepted",
                detail: "Show the current code below and replace the code in the extension popup.",
                tone: "warning",
            };
        }
        if (state.connectionStatus === "connected") {
            return state.targetStatus === "selected"
                ? {
                      title: "Ready to use",
                      detail: "Ascend ext is connected and an Axiom tab is selected.",
                      tone: "success",
                  }
                : {
                      title: "Extension connected",
                      detail: "Open Axiom, then choose that tab from the extension popup.",
                      tone: "success",
                  };
        }
        return {
            title: "Set up the extension",
            detail: [
                "Complete the steps below.",
                "The extension will connect automatically after pairing.",
            ].join(" "),
            tone: "neutral",
        };
    }

    function triggerLabel(
        connectionStatus: ExtensionBridgeState["connectionStatus"],
    ): string {
        return connectionStatus === "connected"
            ? "Manage Ascend ext"
            : "Set up Ascend ext";
    }

    function statusClasses(tone: SetupStatus["tone"]): string {
        if (tone === "success") {
            return "border-emerald-400/20 bg-emerald-500/[0.08]";
        }
        if (tone === "warning") {
            return "border-amber-400/20 bg-amber-500/[0.08]";
        }
        return "border-white/10 bg-white/[0.025]";
    }
</script>

<button
    bind:this={trigger}
    type="button"
    class={triggerClasses}
    onclick={() => void openSetup()}
>
    <Puzzle size={15} aria-hidden="true" />
    {triggerLabel(extensionBridgeStore.state.connectionStatus)}
</button>

<dialog
    bind:this={setupDialog}
    class={dialogClasses}
    aria-labelledby="extension-setup-title"
    oncancel={handleCancel}
>
    <div class="space-y-4 p-4">
        <header>
            <h3 id="extension-setup-title" class="text-sm font-bold">
                Set up Ascend ext
            </h3>
            <p class="text-muted mt-1 text-xs leading-relaxed">
                One setup for Chrome, Edge, and Brave. The extension files are
                already included with Ascend, so there is nothing else to
                download.
            </p>
        </header>

        <section
            class={[
                "flex items-start gap-2.5 rounded-xl border px-3 py-2.5",
                statusClasses(setupStatus(extensionBridgeStore.state).tone),
            ]}
            aria-live="polite"
            aria-label="Extension connection status"
        >
            {#if setupStatus(extensionBridgeStore.state).tone === "success"}
                <CheckCircle2
                    class="mt-0.5 size-4 shrink-0 text-emerald-400"
                    aria-hidden="true"
                />
            {:else if setupStatus(extensionBridgeStore.state).tone === "warning"}
                <CircleAlert
                    class="mt-0.5 size-4 shrink-0 text-amber-300"
                    aria-hidden="true"
                />
            {:else}
                <Puzzle
                    class="mt-0.5 size-4 shrink-0 text-blue-300"
                    aria-hidden="true"
                />
            {/if}
            <div>
                <p class="m-0 text-xs font-semibold">
                    {setupStatus(extensionBridgeStore.state).title}
                </p>
                <p
                    class="text-muted mt-0.5 mb-0 text-[0.68rem] leading-relaxed"
                >
                    {setupStatus(extensionBridgeStore.state).detail}
                </p>
            </div>
        </section>

        <ol class="m-0 list-none space-y-2.5 p-0">
            <li class={stepClasses}>
                <span class={stepNumberClasses} aria-hidden="true">1</span>
                <div class="min-w-0">
                    <p class="m-0 text-xs font-semibold">
                        Open your browser's extensions page
                    </p>
                    <p
                        class="text-muted mt-1 mb-0 text-[0.68rem] leading-relaxed"
                    >
                        Use the browser menu: <strong class="text-foreground"
                            >Extensions → Manage extensions</strong
                        >, then turn on
                        <strong class="text-foreground">Developer mode</strong>.
                    </p>
                </div>
            </li>

            <li class={stepClasses}>
                <span class={stepNumberClasses} aria-hidden="true">2</span>
                <div class="min-w-0">
                    <p class="m-0 text-xs font-semibold">
                        Load the included extension
                    </p>
                    <p
                        class="text-muted mt-1 mb-0 text-[0.68rem] leading-relaxed"
                    >
                        Click <strong class="text-foreground"
                            >Load unpacked</strong
                        > in your browser, then choose the folder prepared by Ascend.
                    </p>
                    {#if installation}
                        <div class="mt-2 flex flex-wrap gap-2">
                            <button
                                data-autofocus
                                type="button"
                                class={folderButtonClasses}
                                disabled={busy}
                                onclick={openInstallationFolder}
                            >
                                <FolderOpen size={15} aria-hidden="true" />
                                Open extension folder
                            </button>
                            <button
                                type="button"
                                class={secondaryButtonClasses}
                                onclick={() =>
                                    copy(
                                        installation?.path ?? "",
                                        "Extension folder path copied.",
                                    )}
                            >
                                <Copy size={14} aria-hidden="true" />
                                Copy folder path
                            </button>
                        </div>
                        <code
                            class={[
                                "text-muted mt-2 block overflow-hidden rounded bg-black/20",
                                "px-2 py-1.5 text-[0.62rem] text-ellipsis",
                                "whitespace-nowrap select-all",
                            ]}
                            title={installation.path}>{installation.path}</code
                        >
                    {:else}
                        <button
                            data-autofocus
                            type="button"
                            class={[
                                "focus-visible:ring-accent-blue mt-2 min-h-10 rounded-lg",
                                "border border-white/10 px-3 text-xs focus-visible:ring-2",
                                "focus-visible:outline-none disabled:opacity-50",
                            ]}
                            disabled={busy}
                            onclick={prepareInstallation}
                        >
                            {busy
                                ? "Preparing extension files…"
                                : "Try preparing files again"}
                        </button>
                    {/if}
                </div>
            </li>

            <li class={stepClasses}>
                <span class={stepNumberClasses} aria-hidden="true">3</span>
                <div class="min-w-0">
                    <p class="m-0 text-xs font-semibold">Pair with Ascend</p>
                    <p
                        class="text-muted mt-1 mb-0 text-[0.68rem] leading-relaxed"
                    >
                        Open the Ascend ext popup and paste the private pairing
                        code. Never share this code.
                    </p>
                    {#if pairingCode}
                        <div class="mt-2 flex gap-2">
                            <code
                                class={[
                                    "text-foreground min-w-0 flex-1 overflow-hidden rounded",
                                    "bg-black/20 px-2 py-2 text-[0.68rem] text-ellipsis select-all",
                                ]}>{pairingCode}</code
                            >
                            <button
                                type="button"
                                class={secondaryButtonClasses}
                                onclick={() =>
                                    copy(pairingCode, "Pairing code copied.")}
                            >
                                <Copy size={14} aria-hidden="true" />
                                Copy
                            </button>
                        </div>
                    {:else}
                        <button
                            type="button"
                            class={revealButtonClasses}
                            disabled={busy}
                            onclick={revealPairingCode}
                        >
                            <KeyRound size={15} aria-hidden="true" />
                            {busy ? "Loading…" : "Show pairing code"}
                        </button>
                    {/if}
                    <button
                        type="button"
                        class={[
                            "text-muted focus-visible:ring-danger mt-2 block min-h-8",
                            "rounded-md px-1 text-[0.65rem] underline decoration-white/20",
                            "underline-offset-2 focus-visible:ring-2 focus-visible:outline-none",
                            "disabled:opacity-50",
                        ]}
                        disabled={busy}
                        onclick={regeneratePairingCode}
                    >
                        {rotateArmed
                            ? "Confirm reset pairing code"
                            : "Reset pairing code"}
                    </button>
                </div>
            </li>

            <li class={stepClasses}>
                <span class={stepNumberClasses} aria-hidden="true">4</span>
                <div class="min-w-0">
                    <p class="m-0 text-xs font-semibold">
                        Select your Axiom tab
                    </p>
                    <p
                        class="text-muted mt-1 mb-0 text-[0.68rem] leading-relaxed"
                    >
                        Open <strong class="text-foreground">axiom.trade</strong
                        >, then choose the current tab from the extension popup.
                    </p>
                </div>
            </li>
        </ol>

        <p
            class="text-danger m-0 min-h-4 text-xs leading-relaxed"
            aria-live="polite"
        >
            {message}
        </p>

        <footer class="flex justify-end">
            <button
                type="button"
                class={[
                    "focus-visible:ring-accent-blue min-h-10 rounded-lg border",
                    "border-white/10 px-4 text-xs font-semibold focus-visible:ring-2",
                    "focus-visible:outline-none",
                ]}
                onclick={closeSetup}>Close</button
            >
        </footer>
    </div>
</dialog>
