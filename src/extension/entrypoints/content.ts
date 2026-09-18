import { browser } from "wxt/browser";
import { defineContentScript } from "wxt/utils/define-content-script";
import { navigateWithAxiomHistory } from "../lib/navigation/axiom-spa-adapter";
import { navigateInContent } from "../lib/navigation/content-navigation";
import { parseContentNavigateRequest } from "../lib/protocol/messages";

export default defineContentScript({
    matches: ["https://axiom.trade/*"],
    main() {
        let activeNavigation: AbortController | null = null;

        browser.runtime.onMessage.addListener(
            (message, _sender, sendResponse) => {
                const request = parseContentNavigateRequest(message);
                if (!request) return false;

                activeNavigation?.abort();
                const controller = new AbortController();
                activeNavigation = controller;
                void navigateInContent(request, {
                    getCurrentUrl: () => window.location.href,
                    tryHistoryNavigation: (url) =>
                        navigateWithAxiomHistory(url, controller.signal),
                }).then((result) => {
                    if (activeNavigation === controller) {
                        activeNavigation = null;
                    }
                    sendResponse(result);
                });
                return true;
            },
        );
    },
});
