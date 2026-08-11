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
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-m4jKFT.png` — follow-up Auto-open and terminal-selector issue at 609 × 188.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-qEUi9C.png` — follow-up native number-spinner issue at 282 × 85.
    - `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-OfHzal.png` — follow-up top-control styling issue at 444 × 99.
- Rendered implementation: `http://127.0.0.1:1420/`.
- Implementation screenshot: `C:\Users\C336~1\AppData\Local\Temp\ascend-design-qa-settings.png`.
- Follow-up implementation screenshots:
    - `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-settings.png` — full Settings view at 627 × 688.
    - `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-auto-open.png` — focused Auto-open region at 605 × 168.
    - `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-top-panel.png` — top-panel state at 627 × 688.
- Viewport: 627 × 688 CSS px, device pixel ratio 1.
- Pixel normalization: source and final implementation captures are both 627 × 688 px at 1× density.
- State: authenticated desktop client, Settings dialog open, Filters tab selected, default filter values, auto-open disabled, Axiom selected, optional previous-token override disabled. GMGN-selected and top-control hover states were also captured and inspected.

## Findings

- No actionable P0, P1, or P2 findings remain.
- Typography: the implementation retains the application's sans-serif stack and compact weights, with a clearer heading hierarchy and readable helper copy at the target viewport.
- Spacing and layout rhythm: dialog dimensions, sticky footer, tab order, and current spacing proportions remain intact. The auto-open copy is geometrically centered, with its switch isolated in a balanced grid column. Token terminal sits directly below it.
- Colors and visual tokens: all surfaces, borders, focus rings, shadows, selected states, and motion use the existing navy, slate, blue, purple, green, and red palette.
- Image and icon fidelity: no new raster imagery was required. Existing product assets remain in use, and interface symbols use the installed Lucide icon set rather than approximate text or custom drawings.
- Copy and content: visible application copy is English. Labels explain the combined core filters, the separate optional performance override, fee-mode behavior, blacklist normalization, and configuration transfer.
- Accessibility and interaction: the custom selects expose combobox/listbox semantics, switches expose checked state, disclosures expose expanded state, tabs retain keyboard navigation, and form controls have stable identifiers and names.
- Follow-up terminal selection: Axiom.trade and GMGN are now large branded radio controls using official service assets. A single selected surface animates between them and honors reduced-motion preferences.
- Follow-up numeric fields: browser number spinners are removed consistently while numeric input behavior remains unchanged.
- Follow-up top controls: gradients, outer glow, and translate-on-hover motion were removed. Hover now changes only border, foreground, and surface colors with a small inset highlight.

## Full-view comparison evidence

- The original Filters screenshot and the first 627 × 688 implementation capture were opened together in one comparison input.
- The first comparison found a P2 density issue: the Filters field grid collapsed to one column at 627 px, moving important content below the fold compared with the source.
- The final source screenshot and revised 627 × 688 implementation screenshot were opened together again after the fix. The revised two-column core-filter grid restores the intended density while preserving a single-column layout at the 450 × 500 minimum desktop size.
- The follow-up Auto-open source and the 605 × 168 implementation region were opened together. The new composition fills the available width, reduces unused margins, and preserves the existing information order.
- The follow-up number-field source and final 627 × 688 Settings implementation were opened together. Spinner arrows are absent and the Developer holds scale starts at 0.1.
- The follow-up top-control source and rendered top-panel state were opened together. Control sizes are slightly larger while the visual treatment is flatter and calmer.

## Focused region comparison evidence

- Select menu: the rendered terminal dropdown was opened and inspected at 640 × 700. It uses a raised dark popover, selected-row treatment, check icon, descriptions, hover/focus states, and correct overlay stacking.
- Optional override: the switch was enabled in the rendered dialog and revealed ATH market-cap and required-token fields without changing the persisted server contract.
- Import / Export: the rendered transfer tab was compared with the provided source. Export is a complete upper section, Import is a complete lower section, and a labeled separator communicates the restore flow.
- Blacklist: realistic entries were entered, the normalized count updated, and the entry list stayed hidden until its disclosure was opened.
- Authentication card: the rendered license form was compared with the supplied form-card reference; the implementation keeps the application palette and uses a stronger bordered, elevated card hierarchy.
- Token card: a realistic token and previous-token record were rendered to inspect the refined card, internal stats surface, and nested last-token row.
- Terminal selector: both official SVG marks were inspected at their rendered size. The Axiom and GMGN selected states were captured, and the indicator's computed translation was sampled during animation.
- Top controls: the Offline control was inspected at hover; computed style confirmed no transform and no outer shadow.

## Comparison history

1. P2 — Filters changed to a single column at the 627 px source viewport.
    - Fix: changed the local Filters grid breakpoint from 640 px to 560 px, including its spanning rows and optional-override grid.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-design-qa-settings.png`, recaptured at 627 × 688 and compared together with the source.
    - Result: resolved.
2. P3 — Chrome reported visible form controls without stable identifiers.
    - Fix: added stable `id` and `name` attributes to range, numeric, file, and textarea controls.
    - Result: resolved in source and covered by the final type, lint, and component checks.
3. P2 — Follow-up terminal selector used a compact dropdown and left excessive unused horizontal space.
    - Fix: replaced it with two large branded radio buttons and a shared animated selection surface; widened and left-aligned the Auto-open row.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-auto-open.png`, compared together with the 609 × 188 source.
    - Result: resolved.
4. P2 — Developer holds displayed 0 instead of the configured 0.1 minimum, and numeric fields exposed native spinner controls.
    - Fix: changed the first visible range mark to 0.1 and suppressed WebKit and Firefox number spinners in the shared base layer.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-settings.png`.
    - Result: resolved.
5. P2 — Top controls used glowing gradients and vertical hover movement.
    - Fix: replaced the treatment with flat current-palette surfaces, subtle borders, color-only hover/active states, and 42 px control sizing.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-followup-top-panel.png`; hover computed with `transform: none` and no outer shadow.
    - Result: resolved.

## Primary interactions and runtime checks

- Open and close Settings.
- Switch tabs using the rendered controls.
- Open the terminal select and choose GMGN.
- Enable the previous-token performance override.
- Enter blacklist values and reveal the normalized entry list.
- Inspect Import / Export empty and actionable states.
- Verify the sticky Save and Cancel actions at 627 × 688 and 450 × 500.
- Switch Axiom.trade and GMGN by click and arrow keys; verify radio state, animated interpolation, and reduced-motion class.
- Inspect the top Offline control at hover and verify it does not move or glow.
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
- [x] Replace terminal dropdown with official branded radio controls and animated selection.
- [x] Correct the 0.1 range label and remove native number spinners.
- [x] Restyle top controls with larger, flat shadcn-like interactions.

## Follow-up polish

- None required for handoff.

final result: passed

## Migrated-token highlight follow-up

### Evidence

- Source visual truth: `C:\Users\C336~1\AppData\Local\Temp\codex-clipboard-Ga1J6X.png` (411 x 371 px).
- Highlight-on implementation: `C:\Users\C336~1\AppData\Local\Temp\ascend-migrated-card-on-final.png` (500 x 500 px).
- Settings implementation: `C:\Users\C336~1\AppData\Local\Temp\ascend-migrated-setting.png` (500 x 500 px).
- Highlight-off implementation: `C:\Users\C336~1\AppData\Local\Temp\ascend-migrated-card-off.png` (500 x 500 px).
- CSS viewport: 500 x 500 px at device pixel ratio 1.
- Normalization: the supplied source is a cropped 411 x 371 product region, so the comparison used the matching token-card content region rather than browser-frame dimensions.
- State: authenticated token feed with one current token and three previous tokens; two previous tokens are migrated.

### Findings

- No actionable P0, P1, or P2 findings remain.
- Typography and copy: the 24 px `M` badge is immediately scannable without competing with token names, while the setting title and helper text explain the effect directly.
- Spacing and layout rhythm: the badge sits inline with the token identity and does not shift metrics or action icons. The new setting remains within the existing auto-open panel and preserves its proportions.
- Colors and visual tokens: migrated rows use a restrained emerald border and translucent tint from the existing palette. The non-migrated row is unchanged.
- Image quality and asset fidelity: token imagery and existing service assets are unchanged; the migration status is semantic text rather than a substituted product asset.
- Accessibility and behavior: the badge exposes `Migrated token`, the setting is a labeled switch, and turning the tint off leaves the persistent `M` status marker visible.

### Full-view comparison evidence

- The supplied token-card screenshot and `ascend-migrated-card-on-final.png` were opened together in one comparison input.
- The implementation preserves the source hierarchy and density while making migrated rows distinguishable through both shape/text and a low-intensity color treatment.
- The wider implementation frame contains the same product region plus the existing top controls; that crop difference was excluded from fidelity judgments.

### Focused region comparison evidence

- The three previous-token rows were inspected together: Octopus remains neutral, while Asset and Hopecoin receive the tint and 24 px `M` badge.
- The highlight-off capture confirms that only the tint is removed; migrated identity remains visible through `M`.
- The Settings capture confirms the switch is directly below terminal selection and does not disturb the tabs or filter layout.

### Comparison history

1. P2 - The original migrated check was too small and visually ambiguous.
    - Fix: replaced it with a clear `M` badge and added an optional subtle row tint.
    - Initial post-fix evidence showed the correct behavior but the badge was still less prominent than requested.
    - Final fix: increased the badge to 24 px while retaining compact typography and the existing palette.
    - Post-fix evidence: `C:\Users\C336~1\AppData\Local\Temp\ascend-migrated-card-on-final.png`, compared together with the source.
    - Result: resolved.

### Primary interactions and runtime checks

- Toggle migrated-token highlighting in Settings and save.
- Confirm migrated rows update immediately after Save.
- Confirm the `M` badge remains when highlighting is disabled.
- Confirm only migrated previous-token rows receive the tint.
- Browser console checked after interaction: no warnings, errors, or issues.

### Implementation checklist

- [x] Add an explicit migration badge to migrated previous tokens.
- [x] Add a restrained migrated-row highlight.
- [x] Add a persisted general setting below terminal selection.
- [x] Preserve the migration badge when highlighting is disabled.
- [x] Verify both rendered states and browser console.

final result: passed
