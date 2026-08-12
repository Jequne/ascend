# Design QA

- Source visual truth: user-provided token-card, blacklist-panel, and developer-holds screenshots from 2026-08-12.
- Implementation: browser-rendered `http://127.0.0.1:4173/` desktop client.
- Viewports: 500 x 300 CSS px for the token card; 660 x 760 CSS px for settings.
- Source pixels: token card 419 x 188, blacklist 381 x 218, developer holds 392 x 116.
- Implementation pixels: token card 500 x 300, settings 660 x 760 at device scale factor 1.
- Density normalization: CSS pixel captures at device scale factor 1; focused regions were compared by component proportions because the source crops omit the surrounding application chrome.
- States: populated token card, blacklist with three saved values and empty additive form, developer-holds range at 0.1–84.6%, and clear-blacklist confirmation dialog.

## Full-view comparison evidence

The browser-rendered token card preserves the original palette, content order, card proportions, badges, and statistics row. The token image is larger, and the blacklist action is a compact rounded square aligned to the full main-info row. The settings dialog preserves its existing desktop structure while replacing the populated editor with an additive multiline form and a separate collapsed saved-values list.

## Focused region comparison evidence

- Token header: compared directly against the supplied token-card crop. Image scale and blacklist-button geometry match the requested changes without widening or reordering the card.
- Developer holds: compared directly against the supplied range crop at 0.1–84.6%. The selected interval is blue and the remaining interval is visibly gray.
- Blacklist: compared directly against the supplied panel crop. Saved values no longer occupy the editor; the form is empty after adding, the normalized list is separately expandable, and destructive clearing opens a modal warning.

## Findings

No actionable P0, P1, or P2 differences remain.

- Fonts and typography: existing system font, weights, sizes, hierarchy, wrapping, and compact labels are preserved.
- Spacing and layout rhythm: original card and settings structure remain intact; the larger image and square action fit without overflow at the tested widths.
- Colors and visual tokens: existing dark palette and semantic green, orange, blue, purple, and red accents are preserved. The range remainder uses a neutral gray distinct from the blue selection.
- Image quality and asset fidelity: the existing real token-image pipeline is preserved; no placeholder or code-drawn image asset was introduced.
- Copy and content: new blacklist instructions specify one value per line, and the confirmation clearly states that clearing is not recoverable without an exported settings file.

## Interaction and browser checks

- Opened Settings and switched between Filters and Blacklist tabs.
- Changed the developer-holds maximum to 84.6 and verified immediate track and output updates.
- Pasted three lines, added them, and verified the editor reset while the saved count and collapsed list updated.
- Opened the clear confirmation and verified the safe action receives focus.
- Verified the token card at the narrow desktop-client width.
- Browser console: no warnings or errors.

## Comparison history

1. P1: the maximum range thumb moved but the blue track remained at 100%. Root cause was a non-reactive style expression hidden behind helper functions. Fixed by deriving reactive range values and binding them directly to the CSS custom properties.
2. Post-fix evidence: browser capture at 0.1–84.6% shows blue through the maximum thumb and gray from 84.6% to 100%; the accessible output also reports 0.1–84.6%.

## Follow-up polish

No P3 follow-up is required for this checkpoint.

final result: passed
