// --- config.js ---
const ITUNES_API_URL = "https://itunes.apple.com/search";
const TABS = ["home", "search", "radio", "discover"];

// --- store.js ---
const store = {
    status: "IDLE",
    playback_mode: "QUEUE",
    audio_output: "browser",
    userRole: "portal",
    adminUsername: "",
    current_track: null,
    position: 0,
    volume: 80,
    sponsorblock_active: true,
    queue: [],
    radio_queue: [],
    history_count: 0,
    lyrics_lines: [],
    lyrics_index: 0,
    lyrics_offset: 0,
    active_tab: "home",
    error_msg: null,
    is_online: true,
    download_progress: null,
    discover_recent: [],
    discover_favorites: [],
    discover_cached: [],
    search_results: [],
    server_ts: 0
};

// --- dom.js ---
const $ = (id) => document.getElementById(id);
const dom = {};
function initDOM() {
    Object.assign(dom, {
        portalScreen: $("portal-screen"),
        portalClientBtn: $("portal-client-btn"),
        portalAdminBtn: $("portal-admin-btn"),
        portalLoginForm: $("portal-login-form"),
        adminUsername: $("admin-username"),
        adminPassword: $("admin-password"),
        adminSubmitBtn: $("admin-submit-btn"),
        loginErrorMsg: $("login-error-msg"),
        logoutBtn: $("logout-btn"),
        appContainer: $("app"),
        tabHome: $("tab-home"),
        tabSearch: $("tab-search"),
        tabRadio: $("tab-radio"),
        tabDiscover: $("tab-discover"),
        outputToggleBtn: $("output-toggle-btn"),
        statusDot: $("status-dot"),
        statusText: $("status-text"),
        npTitle: $("np-title"),
        npArtist: $("np-artist"),
        npThumbnail: $("np-thumbnail"),
        npDurMeta: $("np-dur-meta"),
        npThumbIcon: $("np-thumb-icon"),
        npEqAnim: $("np-eq-anim"),
        vinylWrap: $("vinyl-wrap"),
        vinylRecord: $("vinyl-record"),
        vinylCover: $("vinyl-cover"),
        vinylIcon: $("vinyl-icon"),
        lyricsWrap: $("lyrics-wrap"),
        lyricsTextContainer: $("lyrics-text-container"),
        homeEqualizer: $("home-equalizer"),
        lyricsPrev: $("lyrics-prev"),
        lyricsCurrent: $("lyrics-current"),
        lyricsNext: $("lyrics-next"),
        searchInput: $("search-input"),
        searchMsg: $("search-msg"),
        searchResults: $("search-results"),
        radioToggleWrap: $("radio-toggle-wrap"),
        radioToggleBtn: $("radio-toggle-btn"),
        rtSub: $("rt-sub"),
        radioRandomizeBtn: $("radio-randomize-btn"),
        radioQueueList: $("radio-queue-list"),
        queueList: $("queue-list"),
        queueFooter: $("queue-footer"),
        lyricsPanel: $("lyrics-panel"),
        lyricsContent: $("lyrics-content"),
        lyricOffsetMinus: $("lyric-offset-minus"),
        lyricOffsetPlus: $("lyric-offset-plus"),
        lyricOffsetDisplay: $("lyric-offset-display"),
        pbTrackInfo: $("pb-track-info"),
        pbModeBadge: $("pb-mode-badge"),
        pbTimePos: $("pb-time-pos"),
        pbTimeDur: $("pb-time-dur"),
        pbProgressTrack: $("pb-progress-track"),
        pbProgressFill: $("pb-progress-fill"),
        pbVolLabel: $("pb-vol-label"),
        volSlider: $("vol-slider"),
        btnPrev: $("btn-prev"),
        btnPlay: $("btn-play"),
        btnNext: $("btn-next"),
        btnSettings: $("btn-settings"),
        btnDownload: $("btn-download"),
        btnHelp: $("btn-help"),
        btnLyrics: $("btn-lyrics"),
        btnFavorite: $("btn-favorite"),
        pbCacheBadge: $("pb-cache-badge"),
        pbSbBadge: $("pb-sb-badge"),
        pbDlBadge: $("pb-dl-badge"),
        mainOverlay: $("main-overlay"),
        settingsSheet: $("settings-sheet"),
        sbToggle: $("sb-toggle"),
        ssOutBtn: $("ss-out-btn"),
        ssOutSub: $("ss-out-sub"),
        ssStopBtn: $("ss-stop-btn"),
        ssDlRow: $("ss-dl-row"),
        ssDlTrack: $("ss-dl-track"),
        ssDlPct: $("ss-dl-pct"),
        ssDlFill: $("ss-dl-fill"),
        ssHistorySub: $("ss-history-sub"),
        ssHistoryBtn: $("ss-history-btn"),
        actionSheet: $("action-sheet"),
        actionTitle: $("action-sheet-title"),
        actionPlayNow: $("action-play-now"),
        actionEnqueue: $("action-enqueue"),
        actionDelete: $("action-delete"),
        actionCancel: $("action-cancel"),
        helpSheet: $("help-sheet"),
        helpCloseBtn: $("help-close-btn"),
        lyricsSheet: $("lyrics-sheet"),
        lyricsCloseBtn: $("lyrics-close-btn"),
        connectionToast: $("connection-toast"),
        logToast: $("log-toast"),
        discFavorites: $("discover-favorites"),
        discRecent: $("discover-recent"),
        discCached: $("discover-cached"),
        discArtists: $("discover-artists"),
        discGenres: $("discover-genres")
    });
}

// --- utils.js ---
function formatTime(seconds) {
    if (!seconds || seconds < 0) return "00:00";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return String(minutes).padStart(2, "0") + ":" + String(remainingSeconds).padStart(2, "0");
}
window.safeStorage = {
    get: function(key) {
        try { return localStorage.getItem(key); } catch(e) { return null; }
    },
    set: function(key, value) {
        try { localStorage.setItem(key, value); } catch(e) {}
    },
    remove: function(key) {
        try { localStorage.removeItem(key); } catch(e) {}
    }
};
function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
function showConnectionToast(text, type) {
    dom.connectionToast.textContent = text;
    dom.connectionToast.className = "active " + type;
}
function hideConnectionToast() {
    dom.connectionToast.className = "";
}
let logToastTimer = null;
function showLogToast(text) {
    dom.logToast.textContent = text;
    dom.logToast.classList.add("active");
    if (logToastTimer) clearTimeout(logToastTimer);
    logToastTimer = setTimeout(() => {
        dom.logToast.classList.remove("active");
    }, 3000);
}
window.cleanTrackTitle = function(title) {
    if (!title) return "";
    return title.replace(/[\[\(].*?(official|music video|lyric|audio|live|performance).*?[\]\)]/gi, '')
                .replace(/#\S+/g, '')
                .replace(/\s{2,}/g, ' ')
                .replace(/\s+-\s*$/, '')
                .trim();
};
window.getCoverArt = async function(track) {
    if (!track) return "";
    if (!track.video_id) return track.thumbnail || "";
    const cacheKey = "cover_" + track.video_id;
    const cachedStr = window.safeStorage.get(cacheKey);
    if (cachedStr) {
        try {
            if (cachedStr.startsWith("{")) {
                const cached = JSON.parse(cachedStr);
                if (Date.now() - cached.ts < 7 * 24 * 60 * 60 * 1000) {
                    return cached.url;
                }
            } else {
                return cachedStr;
            }
        } catch(e) {}
    }
    const ytFallback = `https://i.ytimg.com/vi/${track.video_id}/mqdefault.jpg`;
    if (!track.title || !track.artist) {
        let fallback = track.thumbnail || ytFallback;
        if (typeof fallback === "string") {
            fallback = fallback.replace("hqdefault.jpg", "mqdefault.jpg").replace("sddefault.jpg", "mqdefault.jpg");
        }
        return fallback;
    }
    const saveCache = (url) => {
        window.safeStorage.set(cacheKey, JSON.stringify({url: url, ts: Date.now()}));
        return url;
    };
    try {
        const cleanTitle = window.cleanTrackTitle(track.title);
        const query = encodeURIComponent(track.artist + " " + cleanTitle);
        const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
        if (!response.ok) throw new Error("iTunes API failed");
        const data = await response.json();
        if (data.results && data.results.length > 0) {
            let artworkUrl = data.results[0].artworkUrl100;
            if (artworkUrl) {
                artworkUrl = artworkUrl.replace("100x100bb", "600x600bb");
                return saveCache(artworkUrl);
            }
        }
    } catch (e) {
        console.warn("Cover fetch error for", track.title, e);
    }
    return saveCache(ytFallback);
};
let _lazyCoverObserver = null;
window.loadLazyCovers = function() {
    if (!_lazyCoverObserver) {
        _lazyCoverObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    observer.unobserve(img);
                    img.classList.add('loaded');
                    const videoId = img.getAttribute('data-vid');
                    const title = img.getAttribute('data-title');
                    const artist = img.getAttribute('data-artist');
                    const defaultThumb = img.getAttribute('data-thumb');
                    if (!videoId) return;
                    const track = { video_id: videoId, title: title, artist: artist, thumbnail: defaultThumb };
                    window.getCoverArt(track).then(coverUrl => {
                        if (coverUrl) {
                            img.src = coverUrl;
                        }
                    });
                }
            });
        }, { rootMargin: '200px' });
    }
    const images = document.querySelectorAll('img.lazy-cover:not(.observed)');
    images.forEach((img) => {
        img.classList.add('observed');
        _lazyCoverObserver.observe(img);
    });
};
window.extractDominantColor = function(imageElement, callback) {
    if (!imageElement.complete || imageElement.naturalWidth === 0) {
        imageElement.addEventListener('load', () => window.extractDominantColor(imageElement, callback), { once: true });
        return;
    }
    try {
        const canvas = document.createElement('canvas');
        const canvasContext = canvas.getContext('2d', { willReadFrequently: true });
        canvas.width = 50;
        canvas.height = 50;
        canvasContext.drawImage(imageElement, 0, 0, 50, 50);
        const data = canvasContext.getImageData(0, 0, 50, 50).data;
        let bestR = 0, bestG = 0, bestB = 0;
        let maxScore = -1;
        for (let i = 0; i < data.length; i += 16) {
            let r = data[i], g = data[i+1], b = data[i+2];
            let max = Math.max(r, g, b), min = Math.min(r, g, b);
            let l = (max + min) / 2;
            if (l < 20 || l > 240) continue;
            let s = 0;
            if (max !== min) {
                s = l > 127 ? (max - min) / (510 - max - min) : (max - min) / (max + min);
            }
            let score = s * 100;
            if (score > maxScore) {
                maxScore = score;
                bestR = r; bestG = g; bestB = b;
            }
        }
        if (maxScore === -1) {
            let r = 0, g = 0, b = 0, count = 0;
            for (let i = 0; i < data.length; i += 16) {
                r += data[i]; g += data[i+1]; b += data[i+2]; count++;
            }
            bestR = Math.floor(r / count);
            bestG = Math.floor(g / count);
            bestB = Math.floor(b / count);
        }
        console.log("Cover Color Extracted:", bestR, bestG, bestB);
        if (callback) callback({r: bestR, g: bestG, b: bestB});
    } catch (e) {
        console.warn("Color extraction failed:", e);
        if (callback) callback("var(--bg-elevated)");
    }
};

// --- services/auth.js ---
function applyRoleUI() {
    if (store.userRole === "portal") {
        dom.portalScreen.classList.add("portal-active");
        dom.appContainer.classList.add("portal-active");
        document.body.classList.remove("client-mode");
        dom.logoutBtn.style.display = "none";
    } else if (store.userRole === "client") {
        dom.portalScreen.classList.remove("portal-active");
        dom.appContainer.classList.remove("portal-active");
        document.body.classList.add("client-mode");
        switchTab("home");
        dom.logoutBtn.style.display = "flex";
    } else if (store.userRole === "admin") {
        dom.portalScreen.classList.remove("portal-active");
        dom.appContainer.classList.remove("portal-active");
        document.body.classList.remove("client-mode");
        dom.logoutBtn.style.display = "flex";
        switchTab("home");
        if (window.visualViewport) {
            const _app = document.getElementById("app");
            if (_app) {
                _app.style.height = window.visualViewport.height + "px";
            }
        }
    }
    renderHeader();
}
function login(user, pass) {
    if (!user || !pass) {
        dom.loginErrorMsg.textContent = "Isi username dan password!";
        return;
    }
    if (dom.adminSubmitBtn) {
        dom.adminSubmitBtn.disabled = true;
        dom.adminSubmitBtn.textContent = "Menghubungkan...";
    }
    dom.loginErrorMsg.textContent = "";
    store.adminUsername = user;
    if (dom.adminPassword) {
        dom.adminPassword.value = "";
    }
    if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        wsSend(WS_ACTIONS.AUTH, { username: user, password: pass });
    } else {
        dom.loginErrorMsg.textContent = "Koneksi server terputus. Silakan tunggu/refresh.";
        if (dom.adminSubmitBtn) {
            dom.adminSubmitBtn.disabled = false;
            dom.adminSubmitBtn.textContent = "Login Admin";
        }
    }
}
function logout() {
    if (typeof localAudio !== "undefined" && localAudio) {
        try {
            localAudio.pause();
            localAudio.src = "";
            localAudio.removeAttribute("src");
            localAudio.load();
        } catch (e) {
            console.warn("Failed to stop browser audio:", e);
        }
    }
    if (typeof _lastLoadedVideoId !== "undefined") {
        _lastLoadedVideoId = null;
    }
    if (store.userRole === "admin") {
        try {
            wsSend(WS_ACTIONS.STOP);
        } catch (e) {
            console.warn("Failed to send stop command:", e);
        }
    }
    store.userRole = "portal";
    store.adminUsername = "";
    safeStorage.remove("ytgui_user_role");
    safeStorage.remove("ytgui_admin_username");
    safeStorage.remove("ytgui_session_token");
    closeSettings();
    if (window.location.pathname !== "/") {
        setTimeout(() => {
            if (window.ws) {
                try {
                    window.ws.close();
                } catch (e) {}
            }
            window.location.href = "/";
        }, 150);
    } else {
        if (dom.portalClientBtn) {
            dom.portalClientBtn.style.display = "none";
        }
        applyRoleUI();
        if (window.ws) {
            try {
                window.ws.close();
            } catch (e) {}
        }
    }
}

// --- render/player.js ---
function renderPlayerBar() {
    syncPlayerStateAttr();
    const t = store.current_track;
    if (store.status === "LOADING") {
        dom.pbTrackInfo.innerHTML = '<span class="spinner" style="display:inline-block; margin-right:5px; vertical-align:-2px;"></span> Memuat... ' + escapeHtml(t ? t.title : "");
    } else if (t) {
        const title = cleanTrackTitle(t.title);
        const thumbUrl = (t.thumbnail || '').replace('hqdefault.jpg', 'mqdefault.jpg').replace('sddefault.jpg', 'mqdefault.jpg');
        const fallbackIcon = `<i class="ti ti-music" style="color:var(--text-3); font-size:20px;"></i>`;
        const thumbHtml = thumbUrl ? `<img src="${escapeHtml(thumbUrl)}" style="width:44px; height:44px; border-radius:6px; object-fit:cover; flex-shrink:0;">` : `<div style="width:44px; height:44px; border-radius:6px; background:rgba(255,255,255,0.1); flex-shrink:0; display:flex; align-items:center; justify-content:center;">${fallbackIcon}</div>`;
        dom.pbTrackInfo.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px; min-width:0;">
                ${thumbHtml}
                <div style="display:flex; flex-direction:column; justify-content:center; line-height:1.3; overflow:hidden; min-width:0;">
                    <span style="font-weight:600; font-size:14px; color:var(--text-1); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(title)}</span>
                    <span style="font-size:12px; color:var(--text-3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(t.artist)}</span>
                </div>
            </div>
        `;
    } else {
        dom.pbTrackInfo.innerHTML = "";
    }
    renderPlayBtn();
    if (store.playback_mode === "RADIO") {
        dom.pbModeBadge.textContent = "📻 radio";
        dom.pbModeBadge.className = "pb-mode-badge radio";
    } else {
        dom.pbModeBadge.textContent = "≡ queue";
        dom.pbModeBadge.className = "pb-mode-badge queue";
    }
    if (dom.pbVolLabel) dom.pbVolLabel.textContent = store.volume + "%";
    if (dom.volSlider && !window.isDraggingVol) dom.volSlider.value = store.volume;
    if (t && t.local_path) {
        dom.pbCacheBadge.textContent = "✓ tersimpan";
        dom.pbCacheBadge.className = "pb-badge-sm cached";
        dom.pbCacheBadge.style.display = "inline-block";
    } else if (t) {
        dom.pbCacheBadge.textContent = "☁ stream";
        dom.pbCacheBadge.className = "pb-badge-sm stream";
        dom.pbCacheBadge.style.display = "inline-block";
    } else {
        dom.pbCacheBadge.textContent = "";
        dom.pbCacheBadge.style.display = "none";
    }
    dom.pbSbBadge.textContent = store.sponsorblock_active ? "SB: ON" : "";
    dom.pbSbBadge.style.display = store.sponsorblock_active ? "inline-block" : "none";
    if (store.download_progress != null) {
        dom.pbDlBadge.textContent = "⬇ " + Math.round(store.download_progress * 100) + "%";
        dom.pbDlBadge.style.display = "inline-block";
    } else {
        dom.pbDlBadge.textContent = "";
        dom.pbDlBadge.style.display = "none";
    }
}
function renderPlayBtn() {
    if (store.status === "PLAYING") {
        dom.btnPlay.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M14,19H18V5H14M6,19H10V5H6V19Z"></path></svg>';
    } else {
        dom.btnPlay.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M8,5.14V19.14L19,12.14L8,5.14Z"></path></svg>';
    }
}
let _rafProgressPending = false;
function renderProgress() {
    if (_rafProgressPending) return;
    _rafProgressPending = true;
    requestAnimationFrame(() => {
        _rafProgressPending = false;
        _renderProgressCore();
    });
}
function _renderProgressCore() {
    if (window.isDraggingPb) return;
    const dur = store.current_track ? store.current_track.duration : 0;
    const pos = store.position || 0;
    const pct = dur > 0 ? Math.min(100, (pos / dur) * 100) : 0;
    dom.pbProgressFill.style.width = pct + "%";
    const thumb = dom.pbProgressTrack.querySelector('.pb-thumb');
    if(thumb) thumb.style.left = pct + "%";
    dom.pbTimePos.textContent = formatTime(pos);
    dom.pbTimeDur.textContent = formatTime(dur);
    const playerBar = document.getElementById("player-bar");
    if(playerBar) playerBar.style.setProperty("--mini-progress", pct + "%");
}

// --- render/now-playing.js ---
function renderNowPlaying() {
    const t = store.current_track;
    if (dom.vinylCover) {
        if (t && t.video_id) {
            dom.vinylCover.style.display = "none";
            if (dom.vinylIcon) dom.vinylIcon.style.display = "block";
            window.getCoverArt(t).then(url => {
                if (url && store.current_track && store.current_track.video_id === t.video_id) {
                    dom.vinylCover.src = url;
                    dom.vinylCover.style.display = "block";
                    if (dom.vinylIcon) dom.vinylIcon.style.display = "none";
                    if (typeof window.extractDominantColor === "function" && dom.tabHome) {
                        window.extractDominantColor(dom.vinylCover, (color) => {
                            if (color && color.r !== undefined) {
                                dom.tabHome.style.setProperty("--color-r", color.r);
                                dom.tabHome.style.setProperty("--color-g", color.g);
                                dom.tabHome.style.setProperty("--color-b", color.b);
                            }
                        });
                    }
                }
            });
        } else {
            dom.vinylCover.src = "";
            dom.vinylCover.style.display = "none";
            if (dom.vinylIcon) dom.vinylIcon.style.display = "block";
        }
    }
    if (dom.npThumbIcon && dom.npEqAnim) {
        if (store.status === "PLAYING") {
            dom.npThumbIcon.style.display = "none";
            dom.npEqAnim.style.display = "flex";
            if (dom.vinylRecord) {
                const isBrowser = store.userRole === "client" || store.audio_output === "browser";
                dom.vinylRecord.classList.add(isBrowser ? "visualizer-active" : "playing");
                dom.vinylRecord.classList.remove(isBrowser ? "playing" : "visualizer-active");
            }
        } else {
            dom.npThumbIcon.style.display = "block";
            dom.npEqAnim.style.display = "none";
            if (dom.vinylRecord) {
                dom.vinylRecord.classList.remove("playing");
                dom.vinylRecord.classList.remove("visualizer-active");
            }
        }
    }
    if (dom.homeEqualizer) {
        const hasLyrics = store.lyrics_lines && store.lyrics_lines.length > 0;
        dom.homeEqualizer.style.display = (!hasLyrics && store.status === "PLAYING") ? "flex" : "none";
    }
    if (dom.vinylRecord) {
        if (store.status === "PLAYING") {
            dom.vinylRecord.classList.add("playing");
        } else {
            dom.vinylRecord.classList.remove("playing");
        }
    }
    syncPlayerStateAttr();
    if (store.status === "LOADING") {
        dom.npTitle.innerHTML = '<span class="spinner" style="display:inline-block; margin-right:8px; vertical-align:-3px; width:20px; height:20px;"></span> ⏳ Memuat...';
        dom.npArtist.textContent = (t && t.title) ? t.title : "";
    } else if (t && t.title) {
        const cleanedTitle = cleanTrackTitle(t.title);
        dom.npTitle.textContent = cleanedTitle.toLowerCase().replace(/(?:^|\s|-)\S/g, function(a) { return a.toUpperCase(); });
        dom.npArtist.textContent = t.artist || "";
    } else {
        dom.npTitle.textContent = "Belum ada lagu yang diputar";
        dom.npArtist.textContent = "Cari lagu untuk memulai";
    }
    if (dom.npDurMeta && t) {
        dom.npDurMeta.textContent = formatTime(t.duration);
    } else if (dom.npDurMeta) {
        dom.npDurMeta.textContent = '';
    }
    if (dom.btnFavorite) {
        if (t && t.is_favorite) {
            dom.btnFavorite.classList.add("active");
        } else {
            dom.btnFavorite.classList.remove("active");
        }
    }
}
function syncPlayerStateAttr() {
    const t = store.current_track;
    if (!t || (!t.video_id && store.status !== "LOADING")) {
        document.body.setAttribute("data-player-state", "IDLE");
    } else {
        document.body.setAttribute("data-player-state", store.status);
    }
}

// --- render/queue.js ---
function renderQueue() {
    if (window.isDraggingQueue) return;
    document.body.dataset.queueEmpty = (store.queue.length === 0) ? "true" : "false";
    const isRadio = store.playback_mode === "RADIO";
    renderList(dom.queueList, store.queue, false, store.playback_mode === "QUEUE");
    if (dom.radioQueueList) {
        renderList(dom.radioQueueList, store.radio_queue, true, isRadio);
    }
    const modeStr = isRadio
        ? '<span style="color:var(--fm-green)">RADIO</span>'
        : '<span style="color:var(--fm-text-5)">QUEUE</span>';
    if (dom.queueFooter) {
        dom.queueFooter.innerHTML = "Mode: " + modeStr;
    }
}
function renderList(container, items, isRadioList, isCurrentActiveMode) {
    if (!container) return;
    const allItems = [];
    if (isCurrentActiveMode && store.current_track) {
        allItems.push({ track: store.current_track, index: -1, isCurrent: true });
    }
    items.forEach((track, i) => allItems.push({ track, index: i, isCurrent: false }));
    if (allItems.length === 0) {
        container.innerHTML = '<div class="queue-empty">' + (isRadioList ? "Tekan 'Acak Ulang' untuk memulai radio" : "Cari lagu atau putar dari Discover") + '</div>';
    } else {
        const existing = Array.from(container.children);
        if (existing.length === 1 && existing[0].classList.contains('queue-empty')) {
            existing[0].remove();
            existing.shift();
        }
        allItems.forEach((item, i) => {
            let el = existing[i];
            if (!el) {
                el = createQueueItemTemplate(isRadioList);
                container.appendChild(el);
            }
            updateQueueItem(el, item.track, item.index, item.isCurrent, isRadioList);
        });
        while (container.children.length > allItems.length) {
            container.removeChild(container.lastChild);
        }
        if (isRadioList && typeof window.loadLazyCovers === "function") {
            window.loadLazyCovers();
        }
    }
}
function createQueueItemTemplate(isRadio) {
    const div = document.createElement("div");
    if (isRadio) {
        div.className = "radio-queue-item";
        div.innerHTML = `
            <div class="radio-queue-thumb">
                <img class="lazy-cover" src="" alt="">
                <div class="thumb-eq-overlay">
                    <div class="eq-anim-icon">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
            <div class="radio-queue-info">
                <div class="radio-queue-title"></div>
                <div class="radio-queue-artist"></div>
            </div>
        `;
    } else {
        div.className = "queue-item";
        div.innerHTML = `
            <span class="qi-index"></span>
            <div class="qi-info">
                <div class="qi-title"></div>
                <div class="qi-dur"></div>
            </div>
            <button class="qi-remove">✕</button>
        `;
    }
    return div;
}
function updateQueueItem(div, track, index, isCurrent, isRadio) {
    if (isRadio) {
        div.className = "radio-queue-item" + (isCurrent ? " current" : "") + (isCurrent && store.status === "PLAYING" ? " playing" : "");
        div.dataset.vid = track.video_id || '';
        const titleEl = div.querySelector(".radio-queue-title");
        const artistEl = div.querySelector(".radio-queue-artist");
        const title = typeof cleanTrackTitle === "function" ? escapeHtml(cleanTrackTitle(track.title)) : escapeHtml(track.title);
        if (titleEl) titleEl.textContent = title;
        if (artistEl) artistEl.textContent = (track.artist || '') + " · " + formatTime(track.duration);
        const img = div.querySelector(".lazy-cover");
        if (img) {
            if (img.dataset.vid !== (track.video_id || '')) {
                img.dataset.vid = track.video_id || '';
                img.dataset.title = track.title || '';
                img.dataset.artist = track.artist || '';
                img.dataset.thumb = track.thumbnail || '';
                img.src = '';
                img.classList.remove('loaded');
            }
        }
    } else {
        div.className = "queue-item" + (isCurrent ? " current" : "");
        if (!isCurrent) {
            div.dataset.index = index;
        } else {
            div.removeAttribute("data-index");
        }
        if (isCurrent) {
            if (store.status === "PLAYING") {
                div.querySelector(".qi-index").innerHTML = `<div class="eq-anim-icon" style="height:12px; width:14px; gap:2px;"><span style="width:3px; background: currentColor;"></span><span style="width:3px; background: currentColor;"></span><span style="width:3px; background: currentColor;"></span></div>`;
            } else {
                div.querySelector(".qi-index").textContent = "▶";
            }
        } else {
            div.querySelector(".qi-index").textContent = index + 1;
        }
        div.querySelector(".qi-title").textContent = track.title;
        div.querySelector(".qi-dur").textContent = track.artist + " · " + formatTime(track.duration);
        const rmBtn = div.querySelector(".qi-remove");
        if (isCurrent) {
            rmBtn.style.display = "none";
        } else {
            rmBtn.style.display = "block";
            rmBtn.dataset.index = index;
        }
    }
}

// --- render/discover.js ---
const _hashtagColors = {};
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    const hue = Math.floor(Math.random() * 360);
    const saturation = 60 + Math.floor(Math.random() * 30);
    const lightness = 50 + Math.floor(Math.random() * 20);
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    _hashtagColors[hashtag] = color;
    return color;
}
function setLazyCoverData(img, track) {
    if (img.dataset.vid !== track.video_id) {
        img.dataset.vid = track.video_id || '';
        img.dataset.title = track.title || '';
        img.dataset.artist = track.artist || '';
        img.dataset.thumb = track.thumbnail || '';
        img.src = '';
        img.classList.remove('loaded');
    }
}
function renderDiscoverList(container, items, emptyHtml, createTemplate, updateItem) {
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = emptyHtml;
        return;
    }
    const existing = Array.from(container.children);
    if (existing.length > 0 && (existing[0].classList.contains('skeleton-box') || existing[0].querySelector('.skeleton-box'))) {
        container.innerHTML = '';
        existing.length = 0;
    } else if (existing.length === 1 && existing[0].classList.contains('discover-empty')) {
        existing[0].remove();
        existing.shift();
    }
    items.forEach((item, i) => {
        let el = existing[i];
        if (!el) {
            el = createTemplate();
            container.appendChild(el);
        }
        updateItem(el, item, i);
    });
    while (container.children.length > items.length) {
        container.removeChild(container.lastChild);
    }
}
function renderDiscoverTab() {
    if (dom.discFavorites && store.discover_favorites) {
        renderDiscoverList(
            dom.discFavorites,
            store.discover_favorites,
            '<div class="discover-empty"><i class="ti ti-heart-broken" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Belum ada data favorit</div>',
            () => {
                const div = document.createElement("div");
                div.className = "fav-card";
                div.innerHTML = `
                    <div class="fav-num"></div>
                    <div class="fav-thumb">
                        <img class="lazy-cover" src="" alt="">
                    </div>
                    <div class="fav-info">
                        <div class="fav-title"></div>
                        <div class="fav-cnt"></div>
                    </div>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                const playCnt = track.play_count > 0 ? ` · ${track.play_count}×` : '';
                el.dataset.vid = track.video_id || '';
                el.querySelector('.fav-num').textContent = i + 1;
                setLazyCoverData(el.querySelector('.lazy-cover'), track);
                el.querySelector('.fav-title').textContent = title;
                el.querySelector('.fav-cnt').textContent = (track.artist || '') + playCnt;
            }
        );
    }
    if (dom.discRecent && store.discover_recent) {
        renderDiscoverList(
            dom.discRecent,
            store.discover_recent,
            '<div class="discover-empty"><i class="ti ti-history" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Belum ada riwayat</div>',
            () => {
                const div = document.createElement("div");
                div.className = "sr-item";
                div.innerHTML = `
                    <div class="sr-thumb">
                        <img class="lazy-cover" src="" alt="">
                        <div class="thumb-eq-overlay">
                            <div class="eq-anim-icon">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                    <div class="sr-info">
                        <div class="sr-title"></div>
                        <div class="sr-meta"></div>
                    </div>
                    <div class="sr-duration"></div>
                    <button class="sr-more-btn" aria-label="More">
                        <i class="ti ti-dots-vertical"></i>
                    </button>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                let artistName = track.artist || "";
                if (artistName.length > 25) {
                    artistName = artistName.substring(0, 22) + "...";
                }
                el.dataset.vid = track.video_id || '';
                el.dataset.trackStr = JSON.stringify(track).replace(/'/g, "&apos;");
                const thumbDiv = el.querySelector('.sr-thumb');
                if (track.local_path && !thumbDiv.querySelector('.disc-tag')) {
                    const tag = document.createElement("span");
                    tag.className = "disc-tag";
                    tag.textContent = "cache";
                    thumbDiv.appendChild(tag);
                } else if (!track.local_path && thumbDiv.querySelector('.disc-tag')) {
                    thumbDiv.querySelector('.disc-tag').remove();
                }
                const img = el.querySelector('.lazy-cover');
                if (img.dataset.vid !== track.video_id) {
                    img.dataset.vid = track.video_id || '';
                    img.dataset.title = track.title || '';
                    img.dataset.artist = track.artist || '';
                    img.dataset.thumb = track.thumbnail || '';
                    img.src = '';
                    img.classList.remove('loaded');
                }
                el.querySelector('.sr-title').textContent = title;
                el.querySelector('.sr-meta').textContent = artistName;
                el.querySelector('.sr-duration').textContent = formatTime(track.duration);
            }
        );
    }
    if (dom.discCached && store.discover_cached) {
        renderDiscoverList(
            dom.discCached,
            store.discover_cached,
            '<div class="discover-empty"><i class="ti ti-box-off" style="font-size:32px; opacity:0.6; margin-bottom:12px; display:block;"></i>Tidak ada file tersimpan</div>',
            () => {
                const div = document.createElement("div");
                div.className = "sr-item";
                div.innerHTML = `
                    <div class="sr-thumb">
                        <img class="lazy-cover" src="" alt="">
                        <div class="thumb-eq-overlay">
                            <div class="eq-anim-icon">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                    <div class="sr-info">
                        <div class="sr-title"></div>
                        <div class="sr-meta"></div>
                    </div>
                    <div class="sr-duration"></div>
                    <button class="sr-more-btn" aria-label="More">
                        <i class="ti ti-dots-vertical"></i>
                    </button>
                `;
                return div;
            },
            (el, track, i) => {
                const title = cleanTrackTitle(track.title);
                let artistName = track.artist || "";
                if (artistName.length > 25) {
                    artistName = artistName.substring(0, 22) + "...";
                }
                el.dataset.vid = track.video_id || '';
                el.dataset.trackStr = JSON.stringify(track).replace(/'/g, "&apos;");
                const img = el.querySelector('.lazy-cover');
                if (img.dataset.vid !== track.video_id) {
                    img.dataset.vid = track.video_id || '';
                    img.dataset.title = track.title || '';
                    img.dataset.artist = track.artist || '';
                    img.dataset.thumb = track.thumbnail || '';
                    img.src = '';
                    img.classList.remove('loaded');
                }
                el.querySelector('.sr-title').textContent = title;
                el.querySelector('.sr-meta').textContent = artistName;
                el.querySelector('.sr-duration').textContent = formatTime(track.duration);
            }
        );
    }
    if (dom.discArtists && store.discover_featured_artists) {
        renderDiscoverList(
            dom.discArtists,
            store.discover_featured_artists,
            '',
            () => {
                const div = document.createElement("div");
                div.className = "hashtag-pill";
                return div;
            },
            (el, artist, i) => {
                const name = cleanTrackTitle(artist.nama);
                const hashtag = "#" + name.replace(/\s+/g, '');
                const color = getHashtagColor(hashtag);
                const clicks = artist.click_count || 0;
                const bonusSize = Math.min(clicks * 2, 14);
                const fontSize = 14 + bonusSize;
                el.dataset.artist = artist.nama;
                el.style.color = color;
                el.style.setProperty('--base-size', `${fontSize}px`);
                el.textContent = hashtag;
            }
        );
        dom.discArtists.onclick = (e) => {
            const pill = e.target.closest('.hashtag-pill');
            if (pill && pill.dataset.artist) {
                if (store.userRole !== 'admin') {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                showLogToast(`Memutar playlist dari ${pill.dataset.artist}...`);
                wsSend(WS_ACTIONS.ENQUEUE_ARTIST_SONGS, { artist: pill.dataset.artist });
                switchTab('home');
            }
        };
    }
    if (dom.discGenres && store.discover_featured_genres) {
        renderDiscoverList(
            dom.discGenres,
            store.discover_featured_genres,
            '',
            () => {
                const div = document.createElement("div");
                div.className = "hashtag-pill";
                return div;
            },
            (el, genre, i) => {
                const name = cleanTrackTitle(genre.nama_genre);
                const hashtag = "#" + name.replace(/\s+/g, '');
                const color = getHashtagColor(hashtag);
                const clicks = genre.click_count || 0;
                const bonusSize = Math.min(clicks * 2, 14);
                const fontSize = 14 + bonusSize;
                el.dataset.genre = genre.nama_genre;
                el.style.color = color;
                el.style.setProperty('--base-size', `${fontSize}px`);
                el.textContent = hashtag;
            }
        );
        dom.discGenres.onclick = (e) => {
            const pill = e.target.closest('.hashtag-pill');
            if (pill && pill.dataset.genre) {
                if (store.userRole !== 'admin') {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                showLogToast(`Memutar playlist dari genre ${pill.dataset.genre}...`);
                wsSend(WS_ACTIONS.ENQUEUE_GENRE_SONGS, { genre: pill.dataset.genre });
                switchTab('home');
            }
        };
    }
    window.loadLazyCovers();
    updateDiscoverPlayingState();
}
function updateDiscoverPlayingState() {
    const currentId = store.current_track && store.current_track.video_id;
    const isPlaying = store.status === "PLAYING";
    const homeRecentContainer = document.getElementById('home-recent-list');
    if (homeRecentContainer) {
        homeRecentContainer.querySelectorAll(".home-recent-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }
    if (dom.discRecent) {
        dom.discRecent.querySelectorAll(".sr-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }
    if (dom.discCached) {
        dom.discCached.querySelectorAll(".sr-item").forEach(item => {
            const isCurrent = currentId && item.dataset.vid === currentId;
            item.classList.toggle("current", !!isCurrent);
            item.classList.toggle("playing", !!(isCurrent && isPlaying));
        });
    }
}
function renderRadio() {
    const isRadio = store.playback_mode === 'RADIO';
    if (dom.radioToggleBtn) {
        if (isRadio) {
            dom.radioToggleBtn.classList.add("on");
            dom.radioToggleBtn.classList.remove("off");
            dom.radioToggleBtn.dataset.on = "true";
        } else {
            dom.radioToggleBtn.classList.add("off");
            dom.radioToggleBtn.classList.remove("on");
            dom.radioToggleBtn.dataset.on = "false";
        }
    }
    if (dom.rtSub) {
        if (isRadio) {
            if (store.status === "LOADING") {
                dom.rtSub.textContent = "Mencari stasiun...";
            } else {
                dom.rtSub.textContent = "24/7 Nonstop Music";
            }
        } else {
            dom.rtSub.textContent = "Aktifkan untuk putar otomatis";
        }
    }
}
function renderRecentRow() {
    const container = document.getElementById('home-recent-list');
    if (!container) return;
    const items = (store.discover_recent || []).slice(0, 5);
    renderDiscoverList(
        container,
        items,
        '<div style="padding:24px 20px; color:var(--text-3); font-size:14px; text-align:center;">Belum ada riwayat putar</div>',
        () => {
            const div = document.createElement("div");
            div.className = "home-recent-item";
            div.innerHTML = `
                <div class="home-recent-thumb">
                    <img class="lazy-cover" src="" alt="">
                </div>
                <div class="home-recent-info">
                    <div class="home-recent-title"></div>
                    <div class="home-recent-artist"></div>
                </div>
                <button class="home-recent-more" aria-label="More">
                    <i class="ti ti-dots-vertical"></i>
                </button>
            `;
            div.addEventListener('click', (e) => {
                if (e.target.closest('.home-recent-more')) return;
                if (store.userRole !== 'admin') return;
                const vid = div.dataset.vid;
                if (!vid) return;
                const track = (store.discover_recent || []).find(t => t.video_id === vid);
                if (track) window.wsSend(WS_ACTIONS.PLAY_TRACK, track);
            });
            div.querySelector('.home-recent-more').addEventListener('click', (e) => {
                e.stopPropagation();
                try {
                    const trackStr = div.dataset.track;
                    if (trackStr) {
                        const track = JSON.parse(trackStr);
                        window.showActionModal(track);
                    }
                } catch(_) {}
            });
            return div;
        },
        (el, track, i) => {
            const title = typeof cleanTrackTitle === 'function' ? cleanTrackTitle(track.title) : track.title;
            const currentId = store.current_track && store.current_track.video_id;
            const isCurrent = track.video_id && track.video_id === currentId;
            el.dataset.vid = track.video_id || '';
            el.dataset.track = JSON.stringify(track);
            if (isCurrent) el.classList.add('current');
            else el.classList.remove('current');
            const img = el.querySelector('.lazy-cover');
            if (img.dataset.vid !== track.video_id) {
                img.dataset.vid = track.video_id || '';
                img.dataset.title = track.title || '';
                img.dataset.artist = track.artist || '';
                img.dataset.thumb = track.thumbnail || '';
                img.src = '';
                img.classList.remove('loaded');
            }
            el.querySelector('.home-recent-title').textContent = title;
            el.querySelector('.home-recent-artist').textContent = track.artist || '';
        }
    );
    window.loadLazyCovers();
}

// --- render/favorites.js ---

// --- render/lyrics.js ---
function renderLyrics() {
    renderSheetLyrics();
    renderHomeLyrics();
}
function renderSheetLyrics() {
    if (!dom.lyricsSheet || !dom.lyricsSheet.classList.contains("open")) return;
    if (!dom.lyricsContent._scrollBound) {
        dom.lyricsContent._scrollBound = true;
        let scrollTimeout;
        const setScrolling = () => {
            window.isScrollingLyrics = true;
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => window.isScrollingLyrics = false, 3000);
        };
        dom.lyricsContent.addEventListener("wheel", setScrolling, {passive: true});
        dom.lyricsContent.addEventListener("touchmove", setScrolling, {passive: true});
    }
    const lines = store.lyrics_lines;
    const idx = store.lyrics_index;
    if (!lines || lines.length === 0) {
        dom.lyricsContent.innerHTML = '<div style="color:var(--fm-text-5)">Tidak ada lirik tersedia</div>';
        return;
    }
    const start = Math.max(0, idx - 5);
    const end = Math.min(lines.length, idx + 6);
    let html = "";
    for (let i = start; i < end; i++) {
        const text = escapeHtml(lines[i]);
        if (i === idx) {
            html += '<div class="lyric-line active">' + text + '</div>';
        } else if (i < idx) {
            html += '<div class="lyric-line past">' + text + "</div>";
        } else {
            html += '<div class="lyric-line future">' + text + "</div>";
        }
    }
    dom.lyricsContent.innerHTML = html;
    const activeLine = dom.lyricsContent.querySelector(".lyric-line.active");
    if (activeLine && !window.isScrollingLyrics) {
        activeLine.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}
function renderHomeLyrics() {
    if (!dom.lyricsCurrent || !dom.lyricsPrev || !dom.lyricsNext) return;
    if (!store.lyrics_lines || store.lyrics_lines.length === 0) {
        document.body.setAttribute("data-has-lyrics", "false");
        if (dom.lyricsTextContainer) dom.lyricsTextContainer.style.display = "none";
        return;
    }
    document.body.setAttribute("data-has-lyrics", "true");
    if (dom.lyricsTextContainer) dom.lyricsTextContainer.style.display = "flex";
    dom.lyricsCurrent.className = "lyrics-line current lyric-pop";
    if (dom.lyricsCurrent._popTimeout) clearTimeout(dom.lyricsCurrent._popTimeout);
    dom.lyricsCurrent._popTimeout = setTimeout(() => {
        if (dom.lyricsCurrent) {
            dom.lyricsCurrent.className = "lyrics-line current";
        }
    }, 300);
    const idx = store.lyrics_index || 0;
    const lines = store.lyrics_lines;
    dom.lyricsPrev.innerHTML = idx > 0 ? escapeHtml(lines[idx - 1]) : "&nbsp;";
    dom.lyricsCurrent.innerHTML = escapeHtml(lines[idx] || "&nbsp;");
    dom.lyricsNext.innerHTML = idx < lines.length - 1 ? escapeHtml(lines[idx + 1]) : "&nbsp;";
}
function updateOffsetDisplay() {
    const el = document.getElementById("sync-val");
    if (!el) return;
    const val = store.lyrics_offset || 0;
    const sign = val >= 0 ? '+' : '';
    el.textContent = sign + val.toFixed(1) + 's';
}

// --- render/search.js ---
function buildSrThumbHtml(track) {
    return `<img class="lazy-cover" data-vid="${escapeHtml(track.video_id || '')}" data-title="${escapeHtml(track.title || '')}" data-artist="${escapeHtml(track.artist || '')}" data-thumb="${escapeHtml(track.thumbnail || '')}" src="" alt=""><div class="thumb-eq-overlay"><div class="eq-anim-icon"><span></span><span></span><span></span></div></div>`;
}
function renderSearchResults(results) {
    store.search_results = results || [];
    dom.searchResults.innerHTML = "";
    if (!results || results.length === 0) {
        dom.searchMsg.textContent = "Tidak ditemukan hasil.";
        dom.searchMsg.style.display = "block";
        dom.searchResults.style.display = "none";
        return;
    }
    dom.searchMsg.style.display = "none";
    dom.searchResults.style.display = "flex";
    results.forEach((track) => {
        const item = document.createElement("div");
        item.className = "sr-item";
        item.dataset.videoId = track.video_id;
        item.dataset.searchTrackStr = JSON.stringify(track);
        const thumb = document.createElement("div");
        thumb.className = "sr-thumb";
        thumb.innerHTML = buildSrThumbHtml(track);
        const info = document.createElement("div");
        info.className = "sr-info";
        const title = document.createElement("div");
        title.className = "sr-title";
        title.textContent = cleanTrackTitle(track.title);
        const meta = document.createElement("div");
        meta.className = "sr-meta";
        let artistName = track.artist || "";
        if (artistName.length > 25) {
            artistName = artistName.substring(0, 22) + "...";
        }
        meta.textContent = artistName;
        info.appendChild(title);
        info.appendChild(meta);
        const duration = document.createElement("div");
        duration.className = "sr-duration";
        duration.textContent = formatTime(track.duration);
        const moreBtn = document.createElement("button");
        moreBtn.className = "sr-more-btn";
        moreBtn.innerHTML = '<i class="ti ti-dots-vertical"></i>';
        moreBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            showActionModal(track);
        });
        item.appendChild(thumb);
        item.appendChild(info);
        item.appendChild(duration);
        item.appendChild(moreBtn);
        dom.searchResults.appendChild(item);
    });
    updateSearchPlayingState();
}
function updateSearchPlayingState() {
    if (!dom.searchResults) return;
    const currentId = store.current_track && store.current_track.video_id;
    const isPlaying = store.status === "PLAYING";
    dom.searchResults.querySelectorAll(".sr-item").forEach((item) => {
        const isCurrent = currentId && item.dataset.videoId === currentId;
        item.classList.toggle("current", !!isCurrent);
        item.classList.toggle("playing", !!(isCurrent && isPlaying));
    });
    window.loadLazyCovers();
}
function playSearchTrack(track) {
    if (store.userRole !== "admin" || !track) return;
    wsSend(WS_ACTIONS.PLAY_TRACK, track);
}
function showActionModal(track) {
    window.pendingTrack = track;
    dom.actionTitle.textContent = track.title;
    if (dom.actionDelete) {
        dom.actionDelete.style.display = (track.local_path || track.is_cached) ? 'block' : 'none';
    }
    if (dom.actionSheet) dom.actionSheet.classList.add("open");
    if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
}
function hideActionModal() {
    if (dom.actionSheet) dom.actionSheet.classList.remove("open");
    if (dom.mainOverlay) dom.mainOverlay.classList.remove("open");
    window.pendingTrack = null;
}

// --- events/player-events.js ---
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

// --- events/queue-events.js ---
let _dragSrcIndex = null;
let _dragEl = null;
window.isDraggingQueue = false;
function initQueueDragDrop() {
    const list = dom.queueList;
    if (!list) return;
    list.addEventListener('pointerdown', _onDragStart, { passive: false });
    document.addEventListener('pointermove', _onDragMove, { passive: false });
    document.addEventListener('pointerup', _onDragEnd);
    document.addEventListener('pointercancel', _onDragCancel);
}
function _onDragStart(e) {
    if (store.userRole !== 'admin') return;
    const handle = e.target.closest('.qi-drag');
    if (!handle) return;
    const item = handle.closest('.queue-item');
    if (!item || !item.hasAttribute('data-index')) return;
    e.preventDefault();
    _dragSrcIndex = parseInt(item.dataset.index);
    _dragEl = item;
    window.isDraggingQueue = true;
    item.classList.add('dragging');
    item.setPointerCapture(e.pointerId);
}
function _onDragMove(e) {
    if (_dragSrcIndex === null || !_dragEl) return;
    e.preventDefault();
    document.querySelectorAll('.queue-item.drag-over').forEach(el => el.classList.remove('drag-over'));
    const target = document.elementFromPoint(e.clientX, e.clientY);
    if (target) {
        const over = target.closest('.queue-item[data-index]');
        if (over && over !== _dragEl) {
            over.classList.add('drag-over');
        }
    }
}
function _onDragEnd(e) {
    if (_dragSrcIndex === null) return;
    const target = document.elementFromPoint(e.clientX, e.clientY);
    if (target) {
        const over = target.closest('.queue-item[data-index]');
        if (over && over !== _dragEl) {
            const toIndex = parseInt(over.dataset.index);
            if (toIndex !== _dragSrcIndex) {
                wsSend(WS_ACTIONS.QUEUE_REORDER, { from_index: _dragSrcIndex, to_index: toIndex });
            }
        }
    }
    _cleanupDrag();
}
function _onDragCancel() {
    _cleanupDrag();
}
function _cleanupDrag() {
    if (_dragEl) _dragEl.classList.remove('dragging');
    document.querySelectorAll('.queue-item.drag-over').forEach(el => el.classList.remove('drag-over'));
    _dragSrcIndex = null;
    _dragEl = null;
    window.isDraggingQueue = false;
}
function initQueueEvents() {
    if (dom.queueList) {
        dom.queueList.addEventListener("click", (e) => {
            if (store.userRole !== "admin") return;
            const rmBtn = e.target.closest(".qi-remove");
            if (rmBtn) {
                e.stopPropagation();
                wsSend(WS_ACTIONS.QUEUE_REMOVE, { index: parseInt(rmBtn.dataset.index) });
            }
        });
    }
}

// --- events/lyrics-events.js ---
const btnSyncMinus = document.getElementById("btn-sync-minus");
const btnSyncPlus = document.getElementById("btn-sync-plus");
const lyricsWrap = document.getElementById("lyrics-wrap");
const lyricSyncCtrls = document.getElementById("lyric-sync-ctrls");
let lyricSyncHideTimeout = null;
function showLyricSync() {
    if (lyricSyncCtrls) {
        lyricSyncCtrls.classList.add("active");
        if (lyricSyncHideTimeout) clearTimeout(lyricSyncHideTimeout);
        lyricSyncHideTimeout = setTimeout(() => {
            lyricSyncCtrls.classList.remove("active");
        }, 3000);
    }
}
function initLyricsEvents() {
    if (dom.btnLyrics) {
        dom.btnLyrics.addEventListener("click", () => {
            if (dom.lyricsSheet) dom.lyricsSheet.classList.add("open");
            if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
            renderLyrics();
        });
    }
    if (dom.lyricsCloseBtn) {
        dom.lyricsCloseBtn.addEventListener("click", () => {
            if (dom.lyricsSheet) dom.lyricsSheet.classList.remove("open");
            closeMainOverlay();
        });
    }
    if (dom.lyricOffsetMinus) {
        dom.lyricOffsetMinus.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            store.lyrics_offset = (store.lyrics_offset || 0) - 0.5;
            updateOffsetDisplay();
            syncLocalLyrics();
            wsSend(WS_ACTIONS.LYRICS_OFFSET, { offset: store.lyrics_offset });
        });
    }
    if (dom.lyricOffsetPlus) {
        dom.lyricOffsetPlus.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            store.lyrics_offset = (store.lyrics_offset || 0) + 0.5;
            updateOffsetDisplay();
            syncLocalLyrics();
            wsSend(WS_ACTIONS.LYRICS_OFFSET, { offset: store.lyrics_offset });
        });
    }
    if (lyricsWrap && lyricSyncCtrls) {
        lyricsWrap.addEventListener("mousemove", showLyricSync);
        lyricsWrap.addEventListener("touchstart", showLyricSync, { passive: true });
        lyricsWrap.addEventListener("click", showLyricSync);
        if (btnSyncMinus) {
            btnSyncMinus.addEventListener("click", (e) => {
                e.stopPropagation();
                if (store.userRole !== "admin") return;
                store.lyrics_offset = (store.lyrics_offset || 0) - 0.5;
                updateOffsetDisplay();
                syncLocalLyrics();
                wsSend(WS_ACTIONS.LYRICS_OFFSET, { offset: store.lyrics_offset });
                showLyricSync();
            });
        }
        if (btnSyncPlus) {
            btnSyncPlus.addEventListener("click", (e) => {
                e.stopPropagation();
                if (store.userRole !== "admin") return;
                store.lyrics_offset = (store.lyrics_offset || 0) + 0.5;
                updateOffsetDisplay();
                syncLocalLyrics();
                wsSend(WS_ACTIONS.LYRICS_OFFSET, { offset: store.lyrics_offset });
                showLyricSync();
            });
        }
    }
}

// --- events/settings-events.js ---
function openSettings() {
    if (dom.settingsSheet) dom.settingsSheet.classList.add("open");
    if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
    renderSettingsSheet();
}
function closeSettings() {
    if (dom.settingsSheet) dom.settingsSheet.classList.remove("open");
    closeMainOverlay();
}
function renderSettingsSheet() {
    if (!dom.settingsSheet || !dom.settingsSheet.classList.contains("open")) return;
    if (dom.sbToggle) dom.sbToggle.dataset.on = store.sponsorblock_active ? "true" : "false";
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
            wsSend(WS_ACTIONS.SET_SPONSORBLOCK, { enabled: newVal });
        });
    }
    if (dom.ssOutBtn) {
        dom.ssOutBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            const newOutput = store.audio_output === "browser" ? "device" : "browser";
            if (newOutput === "browser" && typeof unlockBrowserAudio === "function") unlockBrowserAudio();
            wsSend(WS_ACTIONS.SET_OUTPUT, { output: newOutput });
            closeSettings();
        });
    }
    if (dom.ssStopBtn) {
        dom.ssStopBtn.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            wsSend(WS_ACTIONS.STOP);
            closeSettings();
        });
    }
    if (dom.ssHistoryBtn) {
        dom.ssHistoryBtn.addEventListener('click', () => {
            closeSettings();
            switchTab('discover');
            wsSend(WS_ACTIONS.DISCOVER, {});
            setTimeout(() => {
                if (dom.discRecent) {
                    dom.discRecent.scrollIntoView({ behavior: 'smooth' });
                }
            }, 300);
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

// --- events/index.js ---
function initEvents() {
    document.querySelectorAll(".mood-card").forEach(card => {
        card.addEventListener("click", () => {
            const mood = card.getAttribute("data-mood");
            if (mood && store.userRole === "admin") {
                switchTab("search");
                if (dom.searchInput) {
                    dom.searchInput.value = mood + " mix";
                    dom.searchInput.dispatchEvent(new Event("input"));
                }
            }
        });
    });
    if (dom.portalClientBtn) {
        dom.portalClientBtn.addEventListener("click", () => {
            store.userRole = "client";
            if (window.safeStorage) {
                window.safeStorage.set("ytgui_user_role", "client");
            } else {
                localStorage.setItem("ytgui_user_role", "client");
            }
            applyRoleUI();
            unlockBrowserAudio();
            syncBrowserAudio();
        });
    }
    if (dom.portalAdminBtn) {
        dom.portalAdminBtn.addEventListener("click", () => {
            if (dom.portalLoginForm) {
                dom.portalLoginForm.classList.toggle("hidden");
                if (!dom.portalLoginForm.classList.contains("hidden") && dom.adminUsername) {
                    dom.adminUsername.focus();
                }
            }
        });
    }
    if (dom.adminSubmitBtn) {
        dom.adminSubmitBtn.addEventListener("click", () => {
            const user = dom.adminUsername ? dom.adminUsername.value.trim() : "";
            const pass = dom.adminPassword ? dom.adminPassword.value : "";
            login(user, pass);
        });
    }
    if (dom.adminPassword) {
        dom.adminPassword.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
        });
    }
    if (dom.logoutBtn) {
        dom.logoutBtn.addEventListener("click", () => {
            logout();
        });
    }
    document.querySelectorAll(".nav-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            switchTab(btn.dataset.tab);
        });
    });
    initPlayerEvents();
    initQueueEvents();
    initQueueDragDrop();
    initLyricsEvents();
    initSettingsEvents();
}

// --- portal.js ---
function initPortal() {
    const role = window.safeStorage ? window.safeStorage.get("ytgui_user_role") : localStorage.getItem("ytgui_user_role");
    if (role && role !== "client") {
        store.userRole = role;
    } else {
        store.userRole = "portal";
    }
    applyRoleUI();
}

// --- platform/viewport.js ---
(function() {
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', () => {
            const app = document.getElementById('app');
            if (app) {
                app.style.height = window.visualViewport.height + 'px';
                document.documentElement.style.setProperty("--sat", "env(safe-area-inset-top)");
                document.documentElement.style.setProperty("--sab", "env(safe-area-inset-bottom)");
            }
        });
    }
})();

// --- platform/touch.js ---
(function() {
    let touchStartX = 0;
    let touchStartY = 0;
    document.addEventListener('touchstart', e => {
        unlockBrowserAudio();
        if (e.touches.length === 1) {
            touchStartX = e.touches[0].screenX;
            touchStartY = e.touches[0].screenY;
        }
    }, { passive: true });
    document.addEventListener('touchend', e => {
        if (e.target.closest(
            "#radio-toggle-btn, button, a, input, select, textarea, [role=\"button\"], .mood-row, .disc-row2, [style*=\"overflow-x\"]"
        )) return;
        if (e.changedTouches.length === 1) {
            const touchEndX = e.changedTouches[0].screenX;
            const touchEndY = e.changedTouches[0].screenY;
            const diffX = Math.abs(touchEndX - touchStartX);
            const diffY = Math.abs(touchEndY - touchStartY);
            if (diffX > 80 && diffX > diffY) {
                if (store.userRole !== "admin") {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
                }
                if (touchEndX < touchStartX) {
                    wsSend(WS_ACTIONS.NEXT);
                } else {
                    wsSend(WS_ACTIONS.PREV);
                }
            }
        }
    });
})();

// --- platform/keyboard.js ---
(function() {
    if (window.matchMedia('(pointer: fine)').matches) {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            switch (e.code) {
                case 'Space':
                    e.preventDefault();
                    cmd('play');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    cmd('next');
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    cmd('prev');
                    break;
            }
        });
    }
})();

// --- audio.js ---
let localAudio = null;
let audioUnlocked = false;
let _unlocking = false;
let _lastLoadedVideoId = null;
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
                    store.position = localAudio.currentTime;
                    renderProgress();
                }
                syncLocalLyrics();
            }
        });
    }
    return localAudio;
}
let audioCtx = null;
let analyser = null;
let dataArray = null;
function initVisualizer() {
    startFakeBeatLoop();
}
let _fakeBeatRaf = null;
function startFakeBeatLoop() {
    if (_fakeBeatRaf) return;
    const BASE_INTERVAL = 500;
    let lastBeat = 0;
    function tick(ts) {
        if (store.status !== 'PLAYING') {
            if (dom.tabHome) {
                dom.tabHome.style.removeProperty('--beat-glow-opacity');
                dom.tabHome.style.removeProperty('--beat-bg-brightness');
                dom.tabHome.style.removeProperty('--beat-glow-transition');
            }
            if (_fakeBeatRaf) {
                cancelAnimationFrame(_fakeBeatRaf);
                _fakeBeatRaf = null;
            }
            return;
        }
        _fakeBeatRaf = requestAnimationFrame(tick);
        const elapsed = ts - lastBeat;
        if (elapsed < BASE_INTERVAL) return;
        lastBeat = ts;
        if (!dom.tabHome) return;
        dom.tabHome.style.setProperty('--beat-glow-opacity', '0.5');
        dom.tabHome.style.setProperty('--beat-bg-brightness', '0.28');
        dom.tabHome.style.setProperty('--beat-glow-transition', '0.15s');
        setTimeout(() => {
            if (!dom.tabHome) return;
            dom.tabHome.style.setProperty('--beat-glow-opacity', '0.4');
            dom.tabHome.style.setProperty('--beat-bg-brightness', '0.22');
            dom.tabHome.style.setProperty('--beat-glow-transition', '0.4s');
        }, 150);
    }
    _fakeBeatRaf = requestAnimationFrame(tick);
}
let _vizRafId = null;
function startVisualizerLoop() {
    if (!analyser || !dom.vinylRecord) return;
    const isBrowser = store.userRole === "client" || store.audio_output === "browser";
    if (!isBrowser || store.status !== "PLAYING") {
        if (dom.tabHome) {
            dom.tabHome.style.removeProperty('--beat-glow-opacity');
            dom.tabHome.style.removeProperty('--beat-bg-brightness');
            dom.tabHome.style.removeProperty('--beat-glow-transition');
        }
        _vizRafId = null;
        return;
    }
    analyser.getByteFrequencyData(dataArray);
    let bassSum = 0;
    for (let i = 0; i < 10; i++) bassSum += dataArray[i];
    const ratio = (bassSum / 10) / 255;
    if (dom.tabHome) {
        dom.tabHome.style.setProperty('--beat-glow-opacity', (0.4 + ratio * 0.2).toFixed(3));
        dom.tabHome.style.setProperty('--beat-bg-brightness', (0.2 + ratio * 0.1).toFixed(3));
        dom.tabHome.style.setProperty('--beat-glow-transition', ratio > 0.4 ? '0.2s' : '0.4s');
    }
    _vizRafId = requestAnimationFrame(startVisualizerLoop);
}
function resumeVisualizerLoop() {
    if (!_vizRafId && analyser) startVisualizerLoop();
}
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
            } else syncBrowserAudio(true);
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
        startFakeBeatLoop();
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
        initVisualizer();
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
        _hideTapToPlayBanner();
        audio.src = expectedSrc;
        if (!window.isDraggingVol) {
            audio.volume = Math.max(0, Math.min(1, (store.volume || 80) / 100));
        }
        audio.onended = () => {
            console.log("[radio] track ended, requesting next...");
            if (store.audio_output === "browser") {
                wsSend(WS_ACTIONS.NEXT, { video_id: track.video_id });
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
            if (store.position > 5 && Math.abs(audio.currentTime - store.position) > 5) {
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
// --- actions.js ---

const WS_ACTIONS = Object.freeze({
    AUTH: "auth",
    PLAY_TRACK: "play_track",
    TOGGLE_PAUSE: "toggle_pause",
    NEXT: "next",
    PREV: "prev",
    STOP: "stop",
    SEEK: "seek",
    QUEUE_SELECT: "queue_select",
    QUEUE_REMOVE: "queue_remove",
    QUEUE_ADD: "queue_add",
    QUEUE_REORDER: "queue_reorder",
    ENQUEUE_ARTIST_SONGS: "enqueue_artist_songs",
    ENQUEUE_GENRE_SONGS: "enqueue_genre_songs",
    RADIO_RANDOMIZE: "radio_randomize",
    VOLUME_UP: "volume_up",
    VOLUME_DOWN: "volume_down",
    VOLUME_SET: "volume_set",
    SET_MODE: "set_mode",
    SET_OUTPUT: "set_output",
    SET_SPONSORBLOCK: "set_sponsorblock",
    LYRICS_OFFSET: "lyrics_offset",
    DOWNLOAD: "download",
    DELETE_DOWNLOAD: "delete_download",
    SEARCH: "search",
    DISCOVER: "discover",
    TOGGLE_FAVORITE: "toggle_favorite"
});

// --- ws.js ---
let ws = null;
let wsReconnectTimer = null;
function wsConnect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${location.host}/ws`;
    showConnectionToast("Menghubungkan...", "connecting");
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
            const token = window.safeStorage.get("ytgui_session_token");
            if (token) {
                wsSend(WS_ACTIONS.AUTH, { token: token });
            }
            const savedOutput = window.safeStorage.get("ytgui_audio_output") || "browser";
            wsSend(WS_ACTIONS.SET_OUTPUT, { output: savedOutput });
        } else if (store.userRole === "client") {
            if (store.active_tab === "home" || store.active_tab === "discover") {
                wsSend(WS_ACTIONS.DISCOVER);
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
                window.safeStorage.set("ytgui_user_role", "admin");
                if (msg.data.token) {
                    window.safeStorage.set("ytgui_session_token", msg.data.token);
                }
                dom.loginErrorMsg.textContent = "";
                dom.portalLoginForm.classList.add("hidden");
                applyRoleUI();
                showLogToast("Akses Admin Diterima!");
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
                    if (!window.audioBlocked) {
                        _resumeAndPlay(audio);
                    }
                }
            }
            renderProgress();
            renderPlayBtn();
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
                requestAnimationFrame(() => syncLocalLyrics());
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

// --- main.js ---
(function () {
    "use strict";
    function init() {
        document.body.dataset.activeTab = (typeof store !== "undefined" && store.active_tab)
            ? store.active_tab
            : "home";
        initDOM();
        const initTab = document.body.dataset.activeTab;
        if (dom["tab" + initTab.charAt(0).toUpperCase() + initTab.slice(1)]) {
            dom["tab" + initTab.charAt(0).toUpperCase() + initTab.slice(1)].classList.add("active");
        }
        const navBtn = document.querySelector(`.nav-btn[data-tab="${initTab}"]`);
        if (navBtn) {
            navBtn.classList.add("active");
            navBtn.setAttribute("aria-selected", "true");
        }
        initPortal();
        initAudio();
        initEvents();
        wsConnect();
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(r) { console.log('SW registered'); })
                .catch(function(e) { console.error('SW failed', e); });
        }
    }
    window.switchTab = function(tab) {
        store.active_tab = tab;
        document.body.dataset.activeTab = tab;
        TABS.forEach((t) => {
            const panel = dom["tab" + t.charAt(0).toUpperCase() + t.slice(1)];
            if (panel) {
                if (t === tab) panel.classList.add("active");
                else panel.classList.remove("active");
            }
        });
        document.querySelectorAll(".nav-btn").forEach((btn) => {
            if (btn.dataset.tab === tab) {
                btn.classList.add("active");
                btn.setAttribute("aria-selected", "true");
            } else {
                btn.classList.remove("active");
                btn.setAttribute("aria-selected", "false");
            }
        });
        if (tab === "search") {
            setTimeout(() => dom.searchInput.focus(), 100);
        }
        if (tab === "discover" || tab === "home") {
            wsSend(WS_ACTIONS.DISCOVER);
        }
    };
    document.addEventListener("DOMContentLoaded", init);
})();

