<script lang="ts">
    import SwitchControl from "$lib/components/settings/SwitchControl.svelte";
    import {
        audioNotificationService,
        MAX_NOTIFICATION_AUDIO_BYTES,
        type PreparedNotificationAudio,
    } from "$lib/services/audioNotifications";
    import { CUSTOM_NOTIFICATION_AUDIO_ID } from "$lib/services/notificationAudioStorage";
    import type { NotificationSettings } from "$lib/types";
    import { BellRing, FileAudio, Play, RotateCcw } from "@lucide/svelte";

    export let settings: NotificationSettings;
    export let customDraft: PreparedNotificationAudio | null;
    export let customAvailable: boolean | null;
    export let storageError = "";
    export let onPreview: () => void;

    let fileError = "";
    let isPreparingFile = false;

    async function chooseFile(event: Event): Promise<void> {
        const input = event.currentTarget as HTMLInputElement;
        const file = input.files?.[0];
        input.value = "";
        if (!file) return;

        fileError = "";
        isPreparingFile = true;
        try {
            customDraft = await audioNotificationService.prepareFile(file);
            settings = {
                ...settings,
                source: "custom",
                customAudioId: CUSTOM_NOTIFICATION_AUDIO_ID,
                customAudioName: customDraft.name,
            };
            customAvailable = true;
        } catch (error: unknown) {
            fileError = error instanceof Error ? error.message : String(error);
        } finally {
            isPreparingFile = false;
        }
    }

    function useDefault(): void {
        customDraft = null;
        customAvailable = null;
        fileError = "";
        settings = {
            ...settings,
            source: "default",
            customAudioId: null,
            customAudioName: null,
        };
    }
</script>

<section
    class="mx-3 mt-3 overflow-hidden rounded-xl border border-white/[0.075] bg-[linear-gradient(145deg,rgba(30,32,43,0.9),rgba(19,21,30,0.92))]"
    aria-labelledby="notifications-heading"
>
    <div
        class="flex items-center justify-between gap-3 border-b border-white/[0.06] p-3"
    >
        <div class="flex min-w-0 items-center gap-2.5">
            <span
                class="text-accent-purple bg-accent-purple/10 flex size-8 shrink-0 items-center justify-center rounded-lg border border-indigo-400/15"
            >
                <BellRing size={17} aria-hidden="true" />
            </span>
            <div class="min-w-0">
                <h3
                    id="notifications-heading"
                    class="text-foreground m-0 text-xs font-bold tracking-[0.025em] uppercase"
                >
                    Notifications
                </h3>
                <p class="text-muted mt-1 mb-0 text-[0.64rem] leading-snug">
                    Play a sound when a token enters the visible feed.
                </p>
            </div>
        </div>
        <SwitchControl
            bind:checked={settings.enabled}
            label="Enable sound notifications"
        />
    </div>

    <div
        class="grid items-end gap-3 p-3 min-[420px]:grid-cols-[minmax(0,1fr)_auto]"
    >
        <label
            class="flex min-w-0 flex-col gap-2 text-xs font-semibold text-slate-200"
        >
            <span class="flex items-center justify-between gap-2">
                Volume
                <span class="text-muted tabular-nums" aria-live="polite">
                    {settings.volume}%
                </span>
            </span>
            <input
                id="notification-volume"
                class="accent-accent-purple h-5 w-full min-w-0 cursor-pointer"
                type="range"
                min="0"
                max="100"
                step="1"
                bind:value={settings.volume}
                aria-label="Notification volume"
            />
        </label>

        <button
            class="focus-visible:ring-accent-purple inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 text-xs font-semibold text-slate-200 transition-colors hover:border-white/20 hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
            type="button"
            disabled={!settings.enabled}
            onclick={onPreview}
        >
            <Play size={13} aria-hidden="true" />
            Test sound
        </button>
    </div>

    <div class="border-t border-white/[0.06] p-3">
        <div
            class="grid min-w-0 gap-2 min-[420px]:grid-cols-[minmax(0,1fr)_auto]"
        >
            <label
                class="hover:border-accent-purple/40 hover:bg-accent-purple/[0.06] focus-within:ring-accent-purple flex min-h-9 min-w-0 cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-white/15 bg-black/15 px-2.5 text-xs font-semibold text-slate-200 transition-colors focus-within:ring-2"
            >
                <FileAudio size={14} class="shrink-0" aria-hidden="true" />
                <span class="min-w-0 truncate">
                    {isPreparingFile ? "Checking audio…" : "Choose audio file"}
                </span>
                <input
                    class="sr-only"
                    type="file"
                    accept="audio/wav,audio/mpeg,audio/ogg,.wav,.mp3,.ogg"
                    aria-label="Choose notification audio file"
                    disabled={isPreparingFile}
                    onchange={chooseFile}
                />
            </label>
            <button
                class="focus-visible:ring-accent-purple inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 text-xs font-semibold text-slate-200 transition-colors hover:border-white/20 hover:bg-white/[0.07] focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                type="button"
                disabled={settings.source === "default" && !customDraft}
                onclick={useDefault}
            >
                <RotateCcw size={13} aria-hidden="true" />
                Use default
            </button>
        </div>

        <div class="mt-2 min-w-0 text-[0.62rem] leading-snug">
            {#if settings.source === "custom" && settings.customAudioName}
                <p class="text-foreground m-0 break-all">
                    Selected: {settings.customAudioName}
                </p>
                {#if customAvailable === false}
                    <p class="mt-1 mb-0 text-amber-300" role="status">
                        This custom file is unavailable on this device. The
                        default sound will play until you choose another file.
                    </p>
                {/if}
            {:else}
                <p class="text-muted m-0">Using the bundled default sound.</p>
            {/if}
            <p class="text-muted mt-1 mb-0">
                WAV, MP3, or OGG · up to {MAX_NOTIFICATION_AUDIO_BYTES /
                    (1024 * 1024)} MiB
            </p>
        </div>

        {#if fileError || storageError}
            <p
                class="mt-2 mb-0 rounded-lg border border-red-500/25 bg-red-500/10 px-2.5 py-2 text-xs text-red-300"
                role="alert"
            >
                {fileError || storageError}
            </p>
        {/if}
    </div>
</section>
