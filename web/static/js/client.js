// client.js
store.userRole = "client";

// Dummy wsSend so playback-sync.js doesn't crash when track ends
function wsSend(action, data) {
    // Client mode NEVER sends commands to the server.
}

// Dummy showLogToast to prevent errors from playback-sync.js
function showLogToast(msg) {
    console.log("Toast:", msg);
}

// Minimal getCoverArt since we don't load toast.js in client.html
window.getCoverArt = async function(track) {
    if (!track) return "";
    if (track.thumbnail && track.thumbnail.startsWith("http")) return track.thumbnail;
    return `/api/thumbnail/${track.video_id}`;
};

window.cleanTrackTitle = function(title) {
    if (!title) return "";
    return title.replace(/[\[\(].*?(official|music video|lyric|audio|live|performance).*?[\]\)]/gi, '')
                .replace(/#\S+/g, '')
                .replace(/\s{2,}/g, ' ')
                .replace(/\s+-\s*$/, '')
                .trim();
};

function updateWSStatus(isOnline) {
    const el = document.getElementById("client-ws-status");
    if (!el) return;
    if (isOnline) {
        el.innerHTML = '<i class="ti ti-wifi"></i> Online';
        el.style.color = 'var(--text-1)';
    } else {
        el.innerHTML = '<i class="ti ti-wifi-off"></i> Offline';
        el.style.color = 'var(--red)';
    }
}

function handleStateMessage(data) {
    if (data.type === "state") {
        Object.assign(store, data.data);
        if (typeof renderNowPlaying === 'function') renderNowPlaying();
        if (typeof renderLyrics === 'function') renderLyrics();

        // Delegate audio streaming to the robust playback-sync.js
        if (typeof syncBrowserAudio === 'function') {
            syncBrowserAudio();
        }
    }
}

function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = protocol + "//" + window.location.host + "/ws";

    window.ws = new WebSocket(wsUrl);

    window.ws.onopen = () => {
        updateWSStatus(true);
    };

    window.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleStateMessage(data);
        } catch (e) {
            console.error("Error parsing WS message:", e);
        }
    };

    window.ws.onclose = () => {
        updateWSStatus(false);
        setTimeout(connectWS, 3000);
    };

    window.ws.onerror = () => {
        updateWSStatus(false);
    };
}

// Progress loop for smooth UI rendering (since player.js is not loaded in client.html)
setInterval(() => {
    const posEl = document.getElementById("pb-time-pos");
    const durEl = document.getElementById("pb-time-dur");
    const fillEl = document.getElementById("pb-progress-fill");

    // store.position is updated by playback-sync.js automatically (timeupdate event)
    if (posEl && typeof formatTime === 'function') posEl.textContent = formatTime(store.position || 0);
    if (store.current_track && store.current_track.duration) {
        if (durEl && typeof formatTime === 'function') durEl.textContent = formatTime(store.current_track.duration);
        if (fillEl) {
            const pct = Math.min(100, Math.max(0, ((store.position || 0) / store.current_track.duration) * 100));
            fillEl.style.width = pct + "%";
        }
    }

    // Sync local lyrics highlight
    if (typeof syncLocalLyrics === 'function') syncLocalLyrics();
}, 200);

document.addEventListener("DOMContentLoaded", () => {
    if (typeof initDOM === 'function') initDOM();
    if (typeof initAudio === 'function') initAudio();
    updateWSStatus(false);
    connectWS();
});
