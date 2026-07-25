import { describe, it, expect, vi, beforeEach } from "vitest";

import { store, markPendingToggle, isPendingToggleActive } from "../../web/static/shared/js/store.js";

// Mock out audio and render components
vi.mock("../../web/static/shared/js/render/toast.js", () => ({ showLogToast: vi.fn(), showPersistentToast: vi.fn(), hidePersistentToast: vi.fn() }));
vi.mock("../../web/static/shared/js/audio/playback-sync.js", () => ({ getOrInitAudio: vi.fn(), syncBrowserAudio: vi.fn(), _resumeAndPlay: vi.fn() }));
vi.mock("../../web/static/shared/js/render/player.js", () => ({ renderProgress: vi.fn(), renderPlayBtn: vi.fn(), setPositionAnchor: vi.fn(), resetAnchorClock: vi.fn(), renderPlayerBar: vi.fn() }));
vi.mock("../../web/static/shared/js/render/now-playing.js", () => ({ renderNowPlaying: vi.fn(), syncPlayerStateAttr: vi.fn() }));
vi.mock("../../web/static/shared/js/render/queue.js", () => ({ renderQueue: vi.fn() }));
vi.mock("../../web/static/shared/js/render/radio-tab.js", () => ({ renderRadioTab: vi.fn(), renderRadio: vi.fn() }));
vi.mock("../../web/static/shared/js/render/discover-tab.js", () => ({ renderDiscoverTab: vi.fn(), updateDiscoverPlayingState: vi.fn(), renderRecentRow: vi.fn() }));
vi.mock("../../web/static/shared/js/render/search.js", () => ({ updateSearchPlayingState: vi.fn() }));
vi.mock("../../web/static/shared/js/render/lyrics.js", () => ({ renderLyrics: vi.fn(), syncLocalLyrics: vi.fn() }));

import * as playbackSync from "../../web/static/shared/js/audio/playback-sync.js";

globalThis.safeStorage = { set: vi.fn(), remove: vi.fn(), get: vi.fn() };
globalThis.window = globalThis; // Provide basic window mock if needed

import * as wsModule from "../../web/static/shared/js/ws.js";

function makeFakeAudio() {
  return { paused: true, src: "https://example.com/stream.mp3", readyState: 4, currentTime: 0 };
}

describe("FIX-PAUSE-RACE-01: pause tidak auto-play lagi walau progress message telat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(store, {
      status: "PAUSED",
      audio_output: "browser",
      userRole: "admin",
      current_track: { video_id: "abc" },
    });
    store.pendingToggleTarget = null;
    store.toggleSentAt = 0;

    // Some tests mutate window.pendingToggleTarget directly, let's proxy that to store if it was historically on window
    globalThis.pendingToggleTarget = null;
    globalThis.toggleSentAt = 0;
    globalThis.audioBlocked = false;
  });

  it("menolak progress PLAYING basi selama masih menunggu konfirmasi PAUSED (RTT lama)", () => {
    const audio = makeFakeAudio();
    audio.paused = true;
    playbackSync.getOrInitAudio.mockReturnValue(audio);

    store.status = "PAUSED";
    markPendingToggle("PAUSED");

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 10, server_ts: 1 },
    });

    expect(store.status).toBe("PAUSED");
    expect(playbackSync._resumeAndPlay).not.toHaveBeenCalled();
    expect(audio.paused).toBe(true);
  });

  it("menerima progress PAUSED begitu server benar-benar mengonfirmasi target", () => {
    const audio = makeFakeAudio();
    audio.paused = true;
    playbackSync.getOrInitAudio.mockReturnValue(audio);

    store.status = "PAUSED";
    markPendingToggle("PAUSED");

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PAUSED", position: 10, server_ts: 2 },
    });

    expect(store.status).toBe("PAUSED");
    expect(isPendingToggleActive()).toBe(false);
  });

  it("safety-valve: berhenti menolak update setelah 8 detik kalau command kita sendiri hilang", () => {
    const audio = makeFakeAudio();
    audio.paused = true;
    playbackSync.getOrInitAudio.mockReturnValue(audio);

    store.status = "PAUSED";
    markPendingToggle("PAUSED");
    // override internal time manually
    Object.assign(store, { toggleSentAt: Date.now() - 9000 });
    // also fallback for globalThis in case `store.js` relies on `window.toggleSentAt`
    globalThis.toggleSentAt = Date.now() - 9000;

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 10, server_ts: 3 },
    });

    expect(store.status).toBe("PLAYING");
    expect(isPendingToggleActive()).toBe(false);
  });

  it("status tidak macet kalau user next/prev sebelum toggle pause sempat dikonfirmasi server (edge case)", () => {
    store.status = "PAUSED";
    markPendingToggle("PAUSED");

    store.status = "LOADING";
    wsModule.wsSend("next", { video_id: "xyz" });

    expect(isPendingToggleActive()).toBe(false);

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 0, server_ts: 4 },
    });

    expect(store.status).toBe("PLAYING");
  });
});
