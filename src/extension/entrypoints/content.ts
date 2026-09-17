import { browser } from "wxt/browser";
import { defineContentScript } from "wxt/utils/define-content-script";
import { navigateWithAxiomHistory } from "../lib/navigation/axiom-spa-adapter";
import { navigateInContent } from "../lib/navigation/content-navigation";
import { parseContentNavigateRequest } from "../lib/protocol/messages";

export default defineContentScript({
    matches: ["https://axiom.trade/*"],
    main() {
        browser.runtime.onMessage.addListener(
            (message, _sender, sendResponse) => {
                const request = parseContentNavigateRequest(message);
                if (!request) return false;

                void navigateInContent(request, {
                    getCurrentUrl: () => window.location.href,
                    tryHistoryNavigation: navigateWithAxiomHistory,
                }).then(sendResponse);
                return true;
            },
        );
    },
});
