<script lang="ts">
    import { onMount } from "svelte";
    import { sendPopupRequest } from "../../lib/popup/client";
    import type { PopupSnapshot } from "../../lib/types/popup";

    let snapshot: PopupSnapshot | null = null;
    let busy = false;
    let errorMessage = "";

    const targetRunning = () => snapshot?.target.kind === "running";
    const canStart = () => snapshot?.activePage.kind === "axiom";

    onMount(() => {
        void refresh();
    });

    async function refresh(): Promise<void> {
        errorMessage = "";
        try {
            const response = await sendPopupRequest({
                type: "get_popup_state",
            });
            if (response.type !== "popup_state") {
                throw new Error("unexpected_response");
            }
            snapshot = response.state;
        } catch {
            errorMessage = "The extension background service is unavailable.";
        }
    }

    async function toggleTarget(): Promise<void> {
        if (busy) return;
        busy = true;
        errorMessage = "";
        try {
            const response = await sendPopupRequest({
                type: targetRunning() ? "stop_target" : "start_target",
            });
            if (response.type !== "action_result") {
                throw new Error("unexpected_response");
            }
            snapshot = response.state;
            if (!response.ok) {
                errorMessage =
                    response.errorCode === "active_tab_not_axiom"
                        ? "Open axiom.trade in the active tab and try again."
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
            return `Selected: ${snapshot.target.title}`;
        }
        if (snapshot.target.kind === "paused") {
            return snapshot.target.reason === "target_closed"
                ? "Paused: the selected tab was closed"
                : "Paused: select an Axiom tab again";
        }
        return "No Axiom tab selected";
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
            <p class="text-muted text-xs">Axiom current-tab foundation</p>
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
            >
                Not connected
            </span>
        </div>
        <p class="text-muted mt-2 text-xs leading-5">
            Pairing becomes available with the secure desktop bridge.
        </p>
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

        <button
            type="button"
            class="from-accent-blue to-accent-purple focus-visible:outline-accent-blue mt-3 min-h-11 w-full rounded-lg bg-gradient-to-r px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-45 motion-reduce:transition-none"
            disabled={busy || (!targetRunning() && !canStart())}
            onclick={toggleTarget}
        >
            {busy
                ? "Updating…"
                : targetRunning()
                  ? "Stop auto-opening"
                  : "Start auto-opening here"}
        </button>

        {#if snapshot && !targetRunning() && !canStart()}
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
        >
            Diagnostics
        </summary>
        <dl class="text-muted mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
            <dt>Page</dt>
            <dd class="text-foreground text-right">
                {snapshot?.activePage.kind ?? "unknown"}
            </dd>
            <dt>Target</dt>
            <dd class="text-foreground text-right">
                {snapshot?.target.kind ?? "unknown"}
            </dd>
        </dl>
    </details>
</main>
