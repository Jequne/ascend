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

        if (this.active) {
            this.active.resolve({
                commandId: this.active.command.commandId,
                status: "superseded",
            });
        }
        this.active = item;
        void this.run(item);
        return resultPromise;
    }

    cancelActive(errorCode: string): void {
        if (!this.active) return;
        this.active.resolve({
            commandId: this.active.command.commandId,
            status: "ignored",
            errorCode,
        });
        this.active = null;
    }

    private async run(item: QueueItem): Promise<void> {
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
        if (this.active !== item) return;

        item.resolve(result);
        this.active = null;
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
