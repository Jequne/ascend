import type { NavigateCommand, NavigationResult } from "../types/navigation";

type QueueItem = {
    command: NavigateCommand;
    resolve: (result: NavigationResult) => void;
};

type ResultRecord = {
    promise: Promise<NavigationResult>;
    settled: boolean;
};

export class NavigationQueue {
    private active: QueueItem | null = null;
    private pending: QueueItem | null = null;
    private readonly results = new Map<string, ResultRecord>();
    private readonly resultOrder: string[] = [];

    constructor(
        private readonly execute: (
            command: NavigateCommand,
        ) => Promise<NavigationResult>,
        private readonly resultLimit = 100,
    ) {}

    submit(command: NavigateCommand): Promise<NavigationResult> {
        const known = this.results.get(command.commandId);
        if (known) return known.promise;

        let resolveResult: ((result: NavigationResult) => void) | undefined;
        const resultPromise = new Promise<NavigationResult>((resolve) => {
            resolveResult = resolve;
        });
        const record: ResultRecord = {
            promise: resultPromise,
            settled: false,
        };
        const item: QueueItem = {
            command,
            resolve: (result) => {
                record.settled = true;
                resolveResult?.(result);
                this.pruneResults();
            },
        };
        this.remember(command.commandId, record);

        if (!this.active) {
            this.active = item;
            void this.runActive();
            return resultPromise;
        }

        if (this.pending) {
            this.pending.resolve({
                commandId: this.pending.command.commandId,
                status: "superseded",
            });
        }
        this.pending = item;
        return resultPromise;
    }

    clearPending(errorCode: string): void {
        if (!this.pending) return;
        this.pending.resolve({
            commandId: this.pending.command.commandId,
            status: "ignored",
            errorCode,
        });
        this.pending = null;
    }

    private async runActive(): Promise<void> {
        const item = this.active;
        if (!item) return;

        let result: NavigationResult;
        try {
            result = await this.execute(item.command);
        } catch {
            result = {
                commandId: item.command.commandId,
                status: "failed",
                errorCode: "navigation_failed",
            };
        }
        item.resolve(result);

        this.active = this.pending;
        this.pending = null;
        if (this.active) void this.runActive();
    }

    private remember(commandId: string, result: ResultRecord): void {
        this.results.set(commandId, result);
        this.resultOrder.push(commandId);
        this.pruneResults();
    }

    private pruneResults(): void {
        let index = 0;
        while (
            this.results.size > this.resultLimit &&
            index < this.resultOrder.length
        ) {
            const commandId = this.resultOrder[index];
            const record = commandId ? this.results.get(commandId) : undefined;
            if (commandId && record?.settled) {
                this.results.delete(commandId);
                this.resultOrder.splice(index, 1);
                continue;
            }
            index += 1;
        }
    }
}
