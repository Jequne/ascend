export type TargetState =
    | { kind: "idle" }
    | {
          kind: "running";
          tabId: number;
          title: string;
          url: string;
      }
    | {
          kind: "paused";
          reason: "target_closed" | "target_left_axiom" | "target_missing";
      };

export type ActivePageState =
    | {
          kind: "axiom";
          tabId: number;
          title: string;
          url: string;
      }
    | { kind: "other" }
    | { kind: "unavailable" };

export type PopupSnapshot = {
    activePage: ActivePageState;
    target: TargetState;
};
