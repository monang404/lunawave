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
