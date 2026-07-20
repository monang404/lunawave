import { describe, it, expect, vi, beforeEach } from "vitest";

// FIX-PAUSE-RACE-01 regression test.
//
// Skenario nyata yang diperbaiki: user klik pause di jaringan jelek -> audio
// browser sudah benar-benar paused -> tapi progress broadcast dari server yang
// tiba TELAT (RTT > grace-window lama) masih bawa status PLAYING lama -> client
// menimpa balik store.status jadi PLAYING -> cabang FIX-RADIO-08 di ws.js
// melihat "status PLAYING tapi audio.paused" -> auto-play tanpa user gesture.
//
// Test ini menjalankan MODUL ASLI (store.js utk markPendingToggle/
// isPendingToggleActive, ws.js utk handleServerMessage) -- bukan re-implementasi
// logikanya di sini -- supaya benar-benar menguji kode produksi.

const storeModule = require("../../web/static/js/store.js");

global.dom = {};
global.store = storeModule.store;
global.window = {};
global.markPendingToggle = storeModule.markPendingToggle;
global.isPendingToggleActive = storeModule.isPendingToggleActive;
global.getOrInitAudio = vi.fn();
global.syncBrowserAudio = vi.fn();
global.renderProgress = vi.fn();
global.renderPlayBtn = vi.fn();
global.renderNowPlaying = vi.fn();
global.renderQueue = vi.fn();
global.renderRadio = vi.fn();
global.syncPlayerStateAttr = vi.fn();
global.setPositionAnchor = vi.fn();
global.resetAnchorClock = vi.fn();
global._resumeAndPlay = vi.fn((audio) => {
  audio.paused = false; // simulasikan audio benar-benar play lagi
});

const wsModule = require("../../web/static/js/ws.js");

function makeFakeAudio() {
  return { paused: true, src: "https://example.com/stream.mp3", readyState: 4, currentTime: 0 };
}

describe("FIX-PAUSE-RACE-01: pause tidak auto-play lagi walau progress message telat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(global.store, {
      status: "PAUSED",
      audio_output: "browser",
      userRole: "admin",
      current_track: { video_id: "abc" },
    });
    global.window.pendingToggleTarget = null;
    global.window.toggleSentAt = 0;
    global.window.audioBlocked = false;
  });

  it("menolak progress PLAYING basi selama masih menunggu konfirmasi PAUSED (RTT lama)", () => {
    const audio = makeFakeAudio();
    audio.paused = true; // user sudah klik pause, audio benar-benar berhenti
    global.getOrInitAudio.mockReturnValue(audio);

    // User klik pause -> optimistic update + tandai target yang ditunggu.
    global.store.status = "PAUSED";
    global.markPendingToggle("PAUSED");

    // Progress message BASI tiba 2 detik kemudian (RTT lambat), masih bawa
    // status lama "PLAYING" dari sebelum server sempat memproses toggle kita.
    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 10, server_ts: 1 },
    });

    // Sebelumnya (bug): store.status ketimpa balik ke PLAYING dan audio
    // di-auto-resume lewat _resumeAndPlay(). Sekarang: message basi ditolak
    // karena kontradiktif dengan pendingToggleTarget yang masih aktif.
    expect(global.store.status).toBe("PAUSED");
    expect(global._resumeAndPlay).not.toHaveBeenCalled();
    expect(audio.paused).toBe(true);
  });

  it("menerima progress PAUSED begitu server benar-benar mengonfirmasi target", () => {
    const audio = makeFakeAudio();
    audio.paused = true;
    global.getOrInitAudio.mockReturnValue(audio);

    global.store.status = "PAUSED";
    global.markPendingToggle("PAUSED");

    // Server akhirnya memproses toggle kita dan broadcast status yang benar.
    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PAUSED", position: 10, server_ts: 2 },
    });

    expect(global.store.status).toBe("PAUSED");
    expect(global.window.pendingToggleTarget).toBeNull(); // sudah dikonfirmasi, berhenti menunggu
  });

  it("safety-valve: berhenti menolak update setelah 8 detik kalau command kita sendiri hilang", () => {
    const audio = makeFakeAudio();
    audio.paused = true;
    global.getOrInitAudio.mockReturnValue(audio);

    global.store.status = "PAUSED";
    global.markPendingToggle("PAUSED");
    // Simulasikan sudah 9 detik berlalu sejak toggle dikirim (command hilang di jalan).
    global.window.toggleSentAt = Date.now() - 9000;

    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 10, server_ts: 3 },
    });

    // Safety-valve sudah habis -> update dari server diterima apa adanya,
    // supaya client tidak macet permanen menolak semua update.
    expect(global.store.status).toBe("PLAYING");
    expect(global.window.pendingToggleTarget).toBeNull();
  });

  it("status tidak macet kalau user next/prev sebelum toggle pause sempat dikonfirmasi server (edge case)", () => {
    global.store.status = "PAUSED";
    global.markPendingToggle("PAUSED"); // user pause, belum dikonfirmasi server

    global.store.status = "LOADING"; // user langsung klik next sebelum konfirmasi datang
    wsModule.wsSend("next", { video_id: "xyz" });

    expect(global.window.pendingToggleTarget).toBeNull(); // target basi harus di-clear

    // Progress utk track baru datang -- dulu ini akan ditolak krn dianggap
    // kontradiktif dgn pendingToggleTarget="PAUSED" yang basi, bikin status
    // macet di LOADING sampai safety-valve 8 detik habis.
    wsModule.handleServerMessage({
      type: "progress",
      data: { status: "PLAYING", position: 0, server_ts: 4 },
    });

    expect(global.store.status).toBe("PLAYING");
  });
});
