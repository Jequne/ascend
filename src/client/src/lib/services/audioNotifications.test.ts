import { describe, expect, it, vi } from "vitest";
import { DEFAULT_NOTIFICATIONS } from "$lib/config/constants";
import {
    BrowserAudioNotificationService,
    DEFAULT_NOTIFICATION_SOUND_URL,
    MAX_NOTIFICATION_AUDIO_BYTES,
} from "$lib/services/audioNotifications";
import type {
    NotificationAudioStorage,
    StoredNotificationAudio,
} from "$lib/services/notificationAudioStorage";

interface FakeAudio {
    volume: number;
    currentTime: number;
    pause: ReturnType<typeof vi.fn>;
    play: ReturnType<typeof vi.fn>;
}

function createStorage(
    record: StoredNotificationAudio | null = null,
): NotificationAudioStorage & {
    get: ReturnType<typeof vi.fn>;
    replace: ReturnType<typeof vi.fn>;
    remove: ReturnType<typeof vi.fn>;
} {
    return {
        get: vi.fn().mockResolvedValue(record),
        replace: vi.fn().mockResolvedValue(undefined),
        remove: vi.fn().mockResolvedValue(undefined),
    };
}

function createAudioHarness(
    storage: NotificationAudioStorage = createStorage(),
    probe = vi.fn().mockResolvedValue(undefined),
): {
    service: BrowserAudioNotificationService;
    audios: FakeAudio[];
    sources: string[];
    probe: ReturnType<typeof vi.fn>;
    revoke: ReturnType<typeof vi.fn>;
} {
    const audios: FakeAudio[] = [];
    const sources: string[] = [];
    const revoke = vi.fn();
    const service = new BrowserAudioNotificationService(
        (source) => {
            const audio: FakeAudio = {
                volume: 1,
                currentTime: 0,
                pause: vi.fn(),
                play: vi.fn().mockResolvedValue(undefined),
            };
            sources.push(source);
            audios.push(audio);
            return audio as unknown as HTMLAudioElement;
        },
        storage,
        () => "blob:custom-audio",
        revoke,
        probe,
    );
    return { service, audios, sources, probe, revoke };
}

const customSettings = {
    ...DEFAULT_NOTIFICATIONS,
    source: "custom" as const,
    customAudioId: "notification-custom-sound",
    customAudioName: "tone.mp3",
};

describe("BrowserAudioNotificationService", () => {
    it("uses the bundled sound, applies volume, and restarts one channel", async () => {
        const { service, audios, sources } = createAudioHarness();

        await service.play({ ...DEFAULT_NOTIFICATIONS, volume: 70 });
        await service.play({ ...DEFAULT_NOTIFICATIONS, volume: 25 });

        expect(sources).toEqual([
            DEFAULT_NOTIFICATION_SOUND_URL,
            DEFAULT_NOTIFICATION_SOUND_URL,
        ]);
        expect(audios[0]?.volume).toBe(0.7);
        expect(audios[0]?.pause).toHaveBeenCalledOnce();
        expect(audios[0]?.currentTime).toBe(0);
        expect(audios[1]?.volume).toBe(0.25);
        expect(audios[1]?.play).toHaveBeenCalledOnce();
    });

    it("stays silent when disabled and contains playback failures", async () => {
        const failure = new Error("autoplay blocked");
        const warning = vi
            .spyOn(console, "warn")
            .mockImplementation(() => undefined);
        const createAudio = vi.fn(() => {
            return {
                volume: 1,
                currentTime: 0,
                pause: vi.fn(),
                play: vi.fn().mockRejectedValue(failure),
            } as unknown as HTMLAudioElement;
        });
        const service = new BrowserAudioNotificationService(
            createAudio,
            createStorage(),
        );

        await service.play({ ...DEFAULT_NOTIFICATIONS, enabled: false });
        expect(createAudio).not.toHaveBeenCalled();

        await expect(
            service.play(DEFAULT_NOTIFICATIONS),
        ).resolves.toBeUndefined();
        expect(warning).toHaveBeenCalledWith(
            "Unable to play notification sound:",
            failure,
        );
    });

    it("validates, previews, and atomically persists a custom draft", async () => {
        const storage = createStorage();
        const { service, sources, probe } = createAudioHarness(storage);
        const file = new File(["audio-data"], "tone.mp3", {
            type: "audio/mpeg",
        });

        const draft = await service.prepareFile(file);
        expect(probe).toHaveBeenCalledWith(file);
        expect(draft).toEqual({
            id: "notification-custom-sound",
            name: "tone.mp3",
            type: "audio/mpeg",
        });

        await service.preview(customSettings, draft);
        expect(storage.get).not.toHaveBeenCalled();
        expect(sources).toEqual(["blob:custom-audio"]);

        await service.saveCustom(draft);
        expect(storage.replace).toHaveBeenCalledWith(
            expect.objectContaining({
                id: "notification-custom-sound",
                name: "tone.mp3",
                type: "audio/mpeg",
                blob: file,
            }),
        );
    });

    it("loads stored custom audio and falls back to default when unavailable", async () => {
        const blob = new Blob(["stored"], { type: "audio/ogg" });
        const storage = createStorage({
            id: "notification-custom-sound",
            name: "stored.ogg",
            type: "audio/ogg",
            blob,
            updatedAt: "2026-09-19T00:00:00.000Z",
        });
        const first = createAudioHarness(storage);
        await first.service.play(customSettings);
        expect(first.sources).toEqual(["blob:custom-audio"]);

        storage.get.mockResolvedValue(null);
        const second = createAudioHarness(storage);
        await second.service.play(customSettings);
        expect(second.sources).toEqual([DEFAULT_NOTIFICATION_SOUND_URL]);
    });

    it("falls back after an IndexedDB error without rejecting playback", async () => {
        const failure = new Error("indexedDB unavailable");
        const storage = createStorage();
        storage.get.mockRejectedValue(failure);
        const warning = vi
            .spyOn(console, "warn")
            .mockImplementation(() => undefined);
        const { service, sources } = createAudioHarness(storage);

        await expect(service.play(customSettings)).resolves.toBeUndefined();
        expect(sources).toEqual([DEFAULT_NOTIFICATION_SOUND_URL]);
        expect(warning).toHaveBeenCalledWith(
            "Unable to load custom notification sound:",
            failure,
        );
    });

    it.each([
        {
            name: "empty file",
            file: new File([], "empty.wav", { type: "audio/wav" }),
            message: "empty",
        },
        {
            name: "unsupported extension",
            file: new File(["audio"], "tone.aac", { type: "audio/aac" }),
            message: ".wav, .mp3, or .ogg",
        },
    ])("rejects $name without touching storage", async ({ file, message }) => {
        const storage = createStorage();
        const { service } = createAudioHarness(storage);
        await expect(service.prepareFile(file)).rejects.toThrow(message);
        expect(storage.replace).not.toHaveBeenCalled();
    });

    it("rejects oversized and undecodable files", async () => {
        const storage = createStorage();
        const large = new File(["audio"], "large.ogg", {
            type: "audio/ogg",
        });
        Object.defineProperty(large, "size", {
            value: MAX_NOTIFICATION_AUDIO_BYTES + 1,
        });
        const first = createAudioHarness(storage);
        await expect(first.service.prepareFile(large)).rejects.toThrow("5 MiB");

        const invalid = new File(["broken"], "broken.wav", {
            type: "audio/wav",
        });
        const second = createAudioHarness(
            storage,
            vi.fn().mockRejectedValue(new Error("cannot decode")),
        );
        await expect(second.service.prepareFile(invalid)).rejects.toThrow(
            "cannot decode",
        );
        expect(storage.replace).not.toHaveBeenCalled();
    });
});
