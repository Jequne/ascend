import {
    cleanup,
    fireEvent,
    render,
    screen,
    within,
} from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { tick } from "svelte";
import {
    afterAll,
    afterEach,
    beforeAll,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from "vitest";
import { DEFAULT_FILTERS, DEFAULT_NOTIFICATIONS } from "$lib/config/constants";
import { createSettingsExportPayload } from "$lib/config/settings";
import { extensionBridgeService } from "$lib/services/extensionBridge";
import {
    audioNotificationService,
    type PreparedNotificationAudio,
} from "$lib/services/audioNotifications";
import { developerLabelsStore } from "$lib/stores/developerLabels.svelte";
import { filtersStore } from "$lib/stores/filters.svelte";
import { notificationsStore } from "$lib/stores/notifications.svelte";
import TopPanel from "$lib/components/TopPanel.svelte";

const originalShowModal = HTMLDialogElement.prototype.showModal;
const originalClose = HTMLDialogElement.prototype.close;

beforeAll(() => {
    HTMLDialogElement.prototype.showModal = function showModal(): void {
        this.setAttribute("open", "");
    };
    HTMLDialogElement.prototype.close = function close(): void {
        this.removeAttribute("open");
        this.dispatchEvent(new Event("close"));
    };
});

afterAll(() => {
    HTMLDialogElement.prototype.showModal = originalShowModal;
    HTMLDialogElement.prototype.close = originalClose;
});

beforeEach(() => {
    filtersStore.updateFilters(DEFAULT_FILTERS);
    developerLabelsStore.replace({});
    notificationsStore.replace(DEFAULT_NOTIFICATIONS);
});

afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
});

async function openSettings(): Promise<{
    user: ReturnType<typeof userEvent.setup>;
    trigger: HTMLButtonElement;
    dialog: HTMLDialogElement;
}> {
    const user = userEvent.setup();
    render(TopPanel);
    const trigger = screen.getByRole("button", {
        name: "Open settings",
    }) as HTMLButtonElement;

    await user.click(trigger);
    await tick();

    return {
        user,
        trigger,
        dialog: screen.getByRole("dialog", { name: "Settings" }),
    };
}

describe("SettingsDialog", () => {
    it("previews notification drafts and applies them only on Save", async () => {
        const preview = vi
            .spyOn(audioNotificationService, "preview")
            .mockResolvedValue(undefined);
        const first = await openSettings();
        const firstVolume = within(first.dialog).getByLabelText(
            "Notification volume",
        ) as HTMLInputElement;

        firstVolume.value = "35";
        await fireEvent.input(firstVolume);
        await first.user.click(
            within(first.dialog).getByRole("button", { name: "Test sound" }),
        );
        expect(preview).toHaveBeenCalledWith(
            {
                enabled: true,
                volume: 35,
                source: "default",
                customAudioId: null,
                customAudioName: null,
            },
            null,
        );
        await first.user.click(
            within(first.dialog).getByRole("button", { name: "Cancel" }),
        );
        expect(notificationsStore.volume).toBe(70);

        await first.user.click(first.trigger);
        await tick();
        const secondDialog = screen.getByRole("dialog", { name: "Settings" });
        const secondVolume = within(secondDialog).getByLabelText(
            "Notification volume",
        ) as HTMLInputElement;
        secondVolume.value = "42";
        await fireEvent.input(secondVolume);
        await first.user.click(
            within(secondDialog).getByRole("switch", {
                name: "Enable sound notifications",
            }),
        );
        await first.user.click(
            within(secondDialog).getByRole("button", { name: "Save" }),
        );

        expect(notificationsStore.settings).toEqual({
            enabled: false,
            volume: 42,
            source: "default",
            customAudioId: null,
            customAudioName: null,
        });
    });

    it("keeps a selected custom file in draft until Save", async () => {
        const prepared: PreparedNotificationAudio = {
            id: "notification-custom-sound",
            name: "tone.mp3",
            type: "audio/mpeg",
        };
        const prepare = vi
            .spyOn(audioNotificationService, "prepareFile")
            .mockResolvedValue(prepared);
        const saveCustom = vi
            .spyOn(audioNotificationService, "saveCustom")
            .mockResolvedValue(undefined);
        const preview = vi
            .spyOn(audioNotificationService, "preview")
            .mockResolvedValue(undefined);
        const { user, dialog, trigger } = await openSettings();
        const file = new File(["audio"], "tone.mp3", {
            type: "audio/mpeg",
        });

        await user.upload(
            within(dialog).getByLabelText("Choose notification audio file"),
            file,
        );
        expect(
            await within(dialog).findByText(/Selected: tone.mp3/),
        ).toBeVisible();
        expect(prepare).toHaveBeenCalledWith(file);
        await user.click(
            within(dialog).getByRole("button", { name: "Test sound" }),
        );
        expect(preview).toHaveBeenCalledWith(
            expect.objectContaining({ source: "custom" }),
            prepared,
        );
        await user.click(
            within(dialog).getByRole("button", { name: "Cancel" }),
        );
        expect(saveCustom).not.toHaveBeenCalled();
        expect(notificationsStore.settings).toEqual(DEFAULT_NOTIFICATIONS);

        await user.click(trigger);
        const reopened = screen.getByRole("dialog", { name: "Settings" });
        await user.upload(
            within(reopened).getByLabelText("Choose notification audio file"),
            file,
        );
        await user.click(
            within(reopened).getByRole("button", { name: "Save" }),
        );
        expect(saveCustom).toHaveBeenCalledWith(prepared);
        expect(notificationsStore.settings).toMatchObject({
            source: "custom",
            customAudioId: "notification-custom-sound",
            customAudioName: "tone.mp3",
        });
    });

    it("shows file and storage errors without replacing the active sound", async () => {
        const prepare = vi
            .spyOn(audioNotificationService, "prepareFile")
            .mockRejectedValueOnce(new Error("The audio is not playable."))
            .mockResolvedValue({
                id: "notification-custom-sound",
                name: "tone.ogg",
                type: "audio/ogg",
            });
        vi.spyOn(audioNotificationService, "saveCustom").mockRejectedValue(
            new Error("IndexedDB write failed."),
        );
        const { user, dialog } = await openSettings();
        const input = within(dialog).getByLabelText(
            "Choose notification audio file",
        );

        await user.upload(
            input,
            new File(["bad"], "bad.wav", { type: "audio/wav" }),
        );
        expect(await within(dialog).findByRole("alert")).toHaveTextContent(
            "not playable",
        );
        expect(notificationsStore.settings).toEqual(DEFAULT_NOTIFICATIONS);

        await user.upload(
            input,
            new File(["audio"], "tone.ogg", { type: "audio/ogg" }),
        );
        await user.click(within(dialog).getByRole("button", { name: "Save" }));
        expect(await within(dialog).findByRole("alert")).toHaveTextContent(
            "IndexedDB write failed",
        );
        expect(dialog).toHaveAttribute("open");
        expect(notificationsStore.settings).toEqual(DEFAULT_NOTIFICATIONS);
        expect(prepare).toHaveBeenCalledTimes(2);
    });

    it("removes the stored custom file only after saving Use default", async () => {
        notificationsStore.replace({
            ...DEFAULT_NOTIFICATIONS,
            source: "custom",
            customAudioId: "notification-custom-sound",
            customAudioName: "old.wav",
        });
        vi.spyOn(audioNotificationService, "hasCustom").mockResolvedValue(true);
        const remove = vi
            .spyOn(audioNotificationService, "removeCustom")
            .mockResolvedValue(undefined);
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("button", { name: "Use default" }),
        );
        expect(remove).not.toHaveBeenCalled();
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(remove).toHaveBeenCalledWith("notification-custom-sound");
        expect(notificationsStore.settings).toEqual(DEFAULT_NOTIFICATIONS);
    });

    it("supports dialog focus, switch, tab keyboard navigation, and Cancel", async () => {
        const { user, trigger, dialog } = await openSettings();
        const autoOpenGroup = within(dialog).getByRole("radiogroup", {
            name: "Auto-open mode",
        });
        const autoOpenOff = within(autoOpenGroup).getByRole("radio", {
            name: /Off/,
        });
        const autoOpenNewTab = within(autoOpenGroup).getByRole("radio", {
            name: /New tab/,
        });
        const autoOpenCurrentTab = within(autoOpenGroup).getByRole("radio", {
            name: /Current Tab/,
        });
        const migratedHighlight = within(dialog).getByRole("switch", {
            name: "Highlight migrated previous tokens",
        });
        const scrollRegion = within(dialog).getByRole("region", {
            name: "Settings content",
        });

        expect(scrollRegion).toHaveClass("overflow-y-auto");
        expect(scrollRegion).toContainElement(autoOpenGroup);
        expect(autoOpenOff).toHaveFocus();
        expect(autoOpenOff).toHaveAttribute("aria-checked", "true");
        expect(migratedHighlight).toHaveAttribute("aria-checked", "true");
        await user.click(migratedHighlight);
        expect(migratedHighlight).toHaveAttribute("aria-checked", "false");
        await user.click(autoOpenNewTab);
        expect(autoOpenNewTab).toHaveAttribute("aria-checked", "true");

        const terminal = within(dialog).getByRole("radiogroup", {
            name: "Token terminal",
        });
        const axiom = within(terminal).getByRole("radio", {
            name: /Axiom.trade/,
        });
        const gmgn = within(terminal).getByRole("radio", { name: /GMGN/ });
        expect(axiom).toHaveAttribute("aria-checked", "true");
        await user.click(gmgn);
        expect(gmgn).toHaveAttribute("aria-checked", "true");
        await user.keyboard("{ArrowLeft}");
        expect(axiom).toHaveAttribute("aria-checked", "true");
        await user.click(gmgn);
        await user.click(autoOpenCurrentTab);
        await tick();
        expect(autoOpenCurrentTab).toHaveAttribute("aria-checked", "true");
        expect(axiom).toHaveAttribute("aria-checked", "true");
        expect(gmgn).toBeDisabled();
        expect(gmgn).toHaveTextContent("Not yet supported in Current Tab");
        expect(
            within(dialog).queryByText("Not installed / not paired"),
        ).toBeNull();

        const filtersTab = within(dialog).getByRole("tab", {
            name: /Filters/,
        });
        const blacklistTab = within(dialog).getByRole("tab", {
            name: /Blacklist/,
        });
        const labelsTab = within(dialog).getByRole("tab", {
            name: /Dev labels/,
        });
        const transferTab = within(dialog).getByRole("tab", {
            name: /Import \/ Export/,
        });

        expect(scrollRegion).toContainElement(filtersTab);
        expect(scrollRegion).toContainElement(
            within(dialog).getByRole("tabpanel", { name: /Filters/ }),
        );
        expect(filtersTab).toHaveAttribute("aria-selected", "true");
        await user.click(filtersTab);
        await user.keyboard("{ArrowRight}");
        expect(labelsTab).toHaveFocus();
        expect(labelsTab).toHaveAttribute("aria-selected", "true");
        await user.keyboard("{ArrowRight}");
        expect(blacklistTab).toHaveFocus();
        expect(blacklistTab).toHaveAttribute("aria-selected", "true");
        expect(
            within(dialog).getByRole("tabpanel", { name: /Blacklist/ }),
        ).toBeVisible();

        await user.keyboard("{End}");
        expect(transferTab).toHaveFocus();
        expect(transferTab).toHaveAttribute("aria-selected", "true");
        await user.keyboard("{Home}");
        expect(filtersTab).toHaveFocus();

        const migrationInput = within(dialog).getByLabelText(
            /Minimum migration rate/,
        );
        await user.clear(migrationInput);
        await user.type(migrationInput, "42");
        await user.click(
            within(dialog).getByRole("button", { name: "Cancel" }),
        );
        await tick();

        expect(screen.queryByRole("dialog", { name: "Settings" })).toBeNull();
        expect(trigger).toHaveFocus();
        expect(filtersStore.minMigrationPercent).toBe(
            DEFAULT_FILTERS.minMigrationPercent,
        );
        expect(filtersStore.autoOpenMode).toBe("off");
        expect(filtersStore.terminal).toBe(DEFAULT_FILTERS.terminal);
        expect(filtersStore.highlightMigratedTokens).toBe(true);
    });

    it("reveals the optional previous-token override only when enabled", async () => {
        const { user, dialog } = await openSettings();
        const override = within(dialog).getByRole("switch", {
            name: "Enable previous-token performance override",
        });

        expect(override).toHaveAttribute("aria-checked", "false");
        expect(
            within(dialog).queryByLabelText(
                /Minimum previous-token ATH market cap/,
            ),
        ).toBeNull();

        await user.click(override);
        expect(override).toHaveAttribute("aria-checked", "true");
        expect(
            within(dialog).getByLabelText(
                /Minimum previous-token ATH market cap/,
            ),
        ).toBeVisible();

        const requiredTokens = within(dialog).getByLabelText(
            /Required previous tokens/,
        );
        await user.clear(requiredTokens);
        await user.type(requiredTokens, "2");
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(filtersStore.lastTokensRequiredCount).toBe(2);
    });

    it("saves the migrated-token highlight preference", async () => {
        const { user, dialog } = await openSettings();
        const migratedHighlight = within(dialog).getByRole("switch", {
            name: "Highlight migrated previous tokens",
        });

        await user.click(migratedHighlight);
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(filtersStore.highlightMigratedTokens).toBe(false);
    });

    it("opens extension setup separately and restores trigger focus", async () => {
        vi.spyOn(
            extensionBridgeService,
            "prepareInstallation",
        ).mockResolvedValue({
            path: "C:\\Ascend\\ascend-ext-0.1.0",
            version: "0.1.0",
        });
        const { user, dialog } = await openSettings();
        const setupTrigger = within(dialog).getByRole("button", {
            name: /Ascend ext/,
        });

        await user.click(setupTrigger);
        const setup = within(dialog).getByRole("dialog", {
            name: "Set up Ascend ext",
        });
        expect(setup).toBeVisible();
        expect(
            await within(setup).findByText("C:\\Ascend\\ascend-ext-0.1.0"),
        ).toBeVisible();
        expect(
            within(setup).getByText(/One setup for Chrome, Edge, and Brave/),
        ).toBeVisible();
        expect(within(setup).queryByRole("combobox")).toBeNull();
        expect(
            within(setup).queryByRole("button", {
                name: /troubleshooting/i,
            }),
        ).toBeNull();
        expect(
            within(setup).getByRole("button", {
                name: "Open extension folder",
            }),
        ).toHaveFocus();

        await user.click(within(setup).getByRole("button", { name: "Close" }));
        expect(setup).not.toHaveAttribute("open");
        expect(setupTrigger).toHaveFocus();
    });

    it("prepares the extension folder and confirms pairing-code rotation", async () => {
        const pairingCode = "a".repeat(43);
        const nextPairingCode = "b".repeat(43);
        const installation = {
            path: "C:\\Ascend\\ascend-ext-0.1.0",
            version: "0.1.0",
        };
        vi.spyOn(
            extensionBridgeService,
            "prepareInstallation",
        ).mockResolvedValue(installation);
        vi.spyOn(
            extensionBridgeService,
            "openInstallationFolder",
        ).mockResolvedValue(installation);
        vi.spyOn(extensionBridgeService, "getPairingCode").mockResolvedValue(
            pairingCode,
        );
        const rotate = vi
            .spyOn(extensionBridgeService, "rotatePairingCode")
            .mockResolvedValue(nextPairingCode);
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("button", {
                name: /Ascend ext/,
            }),
        );
        const setup = within(dialog).getByRole("dialog", {
            name: "Set up Ascend ext",
        });
        await within(setup).findByText(installation.path);
        await user.click(
            within(setup).getByRole("button", { name: "Show pairing code" }),
        );
        expect(await within(setup).findByText(pairingCode)).toBeVisible();

        await user.click(
            within(setup).getByRole("button", {
                name: "Reset pairing code",
            }),
        );
        expect(rotate).not.toHaveBeenCalled();
        await user.click(
            within(setup).getByRole("button", {
                name: "Confirm reset pairing code",
            }),
        );
        expect(rotate).toHaveBeenCalledOnce();
        expect(await within(setup).findByText(nextPairingCode)).toBeVisible();

        await user.click(
            within(setup).getByRole("button", {
                name: "Open extension folder",
            }),
        );
        expect(
            extensionBridgeService.openInstallationFolder,
        ).toHaveBeenCalledOnce();
    });

    it("updates the developer-holds track as the selected range changes", async () => {
        const { dialog } = await openSettings();
        const minimum = within(dialog).getByLabelText(
            "Minimum developer holds percent",
        ) as HTMLInputElement;
        const maximum = within(dialog).getByLabelText(
            "Maximum developer holds percent",
        ) as HTMLInputElement;

        expect(minimum).toHaveAttribute("min", "0");
        expect(minimum).toHaveValue("0");

        maximum.value = "84.6";
        await fireEvent.input(maximum);
        await tick();

        expect(within(dialog).getByTestId("developer-holds-range")).toHaveStyle(
            "--range-end: 84.6%",
        );
        expect(maximum).toHaveValue("84.6");
    });

    it("normalizes blacklist entries and applies all draft changes on Save", async () => {
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("tab", { name: /Blacklist/ }),
        );
        const blacklist = within(dialog).getByLabelText("Add hidden values");
        await user.type(blacklist, "Wallet-1\n wallet-1 \nToken Name");
        await user.click(within(dialog).getByRole("button", { name: "Add" }));

        expect(
            within(dialog).getByLabelText("2 unique blacklist entries"),
        ).toHaveTextContent("2 unique");
        expect(
            within(dialog).getByRole("list", {
                name: "Normalized blacklist preview",
            }),
        ).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(filtersStore.blacklist).toEqual(["Wallet-1", "Token Name"]);
    });

    it("searches and removes one blacklist entry", async () => {
        filtersStore.blacklist = [
            "Wallet-1",
            "Accidental-wallet",
            "Token Name",
        ];
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("tab", { name: /Blacklist/ }),
        );
        const search = within(dialog).getByLabelText("Search blacklist");
        await user.type(search, "accidental");

        expect(within(dialog).getByText("Accidental-wallet")).toBeVisible();
        expect(within(dialog).queryByText("Wallet-1")).toBeNull();
        await user.click(
            within(dialog).getByRole("button", {
                name: "Remove Accidental-wallet from blacklist",
            }),
        );
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(filtersStore.blacklist).toEqual(["Wallet-1", "Token Name"]);
    });

    it("adds a developer label from settings and persists it on Save", async () => {
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("tab", { name: /Dev labels/ }),
        );
        await user.type(
            within(dialog).getByLabelText("Developer wallet"),
            "dev-wallet",
        );
        await user.type(within(dialog).getByLabelText("Label"), "Reliable dev");
        await user.click(
            within(dialog).getByRole("button", { name: "Add label" }),
        );
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(developerLabelsStore.getLabel("dev-wallet")).toBe(
            "Reliable dev",
        );
    });

    it("requires confirmation before clearing all blacklist entries", async () => {
        filtersStore.blacklist = ["Wallet-1", "Token Name"];
        const { user, dialog } = await openSettings();

        await user.click(
            within(dialog).getByRole("tab", { name: /Blacklist/ }),
        );
        await user.click(
            within(dialog).getByRole("button", { name: "Clear blacklist" }),
        );

        const confirmation = within(dialog).getByRole("dialog", {
            name: "Clear the entire blacklist?",
        });
        expect(confirmation).toHaveTextContent(
            "cannot be restored unless you exported your settings first",
        );
        await user.click(
            within(confirmation).getByRole("button", { name: "Keep values" }),
        );
        expect(
            within(dialog).getByLabelText("2 unique blacklist entries"),
        ).toBeVisible();

        await user.click(
            within(dialog).getByRole("button", { name: "Clear blacklist" }),
        );
        await user.click(
            within(dialog).getByRole("button", {
                name: "Clear permanently",
            }),
        );
        expect(
            within(dialog).getByLabelText("0 unique blacklist entries"),
        ).toBeVisible();

        await user.click(within(dialog).getByRole("button", { name: "Save" }));
        expect(filtersStore.blacklist).toEqual([]);
    });

    it("copies, downloads, pastes, and uploads settings without bypassing Save", async () => {
        const { user, dialog } = await openSettings();
        const writeText = vi
            .fn<(value: string) => Promise<void>>()
            .mockResolvedValue();
        const createObjectUrl = vi
            .spyOn(URL, "createObjectURL")
            .mockReturnValue("blob:settings");
        const revokeObjectUrl = vi
            .spyOn(URL, "revokeObjectURL")
            .mockImplementation(() => undefined);
        const anchorClick = vi
            .spyOn(HTMLAnchorElement.prototype, "click")
            .mockImplementation(() => undefined);
        Object.defineProperty(navigator, "clipboard", {
            configurable: true,
            value: { writeText },
        });

        await user.click(
            within(dialog).getByRole("tab", { name: /Import \/ Export/ }),
        );
        await user.click(
            within(dialog).getByRole("button", { name: "Copy JSON" }),
        );
        expect(writeText).toHaveBeenCalledOnce();
        expect(writeText.mock.calls[0]?.[0]).toContain('"schemaVersion": 5');

        await user.click(
            within(dialog).getByRole("button", { name: "Download JSON" }),
        );
        expect(createObjectUrl).toHaveBeenCalledOnce();
        expect(anchorClick).toHaveBeenCalledOnce();
        expect(revokeObjectUrl).toHaveBeenCalledWith("blob:settings");

        const pastedPayload = JSON.stringify(
            createSettingsExportPayload({
                filters: {
                    ...DEFAULT_FILTERS,
                    minMigrationPercent: 73,
                },
            }),
        );
        const importArea = within(dialog).getByLabelText("Settings JSON");
        await user.click(importArea);
        await user.paste(pastedPayload);
        await user.click(
            within(dialog).getByRole("button", {
                name: "Import pasted JSON",
            }),
        );

        expect(filtersStore.minMigrationPercent).toBe(
            DEFAULT_FILTERS.minMigrationPercent,
        );
        expect(within(dialog).getByRole("status")).toHaveTextContent(
            "Settings loaded into the draft",
        );

        const uploadedPayload = JSON.stringify(
            createSettingsExportPayload({
                filters: {
                    ...DEFAULT_FILTERS,
                    minMigrationPercent: 81,
                    blacklist: ["uploaded-wallet"],
                },
                developerLabels: {
                    "uploaded-dev": "Imported label",
                },
                notifications: {
                    ...DEFAULT_NOTIFICATIONS,
                    source: "custom",
                    customAudioId: "notification-custom-sound",
                    customAudioName: "missing-device-sound.ogg",
                },
            }),
        );
        vi.spyOn(audioNotificationService, "hasCustom").mockResolvedValue(
            false,
        );
        const file = new File([uploadedPayload], "settings.json", {
            type: "application/json",
        });
        Object.defineProperty(file, "text", {
            value: async () => uploadedPayload,
        });
        await user.upload(
            within(dialog).getByLabelText("Choose .json file"),
            file,
        );
        await screen.findByText(
            "Settings loaded into the draft. Press Save to apply them.",
        );
        expect(
            await within(dialog).findByText(/unavailable on this device/),
        ).toBeVisible();

        await user.click(within(dialog).getByRole("button", { name: "Save" }));
        expect(filtersStore.minMigrationPercent).toBe(81);
        expect(filtersStore.blacklist).toEqual(["uploaded-wallet"]);
        expect(developerLabelsStore.getLabel("uploaded-dev")).toBe(
            "Imported label",
        );
        expect(notificationsStore.settings).toMatchObject({
            source: "custom",
            customAudioName: "missing-device-sound.ogg",
        });
    });
});
