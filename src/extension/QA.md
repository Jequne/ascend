# Ascend ext QA

## Stage 1 — Axiom target tab foundation

Status: ready for the extension-only scope. Desktop pairing and token-feed integration belong to Stage 2.

### Real Axiom navigation research

Date: 2026-09-17
Environment: an authenticated Axiom session in regular Google Chrome on Windows. The isolated Playwright profile was rejected by Axiom anti-fraud, so the observation probe was run manually in the regular browser. No cookies, local storage, form values, wallet data, or screenshots were collected.

Observed sequence:

1. Opened Pulse with the five network parameters used by Axiom.
2. Opened pair `F8qFEucvUF9govRejz9zHeUwFEbB8MKnrG4bRDnzkgLT` through the normal Axiom card interaction.
3. Returned to Pulse and opened pair `5UtFH1yNsd4tuTFHRiQNdJaDYKroeSCBg5BekdSa59pD` through the normal Axiom card interaction.
4. Tested a direct `history.pushState` to the first verified token URL.
5. Repeated the test with `history.pushState`, preserving the current history state, followed by `window.dispatchEvent(new PopStateEvent("popstate", { state: history.state }))`.

Findings:

- The token-card click target was a `div`, not an anchor with a reusable token URL.
- A normal card transition called `history.pushState`, followed by `history.replaceState` about 20–40 ms later.
- No `popstate`, `hashchange`, or separate event dispatched on `window` or `document` accompanied the transition.
- A direct `history.pushState` changed the address but did not rerender the token view.
- Dispatching `popstate` immediately after `pushState` caused Axiom to render the requested token view without a document reload.
- During a real router transition, the semantic loading state appeared through `aria-busy="true"` or `role="progressbar"` and then disappeared. The document title subsequently changed to a token title ending in `| Axiom SOL`.
- The URL used the pair address in `/meme/<pair_address>` and preserved `chain`, `chains`, `pulseChains`, `trackerChains`, and `discoverChains`.

Decision:

- Run the confirmed `pushState` and `popstate` pair in the page's MAIN world so Axiom's router receives the event.
- Preserve `history.state`, validate the URL again in the MAIN world, and wait for both the semantic loading cycle and the token-title change before reporting completion.
- Do not call private router code or depend on minified classes. If the SPA transition cannot be confirmed, fail the command without reloading, creating a tab, or changing focus.

The reusable manual probe is in `e2e/manual/axiom-navigation-probe.js`.

### Automated coverage

Unit and component coverage:

- exact Axiom origin, port, credentials, path, fragment, chain, and query allowlist;
- malformed internal messages and content-script responses;
- target assignment, session restoration, target closure, and leaving Axiom;
- popup start/stop eligibility, paused state, accessible text, and disabled state;
- one active navigation, one pending slot, `latest wins`, command deduplication, pending cleanup, and recovery after failure;
- already-open handling, cross-world message validation, confirmed SPA navigation, and rejection without reload side effects.

Playwright runs the production unpacked extension in a persistent Chromium profile against a fixture served on the exact `https://axiom.trade` origin. Covered scenarios:

- explicit target selection;
- rejection of a lookalike origin;
- `pushState` plus `popstate` navigation with the same document identity, no new tab, and no focus change;
- target closure and `target_missing`;
- burst commands with only the latest pending URL retained;
- repeated `commandId` without repeated navigation;
- already-open URL handling.

### Completed checks

```text
npm run format:check
npm run lint
npm run check
npm run test        # 45 tests passed
npm run build
npm run test:e2e    # 2 tests passed
```

The production manifest was inspected after the build: Manifest V3, Chrome 116 minimum, exact Axiom host access, `storage` and `tabs` permissions only, no web-accessible remote code, and an extension-page CSP restricted to bundled scripts.

## Stage 2 — secure desktop integration

Status: automated Stage 2 coverage is complete. Packaging the extension as a Tauri resource and the final Chrome, Edge, and Brave manual matrix remain in Stage 3.

Coverage added on 2026-09-18:

- the Rust bridge binds the fixed loopback address, checks the exact extension Origin, pairing secret, protocol version, and extension version before exposing state;
- pairing secrets are generated from 256 bits of operating-system randomness, persist in app data, survive restart, and are revoked by rotation;
- malformed messages, binary frames, unsafe Axiom URLs, invalid UUIDs, invalid timestamps, duplicate command IDs, and unknown navigation results are rejected without navigation;
- the extension waits for the authenticated state before reporting pairing success, sends heartbeats, reconnects with bounded exponential backoff and jitter, and stops retrying on pairing or version rejection;
- settings migrate v1, v2, and legacy values to schema v3 and preserve all three `AutoOpenMode` values;
- accepted feeds dispatch exactly once to the selected path: the existing Axiom/GMGN system opener for `new_tab`, the bridge for `current_axiom_tab`, and no side effect for `off`;
- desktop and popup mode changes synchronize in both directions without falling back to `new_tab` when the extension is unavailable;
- Playwright starts a loopback mock bridge that verifies the extension Origin and pairing handshake, confirms `set_mode`, sends real `navigate` protocol messages, and receives correlated navigation results.

Completed Stage 2 checks:

```text
Client:
npm run format:check
npm run lint
npm run check
npm run test        # 67 tests passed
npm run build

Extension:
npm run format:check
npm run lint
npm run check
npm run test        # 62 tests passed
npm run build
npm run test:e2e    # 2 tests passed

Rust:
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test          # 9 tests passed
cargo check
```
