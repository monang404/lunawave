function initTransportEvents() {
    if (dom.pbTrackInfo) {
        dom.pbTrackInfo.addEventListener("click", () => {
            if (store.active_tab !== "home" && typeof switchTab === "function") {
                switchTab("home");
            }
        });
    }

    dom.btnPlay.addEventListener("click", () => {
        if (store.userRole === "admin") {
            const wantsPlay = store.status !== "PLAYING";
            store.status = wantsPlay ? "PLAYING" : "PAUSED";
            window.lastToggleTime = Date.now();
            if (wantsPlay && typeof resetAnchorClock === "function") resetAnchorClock();
            if (typeof renderPlayBtn === "function") renderPlayBtn();
            if (typeof renderNowPlaying === "function") renderNowPlaying();
            if (typeof renderQueue === "function") renderQueue();
            if (store.audio_output === "browser" && typeof syncBrowserAudio === "function") {
                unlockBrowserAudio(wantsPlay);
                syncBrowserAudio(wantsPlay);
            }
            wsSend("toggle_pause");
        }
    });

    dom.btnNext.addEventListener("click", () => {
        if (store.userRole === "admin") {
            const data = {};
            if (store.current_track && store.current_track.video_id) {
                data.video_id = store.current_track.video_id;
            }
            store.status = "LOADING";
            if (typeof renderNowPlaying === "function") renderNowPlaying();
            if (typeof renderPlayerBar === "function") renderPlayerBar();
            wsSend("next", data);
        }
    });

    dom.btnPrev.addEventListener("click", () => {
        if (store.userRole === "admin") {
            store.status = "LOADING";
            if (typeof renderNowPlaying === "function") renderNowPlaying();
            if (typeof renderPlayerBar === "function") renderPlayerBar();
            wsSend("prev");
        }
    });

    if (dom.btnStop) {
        dom.btnStop.addEventListener('click', () => {
            if (store.userRole === 'admin') wsSend('stop');
        });
    }

    if (dom.volSlider) {
        window.isDraggingVol = false;
        dom.volSlider.addEventListener("input", () => {
            window.isDraggingVol = true;
            store.volume = parseInt(dom.volSlider.value);
            if (dom.pbVolLabel) dom.pbVolLabel.textContent = store.volume + "%";
            if (store.audio_output === "browser" && typeof getOrInitAudio === "function") {
                const audio = getOrInitAudio();
                if (audio) audio.volume = Math.max(0, Math.min(1, store.volume / 100));
            }
        });
        dom.volSlider.addEventListener("change", () => {
            if (store.userRole === "admin") {
                wsSend("volume_set", { volume: store.volume });
            }
            window.isDraggingVol = false;
        });
    }

    if (dom.btnDownload) {
        dom.btnDownload.addEventListener("click", () => {
            if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
            if (typeof closeMainOverlay === "function") closeMainOverlay();
            if (store.userRole === "admin") wsSend("download");
        });
    }

    if (dom.radioToggleBtn) {
        dom.radioToggleBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (store.status === "LOADING") return;
            const newMode = store.playback_mode === "RADIO" ? "QUEUE" : "RADIO";
            store.playback_mode = newMode;
            if (typeof renderRadio === "function") renderRadio();
            if (typeof renderQueue === "function") renderQueue();
            wsSend("set_mode", { mode: newMode });
        });
    }

    if (dom.radioRandomizeBtn) {
        dom.radioRandomizeBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            store.radio_queue = [];
            store.current_track = null;
            store.status = "LOADING";
            if (typeof setPositionAnchor === "function") {
                setPositionAnchor(0);
            } else {
                store.position = 0;
            }
            if (typeof renderRadio === "function") renderRadio();
            if (typeof renderQueue === "function") renderQueue();
            if (typeof renderNowPlaying === "function") renderNowPlaying();
            window.scrollTo({ top: 0, behavior: "smooth" });
            wsSend("radio_randomize", { seed_artist: null });
        });
    }

    if (dom.outputToggleBtn) {
        dom.outputToggleBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            const newOutput = store.audio_output === "browser" ? "device" : "browser";
            if (newOutput === "browser" && typeof unlockBrowserAudio === "function") unlockBrowserAudio();
            wsSend("set_output", { output: newOutput });
        });
    }
}
