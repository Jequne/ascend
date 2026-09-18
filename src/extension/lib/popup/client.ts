import { browser } from "wxt/browser";
import {
    isInternalResponse,
    type InternalRequest,
    type InternalResponse,
} from "../protocol/messages";

export async function sendPopupRequest(
    request: Extract<
        InternalRequest,
        {
            type:
                | "get_popup_state"
                | "start_target"
                | "stop_target"
                | "pair_bridge"
                | "retry_bridge";
        }
    >,
): Promise<InternalResponse> {
    const response: unknown = await browser.runtime.sendMessage(request);
    if (!isInternalResponse(response)) {
        throw new Error("invalid_background_response");
    }
    return response;
}
