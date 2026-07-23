const audioPool = [new Audio(), new Audio()];
const CROSSFADE_DURATION = 5.0; // Edit durasi crossfade di sini (dalam detik)

let activeAudioIndex = 0;
let _fadeIntervals = [null, null];
let audioUnlocked = false;
let _unlocking = false; // guard agar tidak double-call saat masih proses
let _lastLoadedVideoId = null;

let audioCtx = null;
let analyser = null;
let dataArray = null;

// Flag untuk mencegah infinite loop antara native audio event dan Media Session handler
let _mediaSessionHandling = false;

function getOrInitAudio() {
    return audioPool[activeAudioIndex];
}

function initAudioPool() {
    audioPool.forEach((audio, idx) => {
        audio.preload = "auto";
        audio.onerror = (e) => {
            const err = audio.error;
            if (!err) return;
            if (err.code === 1) return;
            if (err.code === 4 && audio.src.includes("data:audio")) return;
            const errMsg = err.message || ("code " + err.code);
            if (errMsg.includes("Empty src") || !audio.getAttribute("src")) return;
            console.warn("Browser audio error:", err.code, errMsg);
            showLogToast("⚠️ Audio stream info: " + errMsg);
        };
        audio.addEventListener("timeupdate", () => {
            if (idx !== activeAudioIndex) return;
            if (store.userRole === "client" || store.audio_output === "browser") {
                if (!window.isDraggingPb) {
                    if (typeof setPositionAnchor === "function") {
                        setPositionAnchor(audio.currentTime);
                    } else {
                        store.position = audio.currentTime;
                    }
                }
                if (typeof syncLocalLyrics === "function") syncLocalLyrics();
            }
        });
        audio.addEventListener("pause", () => {
            if (idx !== activeAudioIndex) return;
            _updateMediaSessionState("paused");
            if (_mediaSessionHandling || window.audioBlocked || audio.ended) return;
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
        audio.addEventListener("play", () => {
            if (idx !== activeAudioIndex) return;
            _updateMediaSessionState("playing");
            if (_mediaSessionHandling || window.audioBlocked) return;
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
    });
}
initAudioPool();

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
        if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume().catch(() => { });
        const isBrowser = store && (store.userRole === "client" || store.audio_output === "browser");
        if (isBrowser && store.status === "PLAYING") {
            const audio = getOrInitAudio();
            if (audio.paused && audio.src && !audio.src.startsWith("data:")) {
                _resumeAndPlay(audio);
            }
        }
        if (typeof startProgressClock === "function" && store.status === "PLAYING") startProgressClock();
        if (typeof resumeVisualizerLoop === "function") resumeVisualizerLoop();
        if (typeof setRadioHeroAnimState === "function" && dom.radioToggleBtn) {
            setRadioHeroAnimState(dom.radioToggleBtn.dataset.on === "true");
        }
    } else {
        if (typeof stopProgressClock === "function") stopProgressClock();
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

function _fadeVolume(audio, targetVolume, durationSec, callback) {
    const steps = 15;
    const intervalMs = (durationSec * 1000) / steps;
    const initialVol = audio.volume;
    const volStep = (targetVolume - initialVol) / steps;
    let stepCount = 0;

    const idx = audioPool.indexOf(audio);
    if (idx !== -1) {
        if (_fadeIntervals[idx]) clearInterval(_fadeIntervals[idx]);
        _fadeIntervals[idx] = setInterval(() => {
            stepCount++;
            let newVol = initialVol + (volStep * stepCount);
            if (newVol < 0) newVol = 0;
            if (newVol > 1) newVol = 1;
            audio.volume = newVol;
            if (stepCount >= steps) {
                clearInterval(_fadeIntervals[idx]);
                _fadeIntervals[idx] = null;
                if (callback) callback();
            }
        }, intervalMs);
    }
}

function syncBrowserAudio(forcePlay) {
    const isBrowser = store.userRole === "client" || store.audio_output === "browser";

    if (!isBrowser) {
        audioPool.forEach(a => { if (!a.paused) a.pause(); });
        return;
    }

    const track = store.current_track;
    if (!track) {
        audioPool.forEach(a => {
            if (!a.paused) a.pause();
            if (a.hasAttribute("src") && a.src && !a.src.startsWith("data:")) {
                a.removeAttribute("src");
                a.load();
            }
        });
        _lastLoadedVideoId = null;
        return;
    }

    const expectedSrc = window.location.origin + `/api/stream/${track.video_id}`;

    if (_lastLoadedVideoId !== track.video_id) {
        _lastLoadedVideoId = track.video_id;
        window.audioBlocked = false;
        if (typeof _hideTapToPlayBanner === "function") _hideTapToPlayBanner();

        // Switch active audio element
        const prevAudio = audioPool[activeAudioIndex];
        activeAudioIndex = (activeAudioIndex + 1) % 2;
        const audio = audioPool[activeAudioIndex];

        // Crossfade out previous audio if enabled and playing
        if (store.crossfade_enabled && !prevAudio.paused && prevAudio.src && !prevAudio.src.startsWith("data:")) {
            console.log("[audio] crossfade out previous track");
            _fadeVolume(prevAudio, 0, CROSSFADE_DURATION, () => {
                prevAudio.pause();
            });
        } else {
            prevAudio.pause();
        }

        audio.src = expectedSrc;

        let _crossfadeTriggered = false;

        audio.ontimeupdate = () => {
            if (store.crossfade_enabled && audio.duration > 0) {
                const remaining = audio.duration - audio.currentTime;
                if (remaining <= CROSSFADE_DURATION && remaining > 0 && !_crossfadeTriggered) {
                    _crossfadeTriggered = true;
                    console.log("[audio] crossfade overlap triggered");
                    if (store.audio_output === "browser") {
                        wsSend("next", { video_id: track.video_id });
                    }
                }
            }
        };

        audio.onended = () => {
            if (!_crossfadeTriggered || !store.crossfade_enabled) {
                console.log("[radio] track ended, requesting next...");
                if (store.audio_output === "browser") {
                    wsSend("next", { video_id: track.video_id });
                }
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
                if (store.crossfade_enabled && !isResume) {
                    audio.volume = 0;
                    _resumeAndPlay(audio);
                    const targetVol = Math.max(0, Math.min(1, (store.volume || 80) / 100));
                    _fadeVolume(audio, targetVol, CROSSFADE_DURATION);
                } else {
                    if (!window.isDraggingVol) {
                        audio.volume = Math.max(0, Math.min(1, (store.volume || 80) / 100));
                    }
                    _resumeAndPlay(audio);
                }
            }
        };
        audio.load();
        return;
    }

    const audio = getOrInitAudio();
    if (!window.isDraggingVol && !_fadeIntervals[activeAudioIndex]) {
        audio.volume = Math.max(0, Math.min(1, (store.volume || 80) / 100));
    }
    if (forcePlay || store.status === "PLAYING") {
        if (audio.paused && audio.src && !audio.src.startsWith("data:") && audioUnlocked) {
            _resumeAndPlay(audio);
        }
    } else {
        audioPool.forEach((a, i) => {
            if (!a.paused) a.pause();
            if (_fadeIntervals[i]) {
                clearInterval(_fadeIntervals[i]);
                _fadeIntervals[i] = null;
            }
        });
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
    } catch (e) { }
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
            if (wantsPlay && store.audio_output === "browser" && typeof syncBrowserAudio === "function") {
                unlockBrowserAudio(true);
            }
        };

        // Pasang action handler — gunakan nama action yang sesuai dengan backend Python
        try {
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
        } catch (e) {
            console.warn("[audio] Media Session API tidak didukung atau error:", e);
        }
    }

    // Selalu sinkronkan status putar/jeda
    _updateMediaSessionState(store.status === "PLAYING" ? "playing" : "paused");
}
