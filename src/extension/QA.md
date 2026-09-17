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
