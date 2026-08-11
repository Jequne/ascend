import eslint from "@eslint/js";
import prettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    ...svelte.configs["flat/recommended"],
    prettier,
    {
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
    },
    {
        files: ["**/*.svelte"],
        languageOptions: {
            parserOptions: {
                parser: tseslint.parser,
            },
        },
    },
    {
        files: ["**/*.svelte.ts"],
        languageOptions: {
            parser: tseslint.parser,
        },
    },
    {
        rules: {
            "svelte/no-navigation-without-resolve": "off",
        },
    },
    {
        ignores: [
            ".svelte-kit/**",
            "build/**",
            "node_modules/**",
            "src-tauri/gen/**",
            "src-tauri/target/**",
        ],
    },
);
