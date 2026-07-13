function applyFullState(data) {
    Object.assign(store, data);
    if (typeof setPositionAnchor === "function") {
        setPositionAnchor(store.position);
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
}
