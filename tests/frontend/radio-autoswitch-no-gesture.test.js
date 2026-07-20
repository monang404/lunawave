import { describe, it, expect, vi, beforeEach } from "vitest";

// PATCH-2026-07-20-135 regression.
//
// Skenario yang sebelumnya belum pernah dipetakan lewat test: radio
// auto-switch ke track berikutnya TANPA klik/tap user. Server broadcast
// "progress" dengan status PLAYING, tapi <audio> browser masih paused
// (AudioContext ter-suspend lagi -- umum di iOS Safari/PWA setelah radio
// pindah track otomatis). Jalur FIX-RADIO-08 di ws.js menangani ini dengan
// memanggil _resumeAndPlay() tanpa menunggu gesture baru. Test ini
// menjalankan ws.js ASLI (require langsung), sama seperti
// tests/frontend/pause-race.test.js.

const storeModule = require("../../web/static/js/store.js");

global.dom = {};
global.store = storeModule.store;
global.window = { location: { origin: "https://example.local" } };
global.markPendingToggle = storeModule.markPendingToggle;
global.isPendingToggleActive = storeModule.isPendingToggleActive;
global.getOrInitAudio = vi.fn();
global.renderProgress = vi.fn();
global.renderPlayBtn = vi.fn();
global.renderNowPlaying = vi.fn();
global.renderQueue = vi.fn();
global.renderRadio = vi.fn();
global.syncPlayerStateAttr = vi.fn();
global.setPositionAnchor = vi.fn();
global.resetAnchorClock = vi.fn();
global.syncBrowserAudio = vi.fn();
global._resumeAndPlay = vi.fn();

const wsModule = require("../../web/static/js/ws.js");

function makeStuckPausedAudio() {
  return {
    paused: true, // stuck paused walau status server PLAYING
    src: "https://example.local/api/stream/abc12345678",
    readyState: 4, // HAVE_ENOUGH_DATA -- sudah ter-load penuh
    currentTime: 40,
  };
}

describe("FIX-RADIO-08: radio auto-switch memicu resume tanpa gesture user", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(global.store, {
      status: "PLAYING",
      audio_output: "browser",
      userRole: "client",
      current_track: { video_id: "abc12345678" },
    });
    global.window.pendingToggleTarget = null;
    global.window.audioBlocked = false; // belum pernah diblokir sebelumnya
  });

  it("memanggil _resumeAndPlay() begitu server bilang PLAYING tapi audio browser masih stuck paused", () => {
    const audio = makeStuckPausedAudio();
    global.getOrInitAudio.mockReturnValue(audio);

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 40, server_ts: 1 },
    });

    // Tidak ada gesture user apa pun di test ini -- murni broadcast server.
    expect(global._resumeAndPlay).toHaveBeenCalledTimes(1);
    expect(global._resumeAndPlay).toHaveBeenCalledWith(audio);
  });

  it("TIDAK retry lagi kalau window.audioBlocked sudah true (sudah pernah ditolak browser sebelumnya)", () => {
    const audio = makeStuckPausedAudio();
    global.getOrInitAudio.mockReturnValue(audio);
    global.window.audioBlocked = true; // sudah ketahuan diblokir sebelumnya

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 40, server_ts: 1 },
    });

    // Guard PATCH-ANDROID-AUDIO-01: jangan spam retry diam-diam, tunggu tap
    // user di banner (diuji terpisah di audio-unlock.test.js).
    expect(global._resumeAndPlay).not.toHaveBeenCalled();
  });

  it("tidak memanggil _resumeAndPlay kalau audio sudah aktif main (bukan stuck)", () => {
    const audio = makeStuckPausedAudio();
    audio.paused = false; // sudah main normal
    global.getOrInitAudio.mockReturnValue(audio);

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 41, server_ts: 1 },
    });

    expect(global._resumeAndPlay).not.toHaveBeenCalled();
  });
});
