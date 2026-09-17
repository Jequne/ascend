(() => {
    const existing = globalThis.__ascendAxiomProbe;
    if (existing && typeof existing.stop === "function") existing.stop();

    const observations = [];
    const networkParameters = [
        "chain",
        "chains",
        "pulseChains",
        "trackerChains",
        "discoverChains",
    ];
    const ignoredDispatchEvents = new Set([
        "click",
        "pointerdown",
        "pointerup",
        "mousedown",
        "mouseup",
        "mousemove",
        "keydown",
        "keyup",
        "input",
        "change",
        "focus",
        "blur",
    ]);
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    const originalDispatchEvent = EventTarget.prototype.dispatchEvent;
    const timers = new Set();

    const sanitizeUrl = (value) => {
        try {
            const url = new URL(String(value), location.href);
            if (url.origin !== "https://axiom.trade") return url.origin;
            const safe = new URL(`${url.origin}${url.pathname}`);
            for (const name of networkParameters) {
                for (const parameterValue of url.searchParams.getAll(name)) {
                    safe.searchParams.append(name, parameterValue);
                }
            }
            return safe.toString();
        } catch {
            return "invalid-url";
        }
    };

    const record = (observation) => {
        if (observations.length >= 500) observations.shift();
        observations.push({
            at: new Date().toISOString(),
            ...observation,
        });
    };

    const captureRenderState = (source, delayMs) => {
        const address = location.pathname.startsWith("/meme/")
            ? location.pathname.slice("/meme/".length).split("/")[0]
            : "";
        const addressAttributes = [];
        if (address) {
            for (const element of document.querySelectorAll("body *")) {
                for (const attribute of element.attributes) {
                    if (!attribute.value.includes(address)) continue;
                    addressAttributes.push({
                        tag: element.tagName.toLowerCase(),
                        attribute: attribute.name,
                        value:
                            attribute.name === "href"
                                ? sanitizeUrl(attribute.value)
                                : "<pair_address>",
                    });
                    if (addressAttributes.length >= 30) break;
                }
                if (addressAttributes.length >= 30) break;
            }
        }
        record({
            kind: "render-state",
            source,
            delayMs,
            url: sanitizeUrl(location.href),
            title: document.title.slice(0, 160),
            readyState: document.readyState,
            mainCount: document.querySelectorAll("main").length,
            headingCount: document.querySelectorAll("h1, h2").length,
            busyCount: document.querySelectorAll(
                '[aria-busy="true"], [role="progressbar"]',
            ).length,
            bodyContainsPairAddress: Boolean(
                address && document.body?.textContent?.includes(address),
            ),
            addressAttributes,
        });
    };

    const scheduleRenderStates = (source) => {
        for (const delayMs of [0, 100, 300, 750, 1500, 3000]) {
            const timer = setTimeout(() => {
                timers.delete(timer);
                captureRenderState(source, delayMs);
            }, delayMs);
            timers.add(timer);
        }
    };

    const onClick = (event) => {
        const path = event.composedPath();
        const anchor = path.find((node) => node instanceof HTMLAnchorElement);
        const target = path.find((node) => node instanceof Element);
        record({
            kind: "captured-click",
            targetTag:
                target instanceof Element
                    ? target.tagName.toLowerCase()
                    : "unknown",
            targetRole:
                target instanceof Element ? target.getAttribute("role") : null,
            anchorHref:
                anchor instanceof HTMLAnchorElement
                    ? sanitizeUrl(anchor.href)
                    : null,
            anchorRole:
                anchor instanceof HTMLAnchorElement
                    ? anchor.getAttribute("role")
                    : null,
            anchorDataAttributes:
                anchor instanceof HTMLAnchorElement
                    ? [...anchor.attributes]
                          .map((attribute) => attribute.name)
                          .filter((name) => name.startsWith("data-"))
                    : [],
        });
    };

    const onPopState = () => {
        record({
            kind: "observed-event",
            eventType: "popstate",
            url: sanitizeUrl(location.href),
        });
        scheduleRenderStates("popstate");
    };

    const onHashChange = () => {
        record({
            kind: "observed-event",
            eventType: "hashchange",
            url: sanitizeUrl(location.href),
        });
        scheduleRenderStates("hashchange");
    };

    history.pushState = function (state, unused, url) {
        record({
            kind: "history-call",
            method: "pushState",
            url: sanitizeUrl(url),
        });
        const result = originalPushState.call(this, state, unused, url);
        scheduleRenderStates("pushState");
        return result;
    };

    history.replaceState = function (state, unused, url) {
        record({
            kind: "history-call",
            method: "replaceState",
            url: sanitizeUrl(url),
        });
        const result = originalReplaceState.call(this, state, unused, url);
        scheduleRenderStates("replaceState");
        return result;
    };

    EventTarget.prototype.dispatchEvent = function (event) {
        if (
            (this === window || this === document) &&
            !ignoredDispatchEvents.has(event.type)
        ) {
            record({
                kind: "dispatched-event",
                target: this === window ? "window" : "document",
                eventType: event.type,
                url: sanitizeUrl(location.href),
            });
        }
        return originalDispatchEvent.call(this, event);
    };

    document.addEventListener("click", onClick, true);
    window.addEventListener("popstate", onPopState);
    window.addEventListener("hashchange", onHashChange);
    captureRenderState("installed", 0);

    globalThis.__ascendAxiomProbe = {
        report: () => JSON.stringify(observations, null, 2),
        stop: () => {
            history.pushState = originalPushState;
            history.replaceState = originalReplaceState;
            EventTarget.prototype.dispatchEvent = originalDispatchEvent;
            document.removeEventListener("click", onClick, true);
            window.removeEventListener("popstate", onPopState);
            window.removeEventListener("hashchange", onHashChange);
            for (const timer of timers) clearTimeout(timer);
            timers.clear();
        },
    };

    console.info("Axiom navigation probe is recording.");
})();
