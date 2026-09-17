import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "wxt";

const DEVELOPMENT_KEY =
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApROwyeIUWM/Aj/KcmCJUXg/tIZxy86OZWrRX5kDDf+nz1IX2IcBQrPJhNp8t+m7JSeRvYbqDSQqiNaGP6sokf0W0QWpVCfvdxDmjMv3Qs0WIZdgizwvl5vFAaqzWEBRKQ93RkYGsmgrQ8DdD4c74qqD56lTFd7alW3dP6Tgpq/I6EtdjoD+MGrhS22WR+VNhQ+U3e34sVwwGt04NFbHb6UeUmWIDyku6D4+QXDyzqneM+0aXF2SJwfAZV0b05D+y+Cgore0C7LCZYkODe1E7yJPIe4J6p8Frvf5HtWf8U9NoEJpXg/2BS3s2P0qUYGB7s7BwC4cCGLBLCPbpQRSO2QIDAQAB";

export default defineConfig({
    manifestVersion: 3,
    modules: ["@wxt-dev/module-svelte"],
    manifest: {
        name: "Ascend ext",
        description: "Open Ascend token signals in a selected Axiom tab.",
        minimum_chrome_version: "116",
        key: DEVELOPMENT_KEY,
        incognito: "not_allowed",
        permissions: ["storage", "tabs"],
        host_permissions: ["https://axiom.trade/*"],
        content_security_policy: {
            extension_pages: "script-src 'self'; object-src 'self';",
        },
        icons: {
            16: "icon/16.png",
            32: "icon/32.png",
            48: "icon/48.png",
            128: "icon/128.png",
        },
        action: {
            default_title: "Ascend ext",
            default_icon: {
                16: "icon/16.png",
                32: "icon/32.png",
                48: "icon/48.png",
                128: "icon/128.png",
            },
        },
    },
    vite: () => ({
        plugins: [tailwindcss()],
    }),
});
