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
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { createSettingsExportPayload } from "$lib/config/settings";
import { filtersStore } from "$lib/stores/filters.svelte";
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
    it("supports dialog focus, switch, tab keyboard navigation, and Cancel", async () => {
        const { user, trigger, dialog } = await openSettings();
        const autoOpen = within(dialog).getByRole("switch", {
            name: "Automatically open accepted tokens",
        });
        const migratedHighlight = within(dialog).getByRole("switch", {
            name: "Highlight migrated previous tokens",
        });

        expect(autoOpen).toHaveFocus();
        expect(autoOpen).toHaveAttribute("aria-checked", "false");
        expect(migratedHighlight).toHaveAttribute("aria-checked", "true");
        await user.click(migratedHighlight);
        expect(migratedHighlight).toHaveAttribute("aria-checked", "false");
        await user.click(autoOpen);
        expect(autoOpen).toHaveAttribute("aria-checked", "true");

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

        const filtersTab = within(dialog).getByRole("tab", {
            name: /Filters/,
        });
        const blacklistTab = within(dialog).getByRole("tab", {
            name: /Blacklist/,
        });
        const transferTab = within(dialog).getByRole("tab", {
            name: /Import \/ Export/,
        });

        expect(filtersTab).toHaveAttribute("aria-selected", "true");
        await user.click(filtersTab);
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
        expect(filtersStore.autoOpenInNewTab).toBe(false);
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

    it("updates the developer-holds track as the selected range changes", async () => {
        const { dialog } = await openSettings();
        const maximum = within(dialog).getByLabelText(
            "Maximum developer holds percent",
        ) as HTMLInputElement;

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
            within(dialog).queryByRole("list", {
                name: "Normalized blacklist preview",
            }),
        ).toBeNull();
        await user.click(
            within(dialog).getByRole("button", {
                name: /Show 2 blacklist entries/,
            }),
        );
        expect(
            within(dialog).getByRole("list", {
                name: "Normalized blacklist preview",
            }),
        ).toBeVisible();
        await user.click(within(dialog).getByRole("button", { name: "Save" }));

        expect(filtersStore.blacklist).toEqual(["Wallet-1", "Token Name"]);
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
        expect(writeText.mock.calls[0]?.[0]).toContain('"schemaVersion": 2');

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
            }),
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

        await user.click(within(dialog).getByRole("button", { name: "Save" }));
        expect(filtersStore.minMigrationPercent).toBe(81);
        expect(filtersStore.blacklist).toEqual(["uploaded-wallet"]);
    });
});
