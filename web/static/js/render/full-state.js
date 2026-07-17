function applyFullState(data) {
    Object.assign(store, data);
    if (typeof setPositionAnchor === "function") {
        setPositionAnchor(store.position);
    }
    // Sync browser audio playback rate jika output = browser
    if (store.audio_output === "browser" && typeof getOrInitAudio === "function") {
        const audio = getOrInitAudio();
        if (audio && store.playback_speed) {
            audio.playbackRate = store.playback_speed;
        }
    }
    // Sync speed dropdown ke nilai dari server
    if (dom.ssSpeedSelect && store.playback_speed) {
        dom.ssSpeedSelect.value = store.playback_speed.toFixed(2);
    }
    renderFullState();
    if (store.userRole !== 'portal' && typeof syncBrowserAudio === "function") {
        syncBrowserAudio();
    }
}

function renderFullState() {
    if (typeof renderHeader === "function") renderHeader();
    if (typeof renderNowPlaying === "function") renderNowPlaying();
    if (typeof renderProgress === "function") renderProgress();
    if (typeof renderPlayerBar === "function") renderPlayerBar();
    if (typeof renderRadio === "function") renderRadio();
    if (typeof renderQueue === "function") renderQueue();
    if (typeof renderLyrics === "function") renderLyrics();
    if (typeof renderSettingsSheet === "function") renderSettingsSheet();
    if (typeof updateSearchPlayingState === "function") updateSearchPlayingState();
    if (typeof updateDiscoverPlayingState === "function") updateDiscoverPlayingState();

    // Dynamic Title & Media Session API
    const track = store.current_track;
    if (track) {
        document.title = `${track.title} - ${track.artist}`;
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: track.title,
                artist: track.artist,
                album: 'LunaWave',
                artwork: [
                    { src: track.cover || '/static/img/default-cover.jpg', sizes: '512x512', type: 'image/jpeg' }
                ]
            });
            navigator.mediaSession.setActionHandler('play', () => { if(typeof wsSend==="function") wsSend("play"); });
            navigator.mediaSession.setActionHandler('pause', () => { if(typeof wsSend==="function") wsSend("pause"); });
            navigator.mediaSession.setActionHandler('previoustrack', () => { if(typeof wsSend==="function") wsSend("prev"); });
            navigator.mediaSession.setActionHandler('nexttrack', () => { if(typeof wsSend==="function") wsSend("next"); });
        }
    } else {
        document.title = "LunaWave — Midnight Audio Experience";
    }
}
