import { normalizeCustomAudioName } from "$lib/config/settings";
import {
    CUSTOM_NOTIFICATION_AUDIO_ID,
    notificationAudioStorage,
    type NotificationAudioStorage,
    type StoredNotificationAudio,
} from "$lib/services/notificationAudioStorage";
import type { NotificationSettings } from "$lib/types";

export const DEFAULT_NOTIFICATION_SOUND_URL =
    "/audio/mixkit-positive-notification-951.wav";
export const MAX_NOTIFICATION_AUDIO_BYTES = 5 * 1024 * 1024;

const ALLOWED_EXTENSIONS = new Set(["wav", "mp3", "ogg"]);
const ALLOWED_MIME_TYPES = new Set([
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
]);

export interface PreparedNotificationAudio {
    readonly id: string;
    readonly name: string;
    readonly type: string;
}

export interface AudioNotificationPlayer {
    play(settings: Readonly<NotificationSettings>): Promise<void>;
}

export interface AudioNotificationPreview extends AudioNotificationPlayer {
    preview(
        settings: Readonly<NotificationSettings>,
        draft?: PreparedNotificationAudio | null,
    ): Promise<void>;
    stop(): void;
}

export type AudioElementFactory = (sourceUrl: string) => HTMLAudioElement;
export type AudioBlobProbe = (blob: Blob) => Promise<void>;

export class BrowserAudioNotificationService implements AudioNotificationPreview {
    private activeAudio: HTMLAudioElement | null = null;
    private activeObjectUrl: string | null = null;
    private playGeneration = 0;
    private readonly preparedBlobs = new WeakMap<
        PreparedNotificationAudio,
        Blob
    >();

    constructor(
        private readonly createAudio: AudioElementFactory = (sourceUrl) =>
            new Audio(sourceUrl),
        private readonly storage: NotificationAudioStorage = notificationAudioStorage,
        private readonly createObjectUrl: (blob: Blob) => string = (blob) =>
            URL.createObjectURL(blob),
        private readonly revokeObjectUrl: (url: string) => void = (url) =>
            URL.revokeObjectURL(url),
        private readonly probeAudio: AudioBlobProbe = (blob) =>
            this.probeAudioBlob(blob),
    ) {}

    async prepareFile(file: File): Promise<PreparedNotificationAudio> {
        if (file.size === 0) {
            throw new Error("The selected audio file is empty.");
        }
        if (file.size > MAX_NOTIFICATION_AUDIO_BYTES) {
            throw new Error("Choose an audio file no larger than 5 MiB.");
        }

        const name = normalizeCustomAudioName(file.name);
        const extension = name?.split(".").at(-1)?.toLowerCase() ?? "";
        if (!name || !ALLOWED_EXTENSIONS.has(extension)) {
            throw new Error("Choose a .wav, .mp3, or .ogg audio file.");
        }
        if (file.type && !ALLOWED_MIME_TYPES.has(file.type.toLowerCase())) {
            throw new Error("The selected file is not a supported audio type.");
        }

        await this.probeAudio(file);
        const draft: PreparedNotificationAudio = Object.freeze({
            id: CUSTOM_NOTIFICATION_AUDIO_ID,
            name,
            type: file.type || mimeTypeForExtension(extension),
        });
        this.preparedBlobs.set(draft, file);
        return draft;
    }

    async saveCustom(draft: PreparedNotificationAudio): Promise<void> {
        const blob = this.preparedBlobs.get(draft);
        if (!blob) throw new Error("The selected audio draft has expired.");
        const record: StoredNotificationAudio = {
            ...draft,
            blob,
            updatedAt: new Date().toISOString(),
        };
        await this.storage.replace(record);
    }

    async removeCustom(id: string | null): Promise<void> {
        if (id) await this.storage.remove(id);
    }

    async hasCustom(id: string | null): Promise<boolean> {
        return id ? (await this.storage.get(id)) !== null : false;
    }

    async play(settings: Readonly<NotificationSettings>): Promise<void> {
        if (!settings.enabled) return;
        const generation = ++this.playGeneration;
        await this.playSettings(settings, null, generation);
    }

    async preview(
        settings: Readonly<NotificationSettings>,
        draft: PreparedNotificationAudio | null = null,
    ): Promise<void> {
        if (!settings.enabled) return;
        const generation = ++this.playGeneration;
        await this.playSettings(settings, draft, generation);
    }

    stop(): void {
        this.playGeneration += 1;
        this.stopActiveAudio();
    }

    private async playSettings(
        settings: Readonly<NotificationSettings>,
        draft: PreparedNotificationAudio | null,
        generation: number,
    ): Promise<void> {
        let blob: Blob | null = draft
            ? (this.preparedBlobs.get(draft) ?? null)
            : null;

        if (!blob && settings.source === "custom" && settings.customAudioId) {
            try {
                blob =
                    (await this.storage.get(settings.customAudioId))?.blob ??
                    null;
            } catch (error: unknown) {
                console.warn(
                    "Unable to load custom notification sound:",
                    error,
                );
            }
        }
        if (generation !== this.playGeneration) return;

        let objectUrl: string | null = null;
        try {
            const sourceUrl = blob
                ? (objectUrl = this.createObjectUrl(blob))
                : DEFAULT_NOTIFICATION_SOUND_URL;
            await this.playUrl(
                sourceUrl,
                settings.volume,
                objectUrl,
                generation,
            );
        } catch (error: unknown) {
            if (objectUrl && this.activeObjectUrl === objectUrl) {
                this.stopActiveAudio();
            } else if (objectUrl) {
                this.revokeObjectUrl(objectUrl);
            }
            console.warn("Unable to play notification sound:", error);
        }
    }

    private async playUrl(
        sourceUrl: string,
        volume: number,
        objectUrl: string | null,
        generation: number,
    ): Promise<void> {
        this.stopActiveAudio();
        if (generation !== this.playGeneration) {
            if (objectUrl) this.revokeObjectUrl(objectUrl);
            return;
        }

        const audio = this.createAudio(sourceUrl);
        audio.volume = Math.min(1, Math.max(0, volume / 100));
        audio.currentTime = 0;
        this.activeAudio = audio;
        this.activeObjectUrl = objectUrl;
        audio.addEventListener?.("ended", () => this.releaseIfActive(audio), {
            once: true,
        });
        await audio.play();
    }

    private stopActiveAudio(): void {
        if (this.activeAudio) {
            this.activeAudio.pause();
            this.activeAudio.currentTime = 0;
            this.activeAudio = null;
        }
        if (this.activeObjectUrl) {
            this.revokeObjectUrl(this.activeObjectUrl);
            this.activeObjectUrl = null;
        }
    }

    private releaseIfActive(audio: HTMLAudioElement): void {
        if (this.activeAudio !== audio) return;
        this.activeAudio = null;
        if (this.activeObjectUrl) {
            this.revokeObjectUrl(this.activeObjectUrl);
            this.activeObjectUrl = null;
        }
    }

    private probeAudioBlob(blob: Blob): Promise<void> {
        const objectUrl = this.createObjectUrl(blob);
        return new Promise((resolve, reject) => {
            const audio = this.createAudio(objectUrl);
            const cleanup = (): void => {
                window.clearTimeout(timeout);
                audio.removeEventListener("loadedmetadata", handleLoaded);
                audio.removeEventListener("error", handleError);
                this.revokeObjectUrl(objectUrl);
            };
            const handleLoaded = (): void => {
                cleanup();
                if (Number.isFinite(audio.duration) && audio.duration > 0) {
                    resolve();
                } else {
                    reject(
                        new Error("The selected audio file is not playable."),
                    );
                }
            };
            const handleError = (): void => {
                cleanup();
                reject(new Error("The selected audio file is not playable."));
            };
            const timeout = window.setTimeout(() => {
                cleanup();
                reject(new Error("The audio file could not be decoded."));
            }, 10_000);
            audio.preload = "metadata";
            audio.addEventListener("loadedmetadata", handleLoaded);
            audio.addEventListener("error", handleError);
            audio.load();
        });
    }
}

function mimeTypeForExtension(extension: string): string {
    if (extension === "mp3") return "audio/mpeg";
    if (extension === "ogg") return "audio/ogg";
    return "audio/wav";
}

export const audioNotificationService = new BrowserAudioNotificationService();
