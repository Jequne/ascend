<script lang="ts">
    import { onMount } from "svelte";
    import { sendPopupRequest } from "../../lib/popup/client";
    import type { BridgeConnectionState } from "../../lib/types/bridge";
    import type { PopupSnapshot } from "../../lib/types/popup";

    let snapshot: PopupSnapshot | null = null;
    let busy = false;
    let errorMessage = "";
    let pairingCode = "";

    const targetSelected = () => snapshot?.target.kind === "running";
    const targetRunning = () =>
        targetSelected() &&
        snapshot?.bridge.connection === "connected" &&
        snapshot.bridge.mode === "current_axiom_tab";
    const canStart = () =>
        snapshot?.activePage.kind === "axiom" &&
        snapshot?.bridge.connection === "connected";

    onMount(() => {
        void refresh();
        const timer = setInterval(() => void refresh(false), 1_000);
        return () => clearInterval(timer);
    });

    async function refresh(showError = true): Promise<void> {
        if (showError) errorMessage = "";
        try {
            const response = await sendPopupRequest({
                type: "get_popup_state",
            });
            if (response.type !== "popup_state")
                throw new Error("unexpected_response");
            snapshot = response.state;
        } catch {
            if (showError)
                errorMessage =
                    "The extension background service is unavailable.";
        }
    }

    async function pair(): Promise<void> {
        if (busy) return;
        busy = true;
        errorMessage = "";
        try {
            const response = await sendPopupRequest({
                type: "pair_bridge",
                pairingCode,
            });
            if (response.type !== "action_result")
                throw new Error("unexpected_response");
            snapshot = response.state;
            if (!response.ok) {
                errorMessage =
                    response.errorCode === "invalid_pairing_code"
                        ? "Enter the 43-character pairing code from Ascend."
                        : "Pairing was rejected. Check that Ascend is open and the code is current.";
            } else {
                pairingCode = "";
            }
        } catch {
            errorMessage = "The pairing code could not be saved.";
        } finally {
            busy = false;
        }
    }

    async function retry(): Promise<void> {
        if (busy) return;
        busy = true;
        errorMessage = "";
        try {
            const response = await sendPopupRequest({ type: "retry_bridge" });
            if (response.type !== "action_result")
                throw new Error("unexpected_response");
            snapshot = response.state;
        } catch {
            errorMessage = "The desktop connection could not be retried.";
        } finally {
            busy = false;
        }
    }

    async function toggleTarget(): Promise<void> {
        if (busy) return;
        busy = true;
        errorMessage = "";
        try {
            const response = await sendPopupRequest({
                type: targetSelected() ? "stop_target" : "start_target",
            });
            if (response.type !== "action_result")
                throw new Error("unexpected_response");
            snapshot = response.state;
            if (!response.ok) {
                errorMessage =
                    response.errorCode === "active_tab_not_axiom"
                        ? "Open axiom.trade in the active tab and try again."
                        : response.errorCode === "bridge_not_connected"
                          ? "Connect Ascend ext to the desktop client first."
                          : "The target tab could not be updated.";
            }
        } catch {
            errorMessage = "The target tab could not be updated.";
        } finally {
            busy = false;
        }
    }

    function targetLabel(): string {
        if (!snapshot) return "Loading target state…";
        if (snapshot.target.kind === "running") {
            return targetRunning()
                ? `Running in: ${snapshot.target.title}`
                : `Paused: ${snapshot.target.title} is selected while desktop reconnects`;
        }
        if (snapshot.target.kind === "paused") {
            return snapshot.target.reason === "target_closed"
                ? "Paused: the selected tab was closed"
                : "Paused: select an Axiom tab again";
        }
        return snapshot.bridge.mode === "current_axiom_tab"
            ? "Waiting for an Axiom tab"
            : "No Axiom tab selected";
    }

    function connectionLabel(connection?: BridgeConnectionState): string {
        const labels: Record<BridgeConnectionState, string> = {
            unpaired: "Not paired",
            connecting: "Connecting",
            connected: "Connected",
            reconnecting: "Reconnecting",
            pairing_rejected: "Pairing rejected",
            version_mismatch: "Update required",
            unavailable: "Unavailable",
        };
        return connection ? labels[connection] : "Loading";
    }

    function modeDescription(): string {
        if (!snapshot) return "Loading mode…";
        if (snapshot.bridge.mode === "new_tab") {
            return "Desktop is using the system new-tab opener.";
        }
        if (snapshot.bridge.mode === "current_axiom_tab") {
            return targetRunning()
                ? "Current-tab auto-opening is active."
                : "Current-tab mode is paused until the connection and target are ready.";
        }
        return "Auto-opening is off.";
    }
</script>

<main class="bg-canvas text-foreground w-[340px] p-4">
    <header class="mb-4 flex items-center gap-3">
        <img
            class="size-10 rounded-xl"
            src="/icon/128.png"
            alt=""
            width="40"
            height="40"
        />
        <div>
            <h1 class="text-base font-semibold tracking-tight">Ascend ext</h1>
            <p class="text-muted text-xs">Axiom current-tab auto-opening</p>
        </div>
    </header>

    <section
        class="border-border bg-surface mb-3 rounded-xl border p-3"
        aria-labelledby="connection-heading"
    >
        <div class="flex items-center justify-between gap-3">
            <h2 id="connection-heading" class="text-sm font-medium">
                Desktop connection
            </h2>
            <span
                class="bg-surface-elevated text-muted rounded-full px-2 py-1 text-xs"
                aria-live="polite"
            >
                {connectionLabel(snapshot?.bridge.connection)}
            </span>
        </div>
        {#if !snapshot || snapshot.bridge.connection === "unpaired" || snapshot.bridge.connection === "pairing_rejected"}
            <form
                class="mt-3 grid gap-2"
                onsubmit={(event) => {
                    event.preventDefault();
                    void pair();
                }}
            >
                <label class="text-muted text-xs" for="pairing-code"
                    >Pairing code from Ascend</label
                >
                <input
                    id="pairing-code"
                    type="password"
                    autocomplete="off"
                    bind:value={pairingCode}
                    class="border-border bg-surface-elevated focus-visible:outline-accent-blue min-h-10 rounded-lg border px-3 text-xs focus-visible:outline-2"
                />
                <button
                    type="submit"
                    disabled={busy || pairingCode.trim().length !== 43}
                    class="focus-visible:outline-accent-blue min-h-10 rounded-lg border border-blue-400/30 bg-blue-500/15 text-xs font-semibold text-blue-100 focus-visible:outline-2 disabled:opacity-45"
                    >{busy ? "Pairing…" : "Pair extension"}</button
                >
            </form>
        {:else if snapshot.bridge.connection !== "connected"}
            {#if snapshot.bridge.connection === "version_mismatch"}
                <p class="text-danger mt-3 text-xs leading-5">
                    Update Ascend or Ascend ext so their versions match.
                </p>
            {/if}
            <button
                type="button"
                disabled={busy}
                class="border-border focus-visible:outline-accent-blue mt-3 min-h-10 w-full rounded-lg border text-xs focus-visible:outline-2 disabled:opacity-45"
                onclick={() => void retry()}
                >{busy ? "Retrying…" : "Retry connection"}</button
            >
        {/if}
    </section>

    <section
        class="border-border bg-surface rounded-xl border p-3"
        aria-labelledby="target-heading"
    >
        <h2 id="target-heading" class="text-sm font-medium">Target tab</h2>
        <p
            class="text-muted mt-2 min-h-10 text-sm leading-5"
            aria-live="polite"
        >
            {targetLabel()}
        </p>
        <p class="text-muted text-xs leading-5" aria-live="polite">
            {modeDescription()}
        </p>
        <button
            type="button"
            class="from-accent-blue to-accent-purple focus-visible:outline-accent-blue mt-3 min-h-11 w-full rounded-lg bg-gradient-to-r px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-45 motion-reduce:transition-none"
            disabled={busy || (!targetSelected() && !canStart())}
            onclick={toggleTarget}
        >
            {busy
                ? "Updating…"
                : targetSelected()
                  ? "Stop auto-opening"
                  : "Start auto-opening here"}
        </button>
        {#if snapshot && !targetSelected() && snapshot.activePage.kind !== "axiom"}
            <p class="text-muted mt-2 text-xs leading-5">
                Open <span class="text-foreground">https://axiom.trade</span> in this
                tab to select it.
            </p>
        {/if}
    </section>

    <p class="text-danger mt-3 min-h-5 text-xs leading-5" aria-live="assertive">
        {errorMessage}
    </p>

    <details
        class="border-border bg-surface rounded-lg border px-3 py-2 text-xs"
    >
        <summary
            class="text-muted focus-visible:outline-accent-blue cursor-pointer select-none focus-visible:outline-2 focus-visible:outline-offset-2"
            >Diagnostics</summary
        >
        <dl class="text-muted mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
            <dt>Connection</dt>
            <dd class="text-foreground text-right">
                {snapshot?.bridge.connection ?? "unknown"}
            </dd>
            <dt>Mode</dt>
            <dd class="text-foreground text-right">
                {snapshot?.bridge.mode ?? "unknown"}
            </dd>
            <dt>Page</dt>
            <dd class="text-foreground text-right">
                {snapshot?.activePage.kind ?? "unknown"}
            </dd>
            <dt>Target</dt>
            <dd class="text-foreground text-right">
                {snapshot?.target.kind ?? "unknown"}
            </dd>
            <dt>Reconnect</dt>
            <dd class="text-foreground text-right">
                {snapshot?.bridge.reconnectAttempt ?? 0}
            </dd>
        </dl>
    </details>
</main>
