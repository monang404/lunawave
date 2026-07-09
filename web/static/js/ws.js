const wsClient = (function() {
    let ws = null;
    let wsReconnectTimer = null;
    let _wsAuthConfirmed = false;  // true setelah auth_status success
    let _pendingQueue = [];        // buffer command sebelum auth dikonfirmasi

    function connect() {
        const protocol = location.protocol === "https:" ? "wss:" : "ws:";
        const url = `${protocol}//${location.host}/ws`;

        if (typeof showConnectionToast === "function") {
            showConnectionToast("Menghubungkan...", "connecting");
        }

        if (ws && ws.readyState !== WebSocket.CLOSED) {
            ws.onclose = null;
            ws.onerror = null;
            ws.close();
        }

        ws = new WebSocket(url);

        ws.onopen = () => {
            // Reset auth state setiap kali reconnect — ws object baru belum terautentikasi
            _wsAuthConfirmed = false;
            _pendingQueue = [];

            if (typeof store !== "undefined") store.is_online = true;
            if (typeof hideConnectionToast === "function") hideConnectionToast();
            if (wsReconnectTimer) {
                clearTimeout(wsReconnectTimer);
                wsReconnectTimer = null;
            }

            if (typeof store !== "undefined" && store.userRole === "admin") {
                const token = window.safeStorage ? window.safeStorage.get("ytgui_session_token") : null;
                if (token && typeof WS_ACTIONS !== "undefined") {
                    // Kirim AUTH langsung tanpa queue — ini command pertama yang HARUS dikirim
                    _sendRaw(WS_ACTIONS.AUTH, { token: token });
                    // Tahan command lain sampai auth_status sukses balik dari server
                    // (lihat confirmAuth() yang dipanggil dari handleServerMessage)
                } else {
                    // Tidak ada token → langsung anggap bukan admin, tidak perlu queue
                    _wsAuthConfirmed = true;
                }
            } else {
                // Role client atau portal tidak butuh auth token
                _wsAuthConfirmed = true;
                if (typeof store !== "undefined" && store.userRole === "client") {
                    if (store.active_tab === "home" || store.active_tab === "discover") {
                        if (typeof WS_ACTIONS !== "undefined") _sendRaw(WS_ACTIONS.DISCOVER);
                    }
                }
            }
            if (typeof renderHeader === "function") renderHeader();
        };

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (typeof handleServerMessage === "function") handleServerMessage(msg);
            } catch (e) {
                console.error("WS parse error:", e);
            }
        };

        ws.onclose = () => {
            if (typeof store !== "undefined") store.is_online = false;
            if (typeof renderHeader === "function") renderHeader();
            if (typeof showConnectionToast === "function") {
                showConnectionToast("Koneksi terputus. Reconnecting...", "disconnected");
            }
            wsReconnectTimer = setTimeout(connect, 2000);
        };

        ws.onerror = () => {
            ws.close();
        };
    }

    // Kirim langsung ke socket tanpa melewati queue (untuk AUTH dan flush)
    function _sendRaw(action, data) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "cmd", action, data: data || {} }));
        }
    }

    // Public send — buffer command sampai auth dikonfirmasi
    function send(action, data) {
        if (!_wsAuthConfirmed) {
            // Queue command, akan di-flush setelah auth_status success
            _pendingQueue.push({ action, data: data || {} });
            return;
        }
        _sendRaw(action, data);
    }

    // Dipanggil oleh handleServerMessage saat auth_status success
    function confirmAuth() {
        _wsAuthConfirmed = true;
        // Flush semua command yang tertahan selama auth berjalan
        const queued = _pendingQueue.splice(0);
        for (const { action, data } of queued) {
            _sendRaw(action, data);
        }
        // Kirim SET_OUTPUT setelah auth dikonfirmasi (butuh auth di backend sekarang)
        const savedOutput = window.safeStorage ? (window.safeStorage.get("ytgui_audio_output") || "browser") : "browser";
        if (typeof WS_ACTIONS !== "undefined") _sendRaw(WS_ACTIONS.SET_OUTPUT, { output: savedOutput });
    }

    function closeConnection() {
        if (wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
        }
        if (ws) {
            ws.onclose = null;
            ws.onerror = null;
            ws.close();
        }
    }

    function getReadyState() {
        return ws ? ws.readyState : (typeof WebSocket !== 'undefined' ? WebSocket.CLOSED : 3);
    }

    return { connect, send, getReadyState, close: closeConnection, confirmAuth };
})();

function wsConnect() {
    wsClient.connect();
}

function wsSend(action, data) {
    wsClient.send(action, data);
}

function handleServerMessage(msg) {
    switch (msg.type) {
        case "auth_status":
            if (dom.adminSubmitBtn) {
                dom.adminSubmitBtn.disabled = false;
                dom.adminSubmitBtn.textContent = "Login Admin";
            }
            if (msg.data.success) {
                store.userRole = "admin";
                window.safeStorage.set("ytgui_user_role", "admin");
                if (msg.data.token) {
                    window.safeStorage.set("ytgui_session_token", msg.data.token);
                }
                dom.loginErrorMsg.textContent = "";
                dom.portalLoginForm.classList.add("hidden");
                applyRoleUI();
                showLogToast("Akses Admin Diterima!");
                // Konfirmasi auth → flush pending queue + kirim SET_OUTPUT
                wsClient.confirmAuth();
                if (store.active_tab === "home" || store.active_tab === "discover") {
                    showLogToast("Meminta data lagu...");
                    wsSend(WS_ACTIONS.DISCOVER);
                }
                requestRenderFullState();
            } else {
                dom.loginErrorMsg.textContent = msg.data.message || "Login gagal.";
                if (store.userRole === "admin") {
                    logout();
                }
            }
            break;
        case "state":
            Object.assign(store, msg.data);
            requestRenderFullState();
            if (store.userRole !== 'portal' && store.audio_output === 'browser') {
                syncBrowserAudio();
            }
            break;
        case "progress":
            store.position = msg.data.position;
            let statusChanged = false;
            if (!window.lastToggleTime || Date.now() - window.lastToggleTime > 1000) {
                if (store.status !== msg.data.status) {
                    store.status = msg.data.status;
                    statusChanged = true;
                }
            }
            if (msg.data.server_ts) {
                store.server_ts = msg.data.server_ts;
            }

            if (store.audio_output === "browser" && store.status === "PLAYING") {
                const audio = getOrInitAudio();
                if (!audio.paused && audio.src && !audio.src.startsWith("data:")) {
                    const diff = Math.abs(audio.currentTime - store.position);
                    if (diff > 0.5 && store.position > 2) {
                        audio.currentTime = store.position;
                    }
                } else if (audio.paused && audio.src && !audio.src.startsWith("data:") && audio.readyState >= 2) {
                    // PATCH-ANDROID-AUDIO-01: kalau sebelumnya sudah ketauan diblock browser,
                    if (!window.audioBlocked) {
                        _resumeAndPlay(audio);
                    }
                }
            }

            renderProgress();

            renderPlayBtn();
            // PATCH-ANDROID-AUDIO-01: dipanggil tiap tick (bukan cuma saat statusChanged)
            syncPlayerStateAttr();
            if (statusChanged) {
                renderNowPlaying();
                renderQueue();
                renderRadio();
                updateSearchPlayingState();
                updateDiscoverPlayingState();
                if (store.audio_output === 'browser') {
                    syncBrowserAudio();
                }
            }
            if (store.lyrics_lines && store.lyrics_lines.length > 0) {
                if (!window._syncLyricsRaf) {
                    window._syncLyricsRaf = requestAnimationFrame(() => {
                        syncLocalLyrics();
                        window._syncLyricsRaf = null;
                    });
                }
            }
            break;
        case "lyrics":
            store.lyrics_lines = msg.data.lyrics_lines || [];
            store.lyrics_timestamps = msg.data.lyrics_timestamps || [];
            store.lyrics_index = msg.data.lyrics_index || 0;
            store.lyrics_offset = msg.data.lyrics_offset || 0;
            store.lyrics_loading = msg.data.lyrics_loading || false;
            renderLyrics();
            break;
        case "search_results":
            renderSearchResults(msg.data);
            break;
        case "discover_data":
            showLogToast("Menerima data lagu! " + (msg.data.recent ? msg.data.recent.length : 0) + " items");
            store.discover_recent = msg.data.recent || [];
            store.discover_favorites = msg.data.favorites || [];
            store.discover_cached   = msg.data.cached_tracks || [];
            store.discover_featured_artists = msg.data.featured_artists || [];
            store.discover_featured_genres = msg.data.featured_genres || [];
            renderDiscoverTab();
            renderRecentRow();
            break;
        case "favorite_status":
            if (store.current_track && store.current_track.video_id === msg.data.video_id) {
                store.current_track.is_favorite = msg.data.is_favorite;
                renderNowPlaying();
            }
            break;
        case "log":
            showLogToast(msg.data);
            break;
        case "error":
            if (typeof msg.data === 'object' && msg.data.message) {
                showLogToast("Error: " + msg.data.message);
            } else {
                showLogToast("Error: " + msg.data);
            }
            break;
        case "download_progress":
            store.download_progress = msg.data;
            renderPlayerBar();
            renderSettingsSheet();
            break;
    }
}

function syncLocalLyrics() {
    if (store.lyrics_timestamps && store.lyrics_timestamps.length > 0) {
        const pos = store.position + (store.lyrics_offset || 0);
        let newIdx = -1;
        for (let i = 0; i < store.lyrics_timestamps.length; i++) {
            if (pos >= store.lyrics_timestamps[i]) {
                newIdx = i;
            } else {
                break;
            }
        }
        newIdx = Math.max(0, newIdx);
        if (store.lyrics_index !== newIdx) {
            store.lyrics_index = newIdx;
            renderLyrics();
        }
    }
}

let renderFullStateTimeout = null;
function requestRenderFullState() {
    if (renderFullStateTimeout) cancelAnimationFrame(renderFullStateTimeout);
    renderFullStateTimeout = requestAnimationFrame(() => {
        renderFullStateTimeout = null;
        renderFullState();
    });
}

function renderFullState() {
    renderHeader();
    renderNowPlaying();
    renderProgress();


    renderPlayerBar();
    renderRadio();
    renderQueue();
    renderLyrics();
    renderSettingsSheet();
    updateSearchPlayingState();
    updateDiscoverPlayingState();
}

function renderHeader() {
    if (store.is_online) {
        dom.statusDot.classList.remove("offline");
        dom.statusText.textContent = "online";
    } else {
        dom.statusDot.classList.add("offline");
        dom.statusText.textContent = "offline";
    }

    const out = store.audio_output || "browser";
    if (out === "browser") {
        dom.outputToggleBtn.textContent = "💻 BROWSER";
        dom.outputToggleBtn.classList.add("browser");
    } else {
        dom.outputToggleBtn.textContent = "📱 HP";
        dom.outputToggleBtn.classList.remove("browser");
    }
}
