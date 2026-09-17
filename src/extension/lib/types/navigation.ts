export type NavigationMethod = "history";

export type NavigateCommand = {
    commandId: string;
    url: string;
    issuedAt: string;
};

export type NavigationResult = {
    commandId: string;
    status: "completed" | "superseded" | "ignored" | "failed";
    method?: NavigationMethod;
    errorCode?: string;
};
