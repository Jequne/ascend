# Repository instructions

## Desktop client

These instructions apply to `src/client` and to documentation describing work on that client.

- Perform the desktop-client refactoring on the `desktop-client-dev` branch. Do not modify Git identity; commits must use the repository's configured user and must not mention an assistant, Codex, AI, or generated work.
- Keep changes inside `src/client` unless the task explicitly requires a repository-level configuration or documentation change. Do not change server contracts while refactoring the client.
- Preserve the current color palette, element order, card dimensions, spacing proportions, and desktop window behavior. Visual work may polish surfaces, borders, shadows, focus states, and motion without redesigning the layout.
- Use Tailwind CSS 4 through its Vite plugin. Prefer utilities directly in Svelte markup; keep custom CSS only for behavior that utilities cannot express cleanly, such as range-input pseudo-elements and the settings-panel track.
- Write all frontend application code in TypeScript. Use `lang="ts"` in Svelte components and strict types for stores, API data, settings, WebSocket messages, utilities, and Vite configuration. Do not rewrite the Tauri Rust layer in TypeScript.
- Format frontend files with Prettier using four-space indentation, semicolons, double quotes, the Svelte plugin, and Tailwind class sorting. Lint TypeScript and Svelte with ESLint.
- Keep the implementation DRY and simple. Prefer pure functions for normalization and filtering, small components for UI composition, and classes only for stateful services with a clear lifecycle.
- Do not add source-code comments. Remove obsolete comments from code being substantially rewritten, but do not make unrelated edits solely to remove existing comments.
- Keep tests next to the modules or components they cover because the repository-level `.gitignore` excludes directories named `tests`.
- Complete each vertical slice with focused tests and run formatting checks, ESLint, `svelte-check`, Vitest, and the production build before committing. Run `cargo check` when Tauri configuration or capabilities are affected.
- Make one conventional commit per completed checkpoint. Do not combine unrelated cleanup with a checkpoint.
