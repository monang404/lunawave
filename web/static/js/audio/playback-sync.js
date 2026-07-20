let localAudio = null;
let audioUnlocked = false;
let _unlocking = false; // guard agar tidak double-call saat masih proses
let _lastLoadedVideoId = null;

let audioCtx = null;
let analyser = null;
let dataArray = null;

// Flag untuk mencegah infinite loop antara native audio event dan Media Session handler
let _mediaSessionHandling = false;

function getOrInitAudio() {
    if (!localAudio) {
        localAudio = new Audio();
        localAudio.preload = "auto";
        localAudio.onerror = (e) => {
            const err = localAudio.error;
            if (!err) return;
            if (err.code === 1) return;
            if (err.code === 4 && localAudio.src.includes("data:audio")) return;
            const errMsg = err.message || ("code " + err.code);
            if (errMsg.includes("Empty src") || !localAudio.getAttribute("src")) return;
            console.warn("Browser audio error:", err.code, errMsg);
            showLogToast("⚠️ Audio stream info: " + errMsg);
        };
        localAudio.addEventListener("timeupdate", () => {
            if (store.userRole === "client" || store.audio_output === "browser") {
                if (!window.isDraggingPb) {
                    if (typeof setPositionAnchor === "function") {
                        setPositionAnchor(localAudio.currentTime);
                    } else {
                        store.position = localAudio.currentTime;
                    }
                }
                if (typeof syncLocalLyrics === "function") syncLocalLyrics();
            }
        });
        localAudio.addEventListener("pause", () => {
            // _updateMediaSessionState HARUS selalu jalan (di luar guard) supaya
            // navigator.mediaSession.playbackState selalu cerminan audio yang
            // sebenarnya — kalau ini ikut di-skip pas _mediaSessionHandling true,
            // OS/headset masih nganggep status "playing" dan notifikasi macet
            // nunjukin tombol pause padahal audio sudah berhenti.
            _updateMediaSessionState("paused");
            if (_mediaSessionHandling || window.audioBlocked || localAudio.ended) return;
            // FIX-PAUSE-RACE-01: kalau kita masih menunggu konfirmasi toggle ke PAUSED
            // (baru saja diminta lewat tombol/media-session), pause ini kemungkinan besar
            // dipicu oleh syncBrowserAudio() kita sendiri — bukan headset/OS. Jangan kirim
            // toggle_pause lagi. Dulu ini pakai timer tetap (1500ms) yang beda sendiri dari
            // ws.js (1200ms); sekarang keduanya pakai satu sumber kebenaran yang sama.
            const _inUIGrace = isPendingToggleActive("PAUSED");
            if (!_inUIGrace && store.status === "PLAYING") {
                console.log("[audio] Native pause (headset/OS), syncing to server...");
                if (store.userRole === "admin") {
                    store.status = "PAUSED";
                    markPendingToggle("PAUSED");
                    if (typeof renderPlayBtn === "function") renderPlayBtn();
                    if (typeof renderNowPlaying === "function") renderNowPlaying();
                    if (typeof wsSend === "function") wsSend("toggle_pause");
                }
            }
        });
        localAudio.addEventListener("play", () => {
            // Sama seperti di atas: selalu sinkronkan state media session dulu,
            // baru cek guard buat keputusan kirim toggle_pause ke server atau tidak.
            _updateMediaSessionState("playing");
            if (_mediaSessionHandling || window.audioBlocked) return;
            // FIX-PAUSE-RACE-01: kalau kita masih menunggu konfirmasi toggle ke PLAYING,
            // play ini kemungkinan besar dipicu oleh syncBrowserAudio() kita sendiri —
            // bukan headset/OS. Jangan kirim toggle_pause lagi. Satu sumber kebenaran yang
            // sama dengan ws.js (lihat store.js), bukan timer tetap terpisah lagi.
            const _inUIGrace = isPendingToggleActive("PLAYING");
            if (!_inUIGrace && store.status !== "PLAYING") {
                console.log("[audio] Native play (headset/OS), syncing to server...");
                if (store.userRole === "admin") {
                    store.status = "PLAYING";
                    markPendingToggle("PLAYING");
                    if (typeof resetAnchorClock === "function") resetAnchorClock();
                    if (typeof renderPlayBtn === "function") renderPlayBtn();
                    if (typeof renderNowPlaying === "function") renderNowPlaying();
                    if (typeof wsSend === "function") wsSend("toggle_pause");
                }
            }
        });
    }
    return localAudio;
}

// PATCH-ANDROID-AUDIO-01
window.audioBlocked = false;

function _showTapToPlayBanner() {
    let el = document.getElementById('audio-unlock-banner');
    if (!el) {
        el = document.createElement('button');
        el.id = 'audio-unlock-banner';
        el.type = 'button';
        el.textContent = '\ud83d\udd0a Tap untuk lanjut memutar';
        el.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);' +
            'z-index:9999;padding:10px 18px;border-radius:999px;border:none;' +
            'background:var(--accent,#1db954);color:#fff;font-weight:600;font-size:14px;' +
            'box-shadow:0 4px 16px rgba(0,0,0,.35);cursor:pointer;';
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            _hideTapToPlayBanner();
            window.audioUnlocked = true;
            window.audioBlocked = false;

            const audio = getOrInitAudio();
            if (audio && audio.src && !audio.src.startsWith('data:')) {
                _resumeAndPlay(audio);
            } else if (typeof syncBrowserAudio === "function") {
                syncBrowserAudio(true);
            }
        });
        document.body.appendChild(el);
    }
    el.style.display = 'block';
}

function _hideTapToPlayBanner() {
    const el = document.getElementById('audio-unlock-banner');
    if (el) el.style.display = 'none';
}

async function _resumeAndPlay(audio) {
    if (audioCtx && audioCtx.state === 'suspended') {
        try { await audioCtx.resume(); } catch (e) { console.warn("[audio] ctx resume failed:", e); }
    }
    try {
        await audio.play();
        console.log("[audio] play() OK");
        window.audioBlocked = false;
        _hideTapToPlayBanner();
        if (typeof startFakeBeatLoop === "function") startFakeBeatLoop();
    } catch (e) {
        console.warn("[audio] play() blocked:", e.name, e.message);
        window.audioBlocked = true;
        _showTapToPlayBanner();
    }
}

document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume().catch(() => {});
        const isBrowser = store && (store.userRole === "client" || store.audio_output === "browser");
        if (isBrowser && store.status === "PLAYING") {
            const audio = getOrInitAudio();
            if (audio.paused && audio.src && !audio.src.startsWith("data:")) {
                _resumeAndPlay(audio);
            }
        }
    }
});

function unlockBrowserAudio(forcePlay) {
    if (audioUnlocked || _unlocking) {
        if (forcePlay && audioUnlocked) syncBrowserAudio(true);
        return;
    }
    _unlocking = true;
    console.log("[audio] unlocking via AudioContext...");

    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) {
        audioUnlocked = true;
        _unlocking = false;
        _lastLoadedVideoId = null;
        syncBrowserAudio(forcePlay);
        return;
    }

    const ctx = audioCtx || new AC();

    const doUnlock = () => {
        audioUnlocked = true;
        _unlocking = false;
        console.log("[audio] unlocked, syncing...");
        if (!audioCtx) {
            audioCtx = ctx;
        }
        if (typeof initVisualizer === "function") initVisualizer();
        _lastLoadedVideoId = null;
        syncBrowserAudio(forcePlay);
    };

    if (ctx.state === 'suspended') {
        ctx.resume().then(doUnlock).catch((e) => {
            console.warn("[audio] AudioContext resume failed:", e);
            _unlocking = false;
            audioUnlocked = true;
            _lastLoadedVideoId = null;
            syncBrowserAudio(forcePlay);
        });
    } else {
        doUnlock();
    }
}

function syncBrowserAudio(forcePlay) {
    const isBrowser = store.userRole === "client" || store.audio_output === "browser";
    const audio = getOrInitAudio();

    if (!isBrowser) {
        if (!audio.paused) audio.pause();
        return;
    }

    const track = store.current_track;
    if (!track) {
        if (!audio.paused) audio.pause();
        if (audio.hasAttribute("src") && audio.src && !audio.src.startsWith("data:")) {
            audio.removeAttribute("src");
            audio.load();
        }
        _lastLoadedVideoId = null;
        return;
    }

    const expectedSrc = window.location.origin + `/api/stream/${track.video_id}`;

    if (_lastLoadedVideoId !== track.video_id) {
        _lastLoadedVideoId = track.video_id;
        window.audioBlocked = false;
        if (typeof _hideTapToPlayBanner === "function") _hideTapToPlayBanner();
        audio.src = expectedSrc;
        if (!window.isDraggingVol) {
            audio.volume = Math.max(0, Math.min(1, (store.volume || 80) / 100));
        }

        audio.onended = () => {
            console.log("[radio] track ended, requesting next...");
            if (store.audio_output === "browser") {
                wsSend("next", { video_id: track.video_id });
            }
        };

        if (!audioUnlocked) {
            audio.oncanplay = null;
            audio.load();
            console.log("[audio] buffering, waiting for user gesture:", track.video_id);
            return;
        }

        audio.oncanplay = () => {
            audio.oncanplay = null;
            // Hanya seek jika posisi memang untuk lagu ini bukan sisa posisi lagu sebelumnya
            const isResume = store.position > 5 &&
                store.current_track &&
                store.current_track.video_id === track.video_id;
            if (isResume && Math.abs(audio.currentTime - store.position) > 5) {
                audio.currentTime = store.position;
            }
            if (forcePlay || store.status === "PLAYING") {
                console.log("[audio] canplay → play:", track.video_id);
                _resumeAndPlay(audio);
            }
        };
        audio.load();
        return;
    }

    if (!window.isDraggingVol) {
        audio.volume = Math.max(0, Math.min(1, (store.volume || 80) / 100));
    }
    if (forcePlay || store.status === "PLAYING") {
        if (audio.paused && audio.src && !audio.src.startsWith("data:") && audioUnlocked) {
            _resumeAndPlay(audio);
        }
    } else {
        if (!audio.paused) audio.pause();
    }
}

function initAudio() {
    document.addEventListener("click", unlockBrowserAudio);
}

// ── Media Session API ─────────────────────────────────────────────────────────

function _updateMediaSessionState(state) {
    if (!('mediaSession' in navigator)) return;
    try {
        navigator.mediaSession.playbackState = state; // "playing" | "paused" | "none"
    } catch(e) {}
}

let _lastMediaSessionVideoId = null;

function updateMediaSession() {
    if (!('mediaSession' in navigator)) return;
    const track = store.current_track;
    if (!track) {
        _updateMediaSessionState('none');
        navigator.mediaSession.metadata = null;
        _lastMediaSessionVideoId = null;
        return;
    }

    // Perbarui metadata hanya jika lagu berubah
    if (_lastMediaSessionVideoId !== track.video_id) {
        _lastMediaSessionVideoId = track.video_id;
        const coverUrl = track.thumbnail
            ? (track.thumbnail.startsWith('http') ? track.thumbnail : window.location.origin + track.thumbnail)
            : (window.location.origin + '/api/thumbnail/' + track.video_id);

        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title || 'Unknown',
            artist: track.artist || 'Unknown',
            album: 'LunaWave',
            artwork: [
                { src: coverUrl, sizes: '512x512', type: 'image/jpeg' }
            ]
        });

        // Helper untuk update instan sebelum menunggu respon server
        const _optimisticToggle = (wantsPlay) => {
            if (store.userRole !== "admin") return;
            store.status = wantsPlay ? "PLAYING" : "PAUSED";
            markPendingToggle(wantsPlay ? "PLAYING" : "PAUSED");
            if (wantsPlay && typeof resetAnchorClock === "function") resetAnchorClock();
            if (typeof renderPlayBtn === "function") renderPlayBtn();
            if (typeof renderNowPlaying === "function") renderNowPlaying();
            if (typeof renderQueue === "function") renderQueue();
            if (store.audio_output === "browser" && typeof syncBrowserAudio === "function") {
                unlockBrowserAudio(wantsPlay);
                syncBrowserAudio(wantsPlay);
            }
        };

        // Pasang action handler — gunakan nama action yang sesuai dengan backend Python
        navigator.mediaSession.setActionHandler('play', () => {
            if (store.status === "PLAYING") return; // Cegah double toggle jika sudah play
            _mediaSessionHandling = true;
            _optimisticToggle(true);
            if (typeof wsSend === "function") wsSend("toggle_pause");
            setTimeout(() => { _mediaSessionHandling = false; }, 300);
        });
        navigator.mediaSession.setActionHandler('pause', () => {
            if (store.status !== "PLAYING") return; // Cegah double toggle jika sudah pause
            _mediaSessionHandling = true;
            _optimisticToggle(false);
            if (typeof wsSend === "function") wsSend("toggle_pause");
            setTimeout(() => { _mediaSessionHandling = false; }, 300);
        });
        navigator.mediaSession.setActionHandler('previoustrack', () => {
            if (store.userRole === "admin") {
                store.status = "LOADING";
                if (typeof renderNowPlaying === "function") renderNowPlaying();
                if (typeof renderPlayerBar === "function") renderPlayerBar();
                const data = (store.current_track && store.current_track.video_id) ? { video_id: store.current_track.video_id } : {};
                if (typeof wsSend === "function") wsSend("prev", data);
            }
        });
        navigator.mediaSession.setActionHandler('nexttrack', () => {
            if (store.userRole === "admin") {
                store.status = "LOADING";
                if (typeof renderNowPlaying === "function") renderNowPlaying();
                if (typeof renderPlayerBar === "function") renderPlayerBar();
                const data = (store.current_track && store.current_track.video_id) ? { video_id: store.current_track.video_id } : {};
                if (typeof wsSend === "function") wsSend("next", data);
            }
        });
        navigator.mediaSession.setActionHandler('seekto', (details) => {
            if (typeof wsSend === "function") wsSend("seek", { position: details.seekTime });
        });
    }

    // Selalu sinkronkan status putar/jeda
    _updateMediaSessionState(store.status === "PLAYING" ? "playing" : "paused");
}
