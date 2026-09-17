import { defineContentScript } from "wxt/utils/define-content-script";
import { installAxiomMainWorldNavigation } from "../lib/navigation/axiom-main-world";

export default defineContentScript({
    matches: ["https://axiom.trade/*"],
    world: "MAIN",
    main() {
        installAxiomMainWorldNavigation();
    },
});
