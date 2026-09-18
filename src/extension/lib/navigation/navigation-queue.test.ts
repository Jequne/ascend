import { describe, expect, it, vi } from "vitest";
import type { NavigateCommand, NavigationResult } from "../types/navigation";
import { NavigationQueue } from "./navigation-queue";

const ids = [
    "123e4567-e89b-42d3-a456-426614174001",
    "123e4567-e89b-42d3-a456-426614174002",
    "123e4567-e89b-42d3-a456-426614174003",
];

describe("NavigationQueue", () => {
    it("starts the latest command immediately and supersedes every older command", async () => {
        const executions: Array<Deferred<NavigationResult>> = [];
        const execute = vi.fn((command: NavigateCommand) => {
            const deferred = createDeferred<NavigationResult>();
            executions.push(deferred);
            return deferred.promise.then((result) => ({
                ...result,
                commandId: command.commandId,
            }));
        });
        const queue = new NavigationQueue(execute);

        const first = queue.submit(command(ids[0]));
        const second = queue.submit(command(ids[1]));
        const third = queue.submit(command(ids[2]));

        await expect(first).resolves.toEqual({
            commandId: ids[0],
            status: "superseded",
        });
        await expect(second).resolves.toEqual({
            commandId: ids[1],
            status: "superseded",
        });
        expect(execute).toHaveBeenCalledTimes(3);
        expect(execute.mock.calls[2]?.[0].commandId).toBe(ids[2]);

        executions[0]?.resolve({ commandId: ids[0]!, status: "completed" });
        executions[1]?.resolve({ commandId: ids[1]!, status: "completed" });

        executions[2]?.resolve({ commandId: ids[2]!, status: "completed" });
        await expect(third).resolves.toMatchObject({ status: "completed" });
    });

    it("deduplicates in-flight and completed command IDs", async () => {
        const deferred = createDeferred<NavigationResult>();
        const execute = vi.fn(() => deferred.promise);
        const queue = new NavigationQueue(execute);
        const request = command(ids[0]);

        const first = queue.submit(request);
        const duplicate = queue.submit(request);
        expect(duplicate).toBe(first);
        expect(execute).toHaveBeenCalledTimes(1);

        deferred.resolve({ commandId: ids[0]!, status: "completed" });
        await first;
        await queue.submit(request);
        expect(execute).toHaveBeenCalledTimes(1);
    });

    it("cancels the latest command when navigation becomes unavailable", async () => {
        const deferred = createDeferred<NavigationResult>();
        const queue = new NavigationQueue(() => deferred.promise);
        const active = queue.submit(command(ids[0]));

        queue.cancelActive("target_missing");
        await expect(active).resolves.toEqual({
            commandId: ids[0],
            status: "ignored",
            errorCode: "target_missing",
        });

        deferred.resolve({ commandId: ids[0]!, status: "completed" });
    });

    it("continues after an execution failure", async () => {
        const execute = vi
            .fn<(command: NavigateCommand) => Promise<NavigationResult>>()
            .mockRejectedValueOnce(new Error("failed"))
            .mockResolvedValueOnce({
                commandId: ids[1]!,
                status: "completed",
            });
        const queue = new NavigationQueue(execute);

        await expect(queue.submit(command(ids[0]))).resolves.toMatchObject({
            status: "failed",
        });
        await expect(queue.submit(command(ids[1]))).resolves.toMatchObject({
            status: "completed",
        });
    });
});

function command(commandId: string | undefined): NavigateCommand {
    if (!commandId) throw new Error("Missing command ID");
    return {
        commandId,
        url: "https://axiom.trade/meme/pair?chain=sol",
        issuedAt: "2026-09-17T12:00:00.000Z",
    };
}

type Deferred<T> = {
    promise: Promise<T>;
    resolve: (value: T) => void;
};

function createDeferred<T>(): Deferred<T> {
    let resolvePromise: ((value: T) => void) | undefined;
    const promise = new Promise<T>((resolve) => {
        resolvePromise = resolve;
    });
    return {
        promise,
        resolve: (value) => resolvePromise?.(value),
    };
}
