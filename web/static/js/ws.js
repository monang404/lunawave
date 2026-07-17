let ws = null;
let wsReconnectTimer = null;

// Dirty checking removed (moved to components or obsolete)

function wsConnect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${location.host}/ws`;

    showConnectionToast("Menghubungkan...", "connecting");

    // Tutup koneksi lama jika masih ada (BUG-003: mencegah concurrent connections)
    if (ws && ws.readyState !== WebSocket.CLOSED) {
        ws.onclose = null;
        ws.onerror = null;
        ws.close();
    }

    ws = new WebSocket(url);
    window.ws = ws;

    ws.onopen = () => {
        store.is_online = true;
        hideConnectionToast();
        if (wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
        }

        if (store.userRole === "admin") {
            const token = window.safeStorage.get("lunawave_session_token");
            if (token) {
                wsSend("auth", { token: token });
            }
            const savedOutput = window.safeStorage.get("lunawave_audio_output") || "browser";
            wsSend("set_output", { output: savedOutput });
        } else if (store.userRole === "client") {
            if (store.active_tab === "home" || store.active_tab === "discover") {
                wsSend("discover");
            }
        }
        renderHeader();
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleServerMessage(msg);
        } catch (e) {
            console.error("WS parse error:", e);
        }
    };

    ws.onclose = () => {
        store.is_online = false;
        renderHeader();
        showConnectionToast("Koneksi terputus. Reconnecting...", "disconnected");
        wsReconnectTimer = setTimeout(wsConnect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}

function wsSend(action, data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "cmd", action, data: data || {} }));
    }
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
                window.safeStorage.set("lunawave_user_role", "admin");
                if (msg.data && msg.data.token) {
                    window.safeStorage.set("lunawave_session_token", msg.data.token);
                }
                window.safeStorage.remove("lunawave_admin_password");
                dom.loginErrorMsg.textContent = "";
                dom.portalLoginForm.classList.add("hidden");
                applyRoleUI();
                showLogToast("Akses Admin Diterima!");
                if (store.active_tab === "home" || store.active_tab === "discover") {
                    showLogToast("Meminta data lagu...");
                    wsSend("discover");
                }
                renderFullState();
            } else {
                dom.loginErrorMsg.textContent = msg.data.message || "Login gagal.";
                if (store.userRole === "admin") {
                    logout();
                }
            }
            break;
        case "state":
            if (typeof applyFullState === "function") {
                applyFullState(msg.data);
            }
            break;
        case "progress":
            // FIX-POSITION-DRIFT-02: server-side mpv (yang jadi sumber msg.data.position)
            // dan <audio> di browser adalah DUA jalur playback yang independen (mpv jalan
            // "silent" cuma buat tracking, audio browser fetch stream sendiri dari
            // /api/stream/). Posisi keduanya nyaris tidak pernah persis sama — beda
            // network/buffering bikin selisih ratusan ms itu wajar & terus ada, bukan
            // cuma soal throttle. Kalau tiap progress message yang lewat 0.5s diff
            // langsung dipakai buat seek paksa, maka SETIAP toggle pause/resume bakal
            // hampir pasti kena koreksi (karena broadcast progress dari toggle_pause
            // datang duluan/independen dari status audio browser) -> audio browser
            // mundur/ngulang sesaat. Solusinya: dalam window sesaat setelah user sendiri
            // yang toggle play/pause, biarkan <audio> browser (yang sudah otomatis
            // benar posisinya sendiri, tidak di-reload) main tanpa dipaksa re-seek oleh
            // posisi mpv server yang independen ini.
            const _inToggleGrace = window.lastToggleTime && (Date.now() - window.lastToggleTime <= 1200);

            let statusChanged = false;
            if (!_inToggleGrace) {
                if (store.status !== msg.data.status) {
                    store.status = msg.data.status;
                    statusChanged = true;
                    // FIX-POSITION-DRIFT-06: client lain (bukan yang mengklik play) baru
                    // tau status berubah jadi PLAYING lewat pesan ini. Reset timestamp
                    // anchor supaya interpolasi mulai ngitung dari sekarang, bukan dari
                    // kapan anchor lama di-set (yang bisa jauh sebelum ini kalau lagunya
                    // lama di-pause) — sama kayak fix di klik tombol play.
                    if (store.status === "PLAYING" && typeof resetAnchorClock === "function") {
                        resetAnchorClock();
                    }
                }
            }
            if (msg.data.server_ts) {
                store.server_ts = msg.data.server_ts;
            }

            // FIX-POSITION-DRIFT-05: bug sebelumnya masih ada dalam bentuk lain. Syarat
            // "jangan pakai angka server" kemarin cuma berlaku SAAT audio browser lagi
            // actively playing (!audio.paused). Begitu user pause, audio.paused jadi true
            // -> syarat itu gugur -> baris ini balik nurut ke msg.data.position, padahal
            // itu posisi mpv di server yang independen & LEBIH LAMBAT beberapa detik dari
            // audio asli (lihat FIX-POSITION-DRIFT-02/03). Efeknya: pas pause, angka
            // muncul mundur (mis. 42 -> 38), dan sesaat setelah resume bisa mundur lagi
            // sebelum audio browser "menang" lagi -> keliatan "bingung" maju-mundur padahal
            // SUARA-nya sendiri gak kenapa-napa (krn audio.currentTime gak disentuh di sini).
            //
            // Fix yang benar: penentu sumber posisi itu bukan "apakah lagi playing", tapi
            // "apakah outputnya browser". Selama audio_output === "browser", elemen <audio>
            // browser adalah SATU-SATUNYA sumber kebenaran posisi — baik lagi main maupun
            // lagi pause — karena mpv di server cuma tracking "bayangan" (silent) di mode
            // ini, bukan pemutar aslinya. msg.data.position cuma layak dipakai sebagai
            // sumber utama saat audio_output BUKAN "browser" (mis. "device", mpv beneran
            // yang mutar).
            const _browserAudioEl = (store.audio_output === "browser") ? getOrInitAudio() : null;
            const _browserAudioActive = !!(_browserAudioEl && !_browserAudioEl.paused && _browserAudioEl.src && !_browserAudioEl.src.startsWith("data:"));
            if (store.audio_output !== "browser") {
                // mpv server = pemutar asli di mode ini, jadi ini SATU-SATUNYA sumber
                // posisi (~1x/detik) — anchor-kan supaya rAF clock bisa interpolasi mulus
                // di antara tick-tick server, bukan cuma loncat tiap detik.
                if (typeof setPositionAnchor === "function") {
                    setPositionAnchor(msg.data.position);
                } else {
                    store.position = msg.data.position;
                }
            }
            // Kalau audio_output === "browser": JANGAN sentuh anchor di sini sama sekali,
            // baik lagi playing maupun paused. Anchor sudah/akan di-set oleh audio.js lewat
            // event "timeupdate" (saat main) dan otomatis diam di posisi terakhir saat
            // pause (krn tidak ada timeupdate baru) — itu justru perilaku yang benar.

            if (store.audio_output === "browser" && store.status === "PLAYING") {
                const audio = _browserAudioEl;
                if (_browserAudioActive) {
                    // FIX-POSITION-DRIFT-03: <audio> browser dan mpv server adalah 2 jalur stream
                    // independen. mpv punya buffer tebal (demuxer-readahead-secs=20) buat tahan
                    // koneksi flaky, sedangkan <audio> browser tidak — jadi selisih beberapa detik
                    // ANTARA KEDUANYA itu WAJAR dan terus membesar seiring waktu, bukan tanda error.
                    // Threshold lama (0.5 detik) terlalu ketat: maksa audio browser "ngejar" tiap kali
                    // drift alami itu lewat 0.5 detik, bikin lompat/pengulangan yang kedengaran jelas
                    // (apalagi pas pause/resume). Naikkan ke 5 detik (samakan dengan threshold initial
                    // load di audio.js) — cuma koreksi kalau beneran desync parah (mis. stream sempat
                    // putus/reconnect), bukan drift wajar akibat perbedaan buffering. Kalau beneran
                    // di-seek, samakan store.position ke posisi baru itu juga (sekali ini aja).
                    if (!_inToggleGrace) {
                        const diff = Math.abs(audio.currentTime - msg.data.position);
                        if (diff > 5 && msg.data.position > 2) {
                            audio.currentTime = msg.data.position;
                            if (typeof setPositionAnchor === "function") {
                                setPositionAnchor(msg.data.position);
                            } else {
                                store.position = msg.data.position;
                            }
                        }
                    }
                } else if (audio.paused && audio.src && !audio.src.startsWith("data:") && audio.readyState >= 2) {
                    // FIX-RADIO-08: Audio stuck paused padahal status PLAYING.
                    // Terjadi saat AudioContext suspended (radio auto-switch tanpa user interaction).
                    // Coba resume AudioContext + play ulang tanpa menunggu user klik.
                    // audio.readyState >= 2 = HAVE_CURRENT_DATA — audio sudah ter-load, aman di-play.
                    // PATCH-ANDROID-AUDIO-01: kalau sebelumnya sudah ketauan diblock browser,
                    // jangan retry diam2 tiap detik (spam gagal) — tunggu user
                    // tap tombol "tap to play" (lihat audio.js), itu pasti lolos
                    // autoplay policy krn ada user gesture beneran.
                    if (!window.audioBlocked && typeof _resumeAndPlay === "function") {
                        _resumeAndPlay(audio);
                    }
                }
            }

            renderProgress();

            renderPlayBtn();
            // PATCH-ANDROID-AUDIO-01: dipanggil tiap tick (bukan cuma saat statusChanged)
            // supaya data-player-state / idle-view selalu sinkron dgn
            // store.status & store.current_track yang sebenarnya.
            if (typeof syncPlayerStateAttr === "function") syncPlayerStateAttr();
            if (statusChanged) {
                if (typeof renderNowPlaying === "function") renderNowPlaying();
                if (typeof renderQueue === "function") renderQueue();
                if (typeof renderRadio === "function") renderRadio();
                if (typeof updateSearchPlayingState === "function") updateSearchPlayingState();
                if (typeof updateDiscoverPlayingState === "function") updateDiscoverPlayingState();
            }
            syncBrowserAudio();
            if (typeof syncLocalLyrics === "function") syncLocalLyrics();
            break;
        case "lyrics":
            store.lyrics_lines = msg.data.lyrics_lines || [];
            store.lyrics_timestamps = msg.data.lyrics_timestamps || [];
            store.lyrics_index = msg.data.lyrics_index || 0;
            store.lyrics_offset = msg.data.lyrics_offset || 0;
            store.lyrics_loading = msg.data.lyrics_loading || false;
            if (typeof renderLyrics === "function") renderLyrics();
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
            store.discover_for_you = msg.data.for_you || [];
            store.discover_unheard = msg.data.unheard || [];
            store.discover_genre_affinity_genre = msg.data.genre_affinity_genre || null;
            store.discover_genre_affinity_artists = msg.data.genre_affinity_artists || [];
            store.discover_taste_spectrum = msg.data.taste_spectrum || [];
            renderDiscoverTab();
            renderRecentRow();
            if (typeof renderDiscoverPersonalization === "function") renderDiscoverPersonalization();
            break;
        case "artist_detail":
            if (typeof handleArtistDetail === "function") handleArtistDetail(msg.data);
            break;
        case "log":
            showLogToast(msg.data);
            break;
        case "error":
            showLogToast("Error: " + msg.data);
            break;
        case "download_progress":
            store.download_progress = msg.data;
            if (typeof renderPlayerBar === "function") renderPlayerBar();
            if (typeof renderSettingsSheet === "function") renderSettingsSheet();
            break;
        case "cache_size":
            if (dom.ssCacheSub) {
                const mb = (msg.data.size_bytes / (1024 * 1024)).toFixed(2);
                dom.ssCacheSub.textContent = mb + " MB";
            }
            break;
        case "cache_cleared":
            if (dom.ssCacheSub) dom.ssCacheSub.textContent = "0.00 MB";
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
            if (typeof renderLyrics === "function") renderLyrics();
        }
    }
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

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { wsConnect, wsSend, handleServerMessage };
}
