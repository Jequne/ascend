# Design QA

## Evidence

- Source visual truth:
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-rf2fWk.png` — original Filters settings view.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-TWegcL.png` — original native fee-mode select.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-Jlj04y.png` — requested range-control direction.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-horB27.png` — requested select-menu direction.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-ng6QnK.png` — requested accordion direction.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-KjuiSW.png` — requested card direction.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-nEKreq.png` — original Import / Export view.
- Rendered implementation: `http://127.0.0.1:1420/`.
- Implementation screenshot: `C:\Users\C336~1\AppData\Local\Temp\ascend-design-qa-settings.png`.
- Viewport: 627 × 688 CSS px, device pixel ratio 1.
- Pixel normalization: source and final implementation captures are both 627 × 688 px at 1× density.
- State: authenticated desktop client, Settings dialog open, Filters tab selected, default filter values, auto-open disabled, Axiom selected, optional previous-token override disabled.

## Findings

- No actionable P0, P1, or P2 findings remain.
- Typography: the implementation retains the application's sans-serif stack and compact weights, with a clearer heading hierarchy and readable helper copy at the target viewport.
- Spacing and layout rhythm: dialog dimensions, sticky footer, tab order, and current spacing proportions remain intact. The auto-open copy is geometrically centered, with its switch isolated in a balanced grid column. Token terminal sits directly below it.
- Colors and visual tokens: all surfaces, borders, focus rings, shadows, selected states, and motion use the existing navy, slate, blue, purple, green, and red palette.
- Image and icon fidelity: no new raster imagery was required. Existing product assets remain in use, and interface symbols use the installed Lucide icon set rather than approximate text or custom drawings.
- Copy and content: visible application copy is English. Labels explain the combined core filters, the separate optional performance override, fee-mode behavior, blacklist normalization, and configuration transfer.
- Accessibility and interaction: the custom selects expose combobox/listbox semantics, switches expose checked state, disclosures expose expanded state, tabs retain keyboard navigation, and form controls have stable identifiers and names.

## Full-view comparison evidence

- The original Filters screenshot and the first 627 × 688 implementation capture were opened together in one comparison input.
- The first comparison found a P2 density issue: the Filters field grid collapsed to one column at 627 px, moving important content below the fold compared with the source.
- The final source screenshot and revised 627 × 688 implementation screenshot were opened together again after the fix. The revised two-column core-filter grid restores the intended density while preserving a single-column layout at the 450 × 500 minimum desktop size.

## Focused region comparison evidence

- Select menu: the rendered terminal dropdown was opened and inspected at 640 × 700. It uses a raised dark popover, selected-row treatment, check icon, descriptions, hover/focus states, and correct overlay stacking.
- Optional override: the switch was enabled in the rendered dialog and revealed ATH market-cap and required-token fields without changing the persisted server contract.
- Import / Export: the rendered transfer tab was compared with the provided source. Export is a complete upper section, Import is a complete lower section, and a labeled separator communicates the restore flow.
- Blacklist: realistic entries were entered, the normalized count updated, and the entry list stayed hidden until its disclosure was opened.
- Authentication card: the rendered license form was compared with the supplied form-card reference; the implementation keeps the application palette and uses a stronger bordered, elevated card hierarchy.
- Token card: a realistic token and previous-token record were rendered to inspect the refined card, internal stats surface, and nested last-token row.

## Comparison history

1. P2 — Filters changed to a single column at the 627 px source viewport.
    - Fix: changed the local Filters grid breakpoint from 640 px to 560 px, including its spanning rows and optional-override grid.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-design-qa-settings.png`, recaptured at 627 × 688 and compared together with the source.
    - Result: resolved.
2. P3 — Chrome reported visible form controls without stable identifiers.
    - Fix: added stable `id` and `name` attributes to range, numeric, file, and textarea controls.
    - Result: resolved in source and covered by the final type, lint, and component checks.

## Primary interactions and runtime checks

- Open and close Settings.
- Switch tabs using the rendered controls.
- Open the terminal select and choose GMGN.
- Enable the previous-token performance override.
- Enter blacklist values and reveal the normalized entry list.
- Inspect Import / Export empty and actionable states.
- Verify the sticky Save and Cancel actions at 627 × 688 and 450 × 500.
- Browser console checked: no application exceptions were present; only Vite hot-update debug messages appeared during the responsive fix.

## Implementation checklist

- [x] Center auto-open content and place terminal beneath it.
- [x] Consolidate filter controls and gate the separate performance override.
- [x] Replace native selects with accessible custom menus.
- [x] Replace the range styling and add a numbered scale.
- [x] Stack Export above Import.
- [x] Hide normalized blacklist entries behind a disclosure.
- [x] Preserve the palette and polish card surfaces.
- [x] Verify target and minimum desktop viewport behavior.
- [x] Run format, lint, type checks, tests, and production build.

## Follow-up polish

- None required for handoff.

final result: passed
