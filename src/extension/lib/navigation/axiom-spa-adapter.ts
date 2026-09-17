export async function navigateWithAxiomHistory(_url: string): Promise<boolean> {
    // Axiom's router does not react to direct pushState, and its card transition exposes no reproducible public event; see QA.md.
    void _url;
    return false;
}
