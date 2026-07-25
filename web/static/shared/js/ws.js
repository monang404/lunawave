import { _resumeAndPlay, getOrInitAudio, syncBrowserAudio } from "./audio/playback-sync.js";
import { emit as bus } from "./bus.js";
import { dom } from "./dom.js";
import { isPendingToggleActive, store } from "./store.js";

export let ws = null;
let wsReconnectTimer = null;
let wsTokenRefreshTimer = null;
let wsReconnectDelay = 2000;
const WS_RECONNECT_MAX_DELAY = 30000;

// Dirty checking removed (moved to components or obsolete)

export function wsConnect() {
    const protocol = globalThis.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = protocol + "//" + globalThis.location.host + "/ws?page=" + encodeURIComponent(globalThis.location.pathname);

    bus("toast:connection-show", { text: "Menghubungkan...", type: "connecting" });

    // Tutup koneksi lama jika masih ada (BUG-003: mencegah concurrent connections)
    if (ws && ws.readyState !== WebSocket.CLOSED) {
        ws.onclose = null;
        ws.onerror = null;
        ws.close();
    }

    ws = new WebSocket(wsUrl);
    globalThis.ws = ws;

    ws.onopen = () => {
        store.is_online = true;
        bus("toast:connection-hide");
        wsReconnectDelay = 2000;
        if (wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
        }

        if (store.userRole === "admin") {
            const token = globalThis.safeStorage.get("lunawave_session_token");
            if (token) {
                wsSend("auth", { token: token });
            }
            const savedOutput = globalThis.safeStorage.get("lunawave_audio_output") || "browser";
            wsSend("set_output", { output: savedOutput });
        } else if (store.userRole === "client") {
            if (store.active_tab === "home" || store.active_tab === "discover") {
                wsSend("discover");
            }
        }

        // Fetch chat history
        wsSend("get_chat_history");

        if (wsTokenRefreshTimer) clearInterval(wsTokenRefreshTimer);
        wsTokenRefreshTimer = setInterval(() => {
            if (store.userRole === "admin" && store.is_online) {
                const token = globalThis.safeStorage.get("lunawave_session_token");
                if (token) wsSend("auth", { token: token });
            }
        }, 3600000);

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
        if (wsTokenRefreshTimer) {
            clearInterval(wsTokenRefreshTimer);
            wsTokenRefreshTimer = null;
        }
        store.is_online = false;
        renderHeader();
        bus("toast:connection-show", { text: "Koneksi terputus. Reconnecting...", type: "disconnected" });
        wsReconnectTimer = setTimeout(wsConnect, wsReconnectDelay);
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, WS_RECONNECT_MAX_DELAY);
    };

    ws.onerror = () => {
        ws.close();
    };
}

// Listener visibilitychange TERPISAH khusus reconnect (PD-4) — scope-nya
// beda dari titik kontrol rAF di playback-sync.js (PERF-3): begitu tab
// kembali visible saat ada reconnect timer pending, langsung coba connect
// tanpa menunggu sisa delay backoff. Sebaliknya, saat tab hidden, timer
// yang sudah capped di 30s dibiarkan jalan seperti biasa (tidak perlu
// dipause total).
if (typeof document !== "undefined") {
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && wsReconnectTimer) {
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = null;
            wsReconnectDelay = 2000;
            wsConnect();
        }
    });
}

export function wsSend(action, data) {
    // FIX-PAUSE-RACE-01 (edge case ditemukan setelah patch awal): kalau ada
    // pendingToggleTarget yang belum dikonfirmasi server (user pause lalu SEBELUM
    // konfirmasi datang langsung next/prev/pilih track lain), status track yang
    // baru (LOADING -> PLAYING) akan salah dianggap "kontradiktif" dengan target
    // basi itu dan ditolak oleh handler "progress" -> UI kelihatan macet di
    // LOADING sampai safety-valve 8 detik habis. Command-command ini mengganti
    // track sepenuhnya, jadi toggle play/pause yang lama sudah tidak relevan --
    // clear di sini (satu titik, berlaku utk semua caller: tombol next/prev,
    // keyboard shortcut, klik track di search/queue, Media Session action).
    if (action === "next" || action === "prev" || action === "play_track") {
        globalThis.pendingToggleTarget = null;
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "cmd", action, data: data || {} }));
    }
}

export function handleServerMessage(msg) {
    switch (msg.type) {
        case "auth_status":
            if (dom.adminSubmitBtn) {
                dom.adminSubmitBtn.disabled = false;
                dom.adminSubmitBtn.textContent = "Login Admin";
            }
            if (msg.data.success) {
                store.userRole = "admin";
                globalThis.safeStorage.set("lunawave_user_role", "admin");
                if (msg.data && msg.data.token) {
                    globalThis.safeStorage.set("lunawave_session_token", msg.data.token);
                }
                globalThis.safeStorage.remove("lunawave_admin_password");
                dom.loginErrorMsg.textContent = "";
                dom.portalLoginForm.classList.add("hidden");
                bus("auth:role-changed");
                bus("toast:log", { message: "Akses Admin Diterima!" });
                if (store.active_tab === "home" || store.active_tab === "discover") {
                    bus("toast:log", { message: "Meminta data lagu..." });
                    wsSend("discover");
                }
                bus("state:full-render");
            } else {
                dom.loginErrorMsg.textContent = msg.data.message || "Login gagal.";
                if (store.userRole === "admin") {
                    bus("auth:logout");
                }
            }
            break;
        case "setup_status":
            // T-B12: respons dari action "setup_admin" (server/handlers/setup.py).
            // Tidak menyentuh store.userRole sama sekali di sini -- akun admin
            // baru dibuat, belum login. Setelah sukses, user diarahkan ke
            // #portal-screen (alur login normal, T-B9) untuk login dengan
            // kredensial yang baru saja dibuat, bukan otomatis masuk sebagai admin.
            if (dom.setupSubmitBtn) {
                dom.setupSubmitBtn.disabled = false;
                dom.setupSubmitBtn.textContent = "Buat Akun Admin";
            }
            if (msg.data.success) {
                if (dom.setupErrorMsg) dom.setupErrorMsg.textContent = "";
                if (dom.setupConfirmErrorMsg) dom.setupConfirmErrorMsg.textContent = "";
                bus("toast:log", { message: "Akun admin berhasil dibuat! Silakan login." });
                if (dom.setupScreen) dom.setupScreen.classList.remove("portal-active");
                if (dom.portalScreen) dom.portalScreen.classList.add("portal-active");
                if (dom.adminUsername) dom.adminUsername.value = "";
            } else if (dom.setupErrorMsg) {
                dom.setupErrorMsg.textContent = msg.data.message || "Gagal membuat akun admin.";
            }
            break;
        case "state":
            bus("state:full", msg.data);
            break;
        case "progress": {
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
            //
            // FIX-PAUSE-RACE-01 (bug: pause auto-play lagi di jaringan jelek): _inToggleGrace
            // dulu dihitung dari globalThis.lastToggleTime dgn window WAKTU TETAP 1200ms. Di
            // jaringan flaky RTT sering > 1200ms, jadi progress message basi (msg.data.status
            // masih status LAMA, dari sebelum server sempat proses toggle kita) lolos grace,
            // menimpa balik store.status yg baru saja di-set user -> FIX-RADIO-08 di bawah
            // melihat "status PLAYING tapi audio.paused" -> auto-play tanpa user gesture.
            // Sekarang pakai globalThis.pendingToggleTarget: kalau kita masih menunggu konfirmasi
            // toggle ke status tertentu, message yg KONTRADIKTIF sama target itu ditolak
            // (masih dianggap basi) TERLEPAS dari sudah berapa lama -- sampai message yang
            // benar-benar mengonfirmasi target itu datang, atau safety-valve 8 detik habis.
            const _awaitedTarget = globalThis.pendingToggleTarget;
            // isPendingToggleActive juga membersihkan pendingToggleTarget sendiri kalau
            // sudah lewat safety-valve 8 detik (command toggle kita kemungkinan hilang).
            const _stillWaitingConfirmation = !!_awaitedTarget && isPendingToggleActive(_awaitedTarget);
            const _inToggleGrace = _stillWaitingConfirmation && msg.data.status !== _awaitedTarget;
            if (_stillWaitingConfirmation && msg.data.status === _awaitedTarget) {
                // Server akhirnya mengonfirmasi toggle yang kita minta -- selesai menunggu.
                globalThis.pendingToggleTarget = null;
            }

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
                    if (store.status === "PLAYING") {
                        bus("player:clock-reset");
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
                bus("player:position", msg.data.position);
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
                            // Audio sudah aktif & ter-load (readyState cukup karena
                            // _browserAudioActive true), jadi seek bisa langsung tanpa
                            // nunggu event 'canplay' -- yang di kondisi ini kemungkinan
                            // besar TIDAK PERNAH fire lagi (canplay hanya muncul lagi
                            // kalau ada reload/stall, bukan tiap kali kita ganti
                            // currentTime pada audio yang sudah playing). Sebelumnya
                            // anchor (angka yang ditampilkan) diubah duluan lewat
                            // setPositionAnchor(), sedangkan audio.currentTime baru
                            // menyusul di dalam oncanplay yang gak jalan -- itu sebabnya
                            // progress bar keliatan "loncat ke posisi server, lalu balik
                            // lagi" begitu timeupdate berikutnya menimpa balik ke posisi
                            // audio yang sebenarnya. Sekarang keduanya diset bareng,
                            // di tick yang sama, jadi tidak ada jeda visual.
                            audio.currentTime = msg.data.position;
                            bus("player:position", msg.data.position);
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
                    if (!globalThis.audioBlocked && typeof _resumeAndPlay === "function") {
                        _resumeAndPlay(audio);
                    }
                }
            }

            bus("player:progress");

            bus("player:btn-changed");
            // PATCH-ANDROID-AUDIO-01: dipanggil tiap tick (bukan cuma saat statusChanged)
            // supaya data-player-state / idle-view selalu sinkron dgn
            // store.status & store.current_track yang sebenarnya.
            bus("now-playing:sync-state-attr");
            if (statusChanged) {
                bus("now-playing:changed");
                bus("queue:changed");
                bus("radio:changed");
                bus("search:playing-state");
                bus("discover:playing-state");
            }
            syncBrowserAudio();
            if (typeof syncLocalLyrics === "function") syncLocalLyrics();
            break;
        }
        case "lyrics":
            store.lyrics_lines = msg.data.lyrics_lines || [];
            store.lyrics_timestamps = msg.data.lyrics_timestamps || [];
            store.lyrics_index = msg.data.lyrics_index || 0;
            store.lyrics_offset = msg.data.lyrics_offset || 0;
            store.lyrics_loading = msg.data.lyrics_loading || false;
            bus("lyrics:changed");
            break;
        case "search_results":
            bus("search:results", msg.data);
            break;
        case "discover_search_results":
            bus("discover:search-results", msg.data);
            break;
        case "discover_data":
            bus("toast:log", { message: "Menerima data lagu! " + (msg.data.recent ? msg.data.recent.length : 0) + " items" });
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
            bus("discover:tab-changed");
            bus("discover:recent-changed");
            bus("discover:personalization-changed");
            break;
        case "artist_detail":
            bus("discover:artist-detail", msg.data);
            break;
        case "log":
            bus("toast:log", { message: msg.data });
            break;
        case "error":
            bus("toast:log", { message: "Error: " + msg.data });
            bus("discover:search-error");
            break;
        case "download_progress": {
            const prevProgress = store.download_progress;
            store.download_progress = msg.data;
            bus("player:bar-changed");
            bus("settings:sheet-changed");

            if (prevProgress == null || prevProgress >= 1.0) {
                if (msg.data >= 0 && msg.data < 1.0) {
                    bus("toast:log", { message: "⬇ Mulai mengunduh lagu..." });
                }
            }
            if (msg.data >= 1.0 && prevProgress !== 1.0) {
                bus("toast:log", { message: "✅ Unduhan selesai! Tersedia di Tersimpan Lokal" });
                setTimeout(() => {
                    store.download_progress = null;
                    bus("player:bar-changed");
                }, 3000);
            }
            break;
        }
        case "cache_size":
            if (dom.ssCacheSub) {
                const mb = (msg.data.size_bytes / (1024 * 1024)).toFixed(2);
                dom.ssCacheSub.textContent = mb + " MB";
            }
            break;
        case "cache_cleared":
            if (dom.ssCacheSub) dom.ssCacheSub.textContent = "0.00 MB";
            break;
        case "chat_history":
            if (globalThis.ChatModule) globalThis.ChatModule.onHistory(msg.data);
            break;
        case "chat_message":
            if (globalThis.ChatModule) globalThis.ChatModule.onNewMessage(msg.data);
            break;
    }
}

export function syncLocalLyrics() {
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
            bus("lyrics:changed");
        }
    }
}



export function renderHeader() {
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
