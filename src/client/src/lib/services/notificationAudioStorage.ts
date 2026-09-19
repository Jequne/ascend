export const CUSTOM_NOTIFICATION_AUDIO_ID = "notification-custom-sound";

export interface StoredNotificationAudio {
    id: string;
    name: string;
    type: string;
    blob: Blob;
    updatedAt: string;
}

export interface NotificationAudioStorage {
    get(id: string): Promise<StoredNotificationAudio | null>;
    replace(record: StoredNotificationAudio): Promise<void>;
    remove(id: string): Promise<void>;
}

const DATABASE_NAME = "ascend-trenches-audio";
const DATABASE_VERSION = 1;
const STORE_NAME = "notification-audio";

export class IndexedDbNotificationAudioStorage implements NotificationAudioStorage {
    private databasePromise: Promise<IDBDatabase> | null = null;

    async get(id: string): Promise<StoredNotificationAudio | null> {
        const database = await this.openDatabase();
        const transaction = database.transaction(STORE_NAME, "readonly");
        const request = transaction.objectStore(STORE_NAME).get(id);
        const record = await requestResult<StoredNotificationAudio | undefined>(
            request,
        );
        return record ?? null;
    }

    async replace(record: StoredNotificationAudio): Promise<void> {
        const database = await this.openDatabase();
        const transaction = database.transaction(STORE_NAME, "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        store.clear();
        store.put(record);
        await transactionComplete(transaction);
    }

    async remove(id: string): Promise<void> {
        const database = await this.openDatabase();
        const transaction = database.transaction(STORE_NAME, "readwrite");
        transaction.objectStore(STORE_NAME).delete(id);
        await transactionComplete(transaction);
    }

    private openDatabase(): Promise<IDBDatabase> {
        if (this.databasePromise) return this.databasePromise;
        if (typeof indexedDB === "undefined") {
            return Promise.reject(
                new Error("Local audio storage is unavailable."),
            );
        }

        this.databasePromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
            request.onupgradeneeded = () => {
                const database = request.result;
                if (!database.objectStoreNames.contains(STORE_NAME)) {
                    database.createObjectStore(STORE_NAME, { keyPath: "id" });
                }
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () =>
                reject(request.error ?? new Error("Unable to open IndexedDB."));
            request.onblocked = () =>
                reject(new Error("Local audio storage upgrade is blocked."));
        });

        void this.databasePromise.catch(() => {
            this.databasePromise = null;
        });
        return this.databasePromise;
    }
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
    return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () =>
            reject(request.error ?? new Error("IndexedDB request failed."));
    });
}

function transactionComplete(transaction: IDBTransaction): Promise<void> {
    return new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () =>
            reject(
                transaction.error ?? new Error("IndexedDB transaction failed."),
            );
        transaction.onabort = () =>
            reject(
                transaction.error ??
                    new Error("IndexedDB transaction was aborted."),
            );
    });
}

export const notificationAudioStorage = new IndexedDbNotificationAudioStorage();
