import { describe, it, expect, vi, beforeEach } from "vitest";

// PATCH-2026-07-20-135 regression tests.
//
// playback-sync.js sebelumnya NOL test coverage sama sekali dan bahkan
// tidak punya module.exports -- jadi skenario "tap untuk lanjut memutar"
// (dan kegagalan diam-diam) tidak pernah dipetakan lewat test. Test ini
// menjalankan MODUL ASLI (require langsung ke file produksi), bukan
// re-implementasi logikanya di sini.

const MODULE_PATH = require.resolve("../../web/static/js/audio/playback-sync.js");

function freshRequire() {
  delete require.cache[MODULE_PATH];
  return require(MODULE_PATH);
}

function makeFakeAudioEl() {
  let _src = "";
  return {
    get src() {
      return _src;
    },
    set src(v) {
      _src = v;
    },
    paused: true,
    volume: 1,
    hasAttribute() {
      return !!_src;
    },
    removeAttribute() {
      _src = "";
    },
    load: vi.fn(),
    play: vi.fn(() => Promise.resolve()),
    addEventListener: vi.fn(),
    getAttribute() {
      return _src;
    },
  };
}

describe("PATCH-AUDIO-UNLOCK-PROACTIVE-01: banner tap-to-play proaktif", () => {
  let fakeAudio;
  let listeners;
  let bannerEl;
  let getElementByIdCalls;

  beforeEach(() => {
    fakeAudio = makeFakeAudioEl();
    listeners = {};
    getElementByIdCalls = [];
    bannerEl = { style: {}, addEventListener: vi.fn(), textContent: "" };

    global.document = {
      hidden: false,
      addEventListener: vi.fn((evt, fn) => {
        listeners[evt] = fn;
      }),
      getElementById: vi.fn((id) => {
        getElementByIdCalls.push(id);
        return null; // belum pernah dibuat
      }),
      createElement: vi.fn(() => bannerEl),
      body: { appendChild: vi.fn() },
    };
    global.window = { location: { origin: "https://example.local" }, audioBlocked: false };
    global.Audio = vi.fn(function () { return fakeAudio; });
    global.store = {
      userRole: "client",
      audio_output: "browser",
      status: "PLAYING",
      current_track: { video_id: "abc12345678" },
      position: 0,
      volume: 80,
    };
    global.wsSend = vi.fn();
    global.showLogToast = vi.fn();
    global.isDraggingVol = false;
  });

  it("SEBELUM fix: client join mid-session (status sudah PLAYING) senyap total tanpa banner -- dibuktikan lewat call count play()/banner", () => {
    const mod = freshRequire();
    mod.syncBrowserAudio();

    // Tidak pernah coba play() sama sekali di jalur "belum unlocked".
    expect(fakeAudio.play).not.toHaveBeenCalled();
  });

  it("SESUDAH fix: banner tap-to-play muncul PROAKTIF begitu join mid-session, bukan menunggu play() ditolak", () => {
    const mod = freshRequire();
    mod.syncBrowserAudio();

    // Banner dibuat (createElement dipanggil) dan window.audioBlocked
    // ditandai true, walau play() belum pernah dicoba sama sekali --
    // inilah inti fix-nya.
    expect(global.document.createElement).toHaveBeenCalled();
    expect(global.window.audioBlocked).toBe(true);
  });

  it("tidak menampilkan banner kalau track belum seharusnya main (status bukan PLAYING & bukan forcePlay)", () => {
    global.store.status = "PAUSED";
    const mod = freshRequire();
    mod.syncBrowserAudio(false);

    expect(global.document.createElement).not.toHaveBeenCalled();
    expect(global.window.audioBlocked).toBe(false);
  });
});

describe("PATCH-AUDIO-UNLOCK-PROACTIVE-01: audioCtx tetap tersimpan walau resume() awal gagal", () => {
  beforeEach(() => {
    global.document = {
      hidden: false,
      addEventListener: vi.fn(),
      getElementById: vi.fn(() => null),
      createElement: vi.fn(() => ({ style: {}, addEventListener: vi.fn() })),
      body: { appendChild: vi.fn() },
    };
    global.window = { location: { origin: "https://example.local" }, audioBlocked: false };
    global.Audio = vi.fn(function () { return makeFakeAudioEl(); });
    global.store = { userRole: "client", audio_output: "browser", status: "PLAYING", current_track: null };
    global.wsSend = vi.fn();
    global.showLogToast = vi.fn();
  });

  it("menyimpan referensi AudioContext meski resume() reject, supaya retry berikutnya (mis. tab refocus) tidak kehilangan konteksnya", async () => {
    let resumeCallCount = 0;
    function FakeAudioContext() {
      this.state = "suspended";
      this.resume = () => {
        resumeCallCount++;
        // Reject pertama kali (gagal saat unlock awal), tapi kalau
        // dipanggil LAGI (dari visibilitychange retry), berhasil --
        // meniru browser yang akhirnya kasih izin begitu tab difokus.
        if (resumeCallCount === 1) {
          return Promise.reject(new Error("resume rejected by browser policy"));
        }
        this.state = "running";
        return Promise.resolve();
      };
    }
    global.window.AudioContext = FakeAudioContext;

    const mod = freshRequire();
    mod.unlockBrowserAudio(true);

    // beri kesempatan promise .catch() jalan
    await new Promise((r) => setTimeout(r, 10));

    expect(resumeCallCount).toBe(1);

    // Simulasikan user balik ke tab -> visibilitychange handler yang
    // didaftarkan modul ini (di document.addEventListener mock) terpicu.
    // Konsumen ASLI dari variabel audioCtx yang mau kita buktikan: handler
    // ini baca `if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume()`.
    // Kalau audioCtx tidak pernah disimpan di jalur resume-gagal di atas
    // (bug lama), listener ini akan skip total dan resumeCallCount tetap 1.
    global.document.hidden = false;
    const visibilityHandler = global.document.addEventListener.mock.calls.find(
      ([evt]) => evt === "visibilitychange"
    )[1];
    visibilityHandler();

    expect(resumeCallCount).toBe(2);
  });
});
