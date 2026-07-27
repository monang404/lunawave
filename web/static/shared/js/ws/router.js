import { handleAuthMessage } from "./message-handlers/auth-messages.js";
import { handlePlaybackMessage } from "./message-handlers/playback-messages.js";
import { handleDiscoverMessage } from "./message-handlers/discover-messages.js";
import { handleChatMessage } from "./message-handlers/chat-messages.js";
import { handleSystemMessage } from "./message-handlers/system-messages.js";

const HANDLERS = {
    auth_status: handleAuthMessage,
    setup_status: handleAuthMessage,
    state: handlePlaybackMessage,
    progress: handlePlaybackMessage,
    lyrics: handlePlaybackMessage,
    search_results: handleDiscoverMessage,
    discover_search_results: handleDiscoverMessage,
    discover_data: handleDiscoverMessage,
    artist_detail: handleDiscoverMessage,
    chat_history: handleChatMessage,
    chat_message: handleChatMessage,
    log: handleSystemMessage,
    error: handleSystemMessage,
    download_progress: handleSystemMessage,
    cache_size: handleSystemMessage,
    cache_cleared: handleSystemMessage
};

export function routeMessage(msg) {
    const handler = HANDLERS[msg.type];
    if (handler) {
        handler(msg);
    } else {
        // Fallback for cases not explicitly defined in HANDLERS (safety net per RFC)
        switch (msg.type) {
            default:
                console.warn("Unhandled message type in fallback:", msg.type);
                break;
        }
    }
}
