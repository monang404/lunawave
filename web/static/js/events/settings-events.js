function openSettings() {
    if (dom.settingsSheet) dom.settingsSheet.classList.add("open");
    if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
    if (typeof renderSettingsSheet === "function") renderSettingsSheet();
    wsSend("get_cache_size", {});
}

function closeSettings() {
    if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
    if (typeof closeMainOverlay === "function") closeMainOverlay();
}

function renderSettingsSheet() {
    if (!dom.settingsSheet || !dom.settingsSheet.classList.contains("open")) return;
    if (dom.sbToggle) dom.sbToggle.dataset.on = store.sponsorblock_active ? "true" : "false";
    if (dom.crossfadeToggle) dom.crossfadeToggle.dataset.on = store.crossfade_enabled ? "true" : "false";
    if (dom.loudnessToggle) dom.loudnessToggle.dataset.on = store.loudness_normalization_enabled ? "true" : "false";
    // Sync speed dropdown ke nilai state saat ini
    if (dom.ssSpeedSelect && store.playback_speed) {
        dom.ssSpeedSelect.value = parseFloat(store.playback_speed).toFixed(2);
        if (dom.ssSpeedSub) dom.ssSpeedSub.textContent = parseFloat(store.playback_speed).toFixed(2) + "x";
    }
    if (dom.ssOutSub && dom.ssOutBtn) {
        if (store.audio_output === "browser") {
            dom.ssOutSub.textContent = "Keluar via browser ini";
            dom.ssOutBtn.textContent = "💻 Browser";
        } else {
            dom.ssOutSub.textContent = "Keluar via perangkat (mpv)";
            dom.ssOutBtn.textContent = "📱 Device";
        }
    }
    if (dom.ssDlRow) {
        if (store.download_progress != null) {
            dom.ssDlRow.style.display = "flex";
            const pct = Math.round(store.download_progress * 100);
            if (dom.ssDlPct) dom.ssDlPct.textContent = pct + "%";
            if (dom.ssDlFill) dom.ssDlFill.style.width = pct + "%";
            if (dom.ssDlTrack && store.current_track) {
                dom.ssDlTrack.textContent = store.current_track.title;
            }
        } else {
            dom.ssDlRow.style.display = "none";
        }
    }
    if (dom.ssHistorySub) {
        dom.ssHistorySub.textContent = (store.history_count || 0) + " lagu diputar";
    }
}

function closeMainOverlay() {
    if (dom.mainOverlay) dom.mainOverlay.classList.remove("open");
    if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
    if (dom.actionSheet) dom.actionSheet.classList.remove("open");
    if (dom.helpSheet) dom.helpSheet.classList.remove("open");
    if (dom.artistDetailSheet) dom.artistDetailSheet.classList.remove("open");
}

function initSettingsEvents() {
    if (dom.btnSettings) {
        dom.btnSettings.addEventListener("click", () => {
            if (dom.settingsSheet && dom.settingsSheet.classList.contains("open")) {
                closeSettings();
            } else {
                openSettings();
            }
        });
    }

    if (dom.mainOverlay) {
        dom.mainOverlay.addEventListener("click", closeMainOverlay);
    }

    if (dom.sbToggle) {
        dom.sbToggle.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            const newVal = dom.sbToggle.dataset.on !== "true";
            dom.sbToggle.dataset.on = newVal ? "true" : "false";
            store.sponsorblock_active = newVal;
            wsSend("set_sponsorblock", { enabled: newVal });
        });
    }

    if (dom.ssOutBtn) {
        dom.ssOutBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            const newOutput = store.audio_output === "browser" ? "device" : "browser";
            if (newOutput === "browser" && typeof unlockBrowserAudio === "function") unlockBrowserAudio();
            wsSend("set_output", { output: newOutput });
            closeSettings();
        });
    }

    if (dom.crossfadeToggle) {
        dom.crossfadeToggle.addEventListener('click', () => {
            if (store.userRole !== 'admin') return;
            const current = store.crossfade_enabled;
            wsSend("set_crossfade", { enabled: !current });
        });
    }

    if (dom.loudnessToggle) {
        dom.loudnessToggle.addEventListener('click', () => {
            if (store.userRole !== 'admin') return;
            const current = store.loudness_normalization_enabled;
            wsSend("set_loudness_normalization", { enabled: !current });
        });
    }

    if (dom.ssStopBtn) {
        dom.ssStopBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            wsSend("stop");
            closeSettings();
        });
    }

    if (dom.ssHistoryBtn) {
        dom.ssHistoryBtn.addEventListener('click', () => {
            closeSettings();
            if (typeof switchTab === "function") switchTab('discover');
            wsSend('discover', {});
            setTimeout(() => {
                if (dom.discRecent) {
                    dom.discRecent.scrollIntoView({ behavior: 'smooth' });
                }
            }, 300);
        });
    }

    if (dom.ssCacheClearBtn) {
        dom.ssCacheClearBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (confirm("Bersihkan cache MP3 sementara? (Track yang diunduh manual tidak akan dihapus)")) {
                if (dom.ssCacheSub) dom.ssCacheSub.textContent = "Membersihkan...";
                wsSend("clear_cache", {});
            }
        });
    }

    if (dom.ssSleepSelect) {
        let _sleepCountdownInterval = null;

        function startSleepCountdown(minutes) {
            if (_sleepCountdownInterval) clearInterval(_sleepCountdownInterval);
            if (minutes <= 0) {
                if (dom.ssSleepSub) dom.ssSleepSub.textContent = "Mati";
                return;
            }
            let remaining = minutes * 60; // detik
            function tick() {
                if (remaining <= 0) {
                    clearInterval(_sleepCountdownInterval);
                    _sleepCountdownInterval = null;
                    if (dom.ssSleepSub) dom.ssSleepSub.textContent = "Mati";
                    if (dom.ssSleepSelect) dom.ssSleepSelect.value = "0";
                    return;
                }
                const m = Math.floor(remaining / 60);
                const s = remaining % 60;
                if (dom.ssSleepSub) dom.ssSleepSub.textContent = `${m}:${String(s).padStart(2,'0')} tersisa`;
                remaining--;
            }
            tick();
            _sleepCountdownInterval = setInterval(tick, 1000);
        }

        dom.ssSleepSelect.addEventListener("change", (e) => {
            if (store.userRole !== "admin") return;
            const minutes = parseInt(e.target.value);
            startSleepCountdown(minutes);
            wsSend("set_sleep_timer", { minutes });
        });
    }

    if (dom.ssSpeedSelect) {
        dom.ssSpeedSelect.addEventListener("change", (e) => {
            if (store.userRole !== "admin") return;
            const speed = parseFloat(e.target.value);
            store.playback_speed = speed;
            if (dom.ssSpeedSub) {
                dom.ssSpeedSub.textContent = speed.toFixed(2) + "x";
            }
            // Langsung apply ke browser audio tanpa tunggu round-trip server
            if (store.audio_output === "browser" && typeof getOrInitAudio === "function") {
                const audio = getOrInitAudio();
                if (audio) audio.playbackRate = speed;
            }
            wsSend("set_speed", { speed });
        });
    }

    if (dom.btnHelp) {
        dom.btnHelp.addEventListener("click", () => {
            if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
            if (dom.helpSheet) dom.helpSheet.classList.add("open");
            if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
        });
    }

    if (dom.helpCloseBtn) {
        dom.helpCloseBtn.addEventListener("click", () => {
            if (dom.helpSheet) dom.helpSheet.classList.remove("open");
            closeMainOverlay();
        });
    }
}
