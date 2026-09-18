import type { NavigationResult } from "./navigation";

export const BRIDGE_URL = "ws://127.0.0.1:17321/extension/v1";
export const BRIDGE_PROTOCOL_VERSION = 1 as const;

export type AutoOpenMode = "off" | "new_tab" | "current_axiom_tab";

export type BridgeConnectionState =
    | "unpaired"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "pairing_rejected"
    | "version_mismatch"
    | "unavailable";

export type ExtensionBridgeSnapshot = {
    connection: BridgeConnectionState;
    mode: AutoOpenMode;
    reconnectAttempt: number;
};

export type DesktopBridgeMessage =
    | {
          type: "state";
          protocolVersion: 1;
          mode: AutoOpenMode;
          bridgeStatus: "ready";
      }
    | {
          type: "navigate";
          protocolVersion: 1;
          commandId: string;
          url: string;
          issuedAt: string;
      }
    | {
          type: "mode_result";
          protocolVersion: 1;
          requestId: string;
          accepted: boolean;
          mode: AutoOpenMode;
          errorCode?: string;
      }
    | {
          type: "pong";
          protocolVersion: 1;
          sentAt: string;
      };

export type ExtensionBridgeMessage =
    | {
          type: "hello";
          protocolVersion: 1;
          extensionVersion: string;
          pairingSecret: string;
      }
    | {
          type: "set_mode";
          protocolVersion: 1;
          requestId: string;
          mode: "off" | "current_axiom_tab";
      }
    | ({
          type: "navigation_result";
          protocolVersion: 1;
      } & NavigationResult)
    | {
          type: "ping";
          protocolVersion: 1;
          sentAt: string;
      };
