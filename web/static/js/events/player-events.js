function initPlayerEvents() {
    if (dom.pbTrackInfo) {
        dom.pbTrackInfo.addEventListener("click", () => {
            if (store.active_tab !== "home" && typeof switchTab === "function") {
                switchTab("home");
            }
        });
    }

    dom.btnPlay.addEventListener("click", () => {
        if (store.userRole === "admin") {
            // PATCH-AUDIO-UNLOCK-RACE-01: simpan intent SEBELUM store.status di-flip, supaya
            const wantsPlay = store.status !== "PLAYING";
            store.status = wantsPlay ? "PLAYING" : "PAUSED";
            window.lastToggleTime = Date.now();
            renderPlayBtn();
            renderNowPlaying();
            renderQueue();
            if (store.audio_output === "browser" && typeof syncBrowserAudio === "function") {
                unlockBrowserAudio(wantsPlay);
                syncBrowserAudio(wantsPlay);
            }
            wsSend(WS_ACTIONS.TOGGLE_PAUSE);
        }
    });

    dom.btnNext.addEventListener("click", () => {
        if (store.userRole === "admin") {
            const data = {};
            if (store.current_track && store.current_track.video_id) {
                data.video_id = store.current_track.video_id;
            }
            store.status = "LOADING";
            renderNowPlaying();
            renderPlayerBar();
            wsSend(WS_ACTIONS.NEXT, data);
        }
    });

    dom.btnPrev.addEventListener("click", () => {
        if (store.userRole === "admin") {
            store.status = "LOADING";
            renderNowPlaying();
            renderPlayerBar();
            wsSend(WS_ACTIONS.PREV);
        }
    });

    if (dom.btnStop) {
        dom.btnStop.addEventListener('click', () => {
            if (store.userRole === 'admin') wsSend(WS_ACTIONS.STOP);
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
                if (audio) audio.volume = Math.max(0, Math.min(1, store.volume / 150));
            }
        });
        dom.volSlider.addEventListener("change", () => {
            if (store.userRole === "admin") {
                wsSend(WS_ACTIONS.VOLUME_SET, { volume: store.volume });
            }
            window.isDraggingVol = false;
        });
    }

    if (dom.btnDownload) {
        dom.btnDownload.addEventListener("click", () => {
            if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
            closeMainOverlay();
            if (store.userRole === "admin") wsSend(WS_ACTIONS.DOWNLOAD);
        });
    }

    window.isDraggingPb = false;
    function updatePb(e) {
        if (store.userRole !== "admin") return 0;
        const rect = dom.pbProgressTrack.getBoundingClientRect();
        let pct = (e.clientX - rect.left) / rect.width;
        pct = Math.max(0, Math.min(1, pct));
        const dur = store.current_track ? store.current_track.duration : 0;
        if (dom.pbProgressFill) dom.pbProgressFill.style.width = (pct * 100) + "%";
        const thumb = dom.pbProgressTrack.querySelector('.pb-thumb');
        if (thumb) thumb.style.left = (pct * 100) + "%";
        if (dom.pbTimePos) dom.pbTimePos.textContent = formatTime(pct * dur);
        const playerBar = document.getElementById("player-bar");
        if (playerBar) playerBar.style.setProperty("--mini-progress", (pct * 100) + "%");
        return pct;
    }
    if (dom.pbProgressTrack) {
        dom.pbProgressTrack.addEventListener("pointerdown", (e) => {
            if (store.userRole !== "admin") return;
            window.isDraggingPb = true;
            dom.pbProgressTrack.setPointerCapture(e.pointerId);
            updatePb(e);
        });
        dom.pbProgressTrack.addEventListener("pointermove", (e) => {
            if (window.isDraggingPb) updatePb(e);
        });
        dom.pbProgressTrack.addEventListener("pointerup", (e) => {
            if (!window.isDraggingPb) return;
            window.isDraggingPb = false;
            dom.pbProgressTrack.releasePointerCapture(e.pointerId);
            const pct = updatePb(e);
            const dur = store.current_track ? store.current_track.duration : 0;
            if (dur > 0) {
                const targetPos = pct * dur;
                if (store.audio_output === "browser" && typeof getOrInitAudio === "function") {
                    const audio = getOrInitAudio();
                    if (audio && audio.src) {
                        audio.currentTime = targetPos;
                        store.position = targetPos;
                        renderProgress();
                    }
                }
                wsSend(WS_ACTIONS.SEEK, { position: targetPos });
            }
        });
    }

    if (dom.radioToggleBtn) {
        dom.radioToggleBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (store.status === "LOADING") return;
            const newMode = store.playback_mode === "RADIO" ? "QUEUE" : "RADIO";
            store.playback_mode = newMode;
            renderRadio();
            renderQueue();
            wsSend(WS_ACTIONS.SET_MODE, { mode: newMode });
        });
    }

    if (dom.radioRandomizeBtn) {
        dom.radioRandomizeBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            store.radio_queue = [];
            store.current_track = null;
            store.status = "LOADING";
            store.position = 0;
            renderRadio();
            renderQueue();
            renderNowPlaying();
            window.scrollTo({ top: 0, behavior: "smooth" });
            wsSend(WS_ACTIONS.RADIO_RANDOMIZE, { seed_artist: null });
        });
    }

    if (dom.btnFavorite) {
        dom.btnFavorite.addEventListener("click", () => {
            if (store.userRole === "admin" && store.current_track) {
                wsSend(WS_ACTIONS.TOGGLE_FAVORITE, { video_id: store.current_track.video_id });
            }
        });
    }

    if (dom.outputToggleBtn) {
        dom.outputToggleBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            const newOutput = store.audio_output === "browser" ? "device" : "browser";
            if (newOutput === "browser" && typeof unlockBrowserAudio === "function") unlockBrowserAudio();
            wsSend(WS_ACTIONS.SET_OUTPUT, { output: newOutput });
        });
    }

    const searchClearBtn = document.getElementById("search-clear-btn");
    if (searchClearBtn) {
        searchClearBtn.addEventListener("click", () => {
            dom.searchInput.value = "";
            searchClearBtn.style.display = "none";
            dom.searchInput.dispatchEvent(new Event("input"));
            dom.searchInput.focus();
        });
    }

    const searchHeader = document.getElementById("search-header");
    if (searchHeader && dom.searchInput) {
        const updateSearchHeaderCollapse = () => {
            const hasValue = !!dom.searchInput.value.trim();
            const isFocused = document.activeElement === dom.searchInput;
            if (hasValue || isFocused) {
                searchHeader.classList.add("collapsed");
            } else {
                searchHeader.classList.remove("collapsed");
            }
        };
        dom.searchInput.addEventListener("input", updateSearchHeaderCollapse);
        dom.searchInput.addEventListener("focus", updateSearchHeaderCollapse);
        dom.searchInput.addEventListener("blur", updateSearchHeaderCollapse);
        updateSearchHeaderCollapse();
    }

    let searchTimer = null;
    let lastSearchQuery = "";
    if (dom.searchInput) {
        dom.searchInput.addEventListener("input", (e) => {
            if (searchClearBtn) searchClearBtn.style.display = e.target.value ? "block" : "none";
            const q = e.target.value.trim();
            if (searchTimer) clearTimeout(searchTimer);
            if (!q) {
                dom.searchMsg.textContent = "Ketik nama lagu atau artis";
                dom.searchMsg.style.display = "block";
                dom.searchResults.innerHTML = "";
                dom.searchResults.style.display = "none";
                lastSearchQuery = "";
                return;
            }
            if (q !== lastSearchQuery) {
                lastSearchQuery = q;
                searchTimer = setTimeout(() => {
                    dom.searchMsg.innerHTML = '<span class="spinner"></span> Mencari...';
                    dom.searchMsg.style.display = "block";
                    dom.searchResults.style.display = "none";
                    wsSend(WS_ACTIONS.SEARCH, { query: q });
                }, 500);
            }
        });

        dom.searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const q = e.target.value.trim();
                if (q) {
                    if (searchTimer) clearTimeout(searchTimer);
                    lastSearchQuery = q;
                    dom.searchMsg.innerHTML = '<span class="spinner"></span> Mencari...';
                    dom.searchMsg.style.display = "block";
                    dom.searchResults.style.display = "none";
                    wsSend(WS_ACTIONS.SEARCH, { query: q });
                }
            }
        });
    }

    if (dom.searchResults) {
        dom.searchResults.addEventListener("click", (e) => {
            const item = e.target.closest(".sr-item");
            if (item && item.dataset.searchTrackStr) {
                try {
                    const track = JSON.parse(item.dataset.searchTrackStr);
                    playSearchTrack(track);
                } catch (err) {
                    console.error("Invalid track data", err);
                }
            }
        });
    }

    if (dom.actionPlayNow) {
        dom.actionPlayNow.addEventListener("click", () => {
            if (window.pendingTrack) wsSend(WS_ACTIONS.PLAY_TRACK, window.pendingTrack);
            hideActionModal();
        });
    }

    if (dom.actionEnqueue) {
        dom.actionEnqueue.addEventListener("click", () => {
            if (window.pendingTrack) wsSend(WS_ACTIONS.QUEUE_ADD, window.pendingTrack);
            hideActionModal();
        });
    }

    if (dom.actionCancel) {
        dom.actionCancel.addEventListener("click", () => {
            hideActionModal();
        });
    }

    if (dom.actionDelete) {
        dom.actionDelete.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (window.pendingTrack) {
                wsSend(WS_ACTIONS.DELETE_DOWNLOAD, window.pendingTrack);
            }
            hideActionModal();
        });
    }

    document.addEventListener("click", (e) => {
        const moreBtn = e.target.closest(".sr-more-btn");
        if (moreBtn) {
            const item = moreBtn.closest(".sr-item");
            if (item) {
                const trackStr = item.dataset.trackStr || item.dataset.searchTrackStr;
                if (trackStr) {
                    try {
                        const track = JSON.parse(trackStr);
                        showActionModal(track);
                    } catch (err) { console.error(err); }
                }
            }
            return;
        }

        const srItem = e.target.closest(".sr-item");
        if (srItem) {
            const trackStr = srItem.dataset.trackStr || srItem.dataset.searchTrackStr;
            if (trackStr) {
                try {
                    const track = JSON.parse(trackStr);
                    if (store.userRole === "admin") {
                        wsSend(WS_ACTIONS.PLAY_TRACK, track);
                    }
                } catch (err) { console.error(err); }
            }
            return;
        }

        const card = e.target.closest(".disc-card, .fav-card, .search-result-item");
        if (card && card.dataset.vid) {
            let track = null;
            if (card.classList.contains("search-result-item") && card.dataset.searchTrackStr) {
                track = JSON.parse(card.dataset.searchTrackStr);
            } else {
                const vid = card.dataset.vid;
                const lists = [
                    store.discover_recent || [],
                    store.discover_favorites || [],
                    store.discover_cached || [],
                    store.queue || []
                ];
                for (const list of lists) {
                    track = list.find(t => t.video_id === vid);
                    if (track) break;
                }
            }
            if (track && typeof showActionModal === "function") showActionModal(track);
            return;
        }
    });

    document.addEventListener("keydown", (e) => {
        const active = document.activeElement;
        if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) {
            if (e.key === "Escape") active.blur();
            return;
        }

        switch (e.key) {
            case " ":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend(WS_ACTIONS.TOGGLE_PAUSE);
                break;
            case "n":
            case "N":
                if (store.userRole !== "admin") return;
                wsSend(WS_ACTIONS.NEXT);
                break;
            case "b":
            case "B":
                if (store.userRole !== "admin") return;
                wsSend(WS_ACTIONS.PREV);
                break;
            case "s":
            case "S":
                if (store.userRole !== "admin") return;
                wsSend(WS_ACTIONS.STOP);
                break;
            case "ArrowUp":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend(WS_ACTIONS.VOLUME_UP);
                break;
            case "ArrowDown":
                if (store.userRole !== "admin") return;
                e.preventDefault();
                wsSend(WS_ACTIONS.VOLUME_DOWN);
                break;
            case "m":
            case "M":
                if (store.userRole !== "admin") return;
                wsSend(WS_ACTIONS.DOWNLOAD);
                break;
            case "r":
            case "R":
                if (store.userRole !== "admin") return;
                if (store.status === "LOADING") break;
                const newMode = store.playback_mode === "RADIO" ? "QUEUE" : "RADIO";
                wsSend(WS_ACTIONS.SET_MODE, { mode: newMode });
                break;
            case "l":
            case "L":
                if (dom.lyricsSheet) {
                    const isOpen = dom.lyricsSheet.classList.contains("open");
                    if (isOpen) {
                        dom.lyricsSheet.classList.remove("open");
                        closeMainOverlay();
                    } else {
                        dom.lyricsSheet.classList.add("open");
                        if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
                        renderLyrics();
                    }
                }
                break;
            case "/":
                e.preventDefault();
                switchTab("search");
                break;
            case "?":
                if (dom.helpSheet) {
                    if (dom.helpSheet.classList.contains("open")) { 
                        dom.helpSheet.classList.remove("open"); 
                        closeMainOverlay(); 
                    } else { 
                        dom.helpSheet.classList.add("open"); 
                        if (dom.mainOverlay) dom.mainOverlay.classList.add("open"); 
                    }
                }
                break;
            case "Escape":
                hideActionModal();
                if (dom.helpSheet) dom.helpSheet.classList.remove("open");
                if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
                if (dom.lyricsSheet) dom.lyricsSheet.classList.remove("open");
                closeMainOverlay();
                break;
        }
    });
}
