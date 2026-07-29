import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { dom } from "../../../web/static/shared/js/dom.js";
import { store } from "../../../web/static/shared/js/store.js";
import { updateEqualizerState } from "../../../web/static/shared/js/render/equalizer.js";

function el(tag = "div") {
  return document.createElement(tag);
}

// PATCH-EQ-REDESIGN-01 regression tests. See the comment block at the top
// of render/equalizer.js for the full history of the bug this replaces.
describe("render/equalizer.js", () => {
  let hiddenGetter;

  beforeEach(() => {
    Object.assign(dom, { homeEqualizer: el() });
    Object.assign(store, { lyrics_lines: null, status: "PAUSED" });
    hiddenGetter = vi.spyOn(document, "hidden", "get").mockReturnValue(false);
  });

  afterEach(() => {
    hiddenGetter.mockRestore();
  });

  it("does nothing when dom.homeEqualizer is missing", () => {
    dom.homeEqualizer = null;
    expect(() => updateEqualizerState()).not.toThrow();
  });

  it("shows the container and animates when PLAYING with no lyrics and the page visible", () => {
    store.status = "PLAYING";
    store.lyrics_lines = null;
    updateEqualizerState();
    expect(dom.homeEqualizer.style.display).toBe("flex");
    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(false);
  });

  it("keeps the container visible but freezes the animation when idle/paused (no lyrics)", () => {
    store.status = "PAUSED";
    store.lyrics_lines = [];
    updateEqualizerState();
    expect(dom.homeEqualizer.style.display).toBe("flex");
    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(true);
  });

  it("hides the container entirely and freezes the animation once lyrics are available", () => {
    store.status = "PLAYING";
    store.lyrics_lines = ["a", "b"];
    updateEqualizerState();
    expect(dom.homeEqualizer.style.display).toBe("none");
    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(true);
  });

  it("freezes the animation while PLAYING with no lyrics if the page/tab is hidden (battery/CPU regression)", () => {
    store.status = "PLAYING";
    store.lyrics_lines = null;
    hiddenGetter.mockReturnValue(true);

    updateEqualizerState();

    // Container tetap "flex" (masih fallback yang benar untuk ditampilkan),
    // tapi animasinya WAJIB freeze -- sebelum patch ini tidak ada jalur
    // sama sekali yang mematikan animasi saat tab/layar tersembunyi selagi
    // status masih PLAYING, jadi keyframe terus dihitung di background.
    expect(dom.homeEqualizer.style.display).toBe("flex");
    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(true);
  });

  it("re-evaluates and unfreezes once the page becomes visible again via the visibilitychange listener", () => {
    store.status = "PLAYING";
    store.lyrics_lines = null;
    hiddenGetter.mockReturnValue(true);
    updateEqualizerState();
    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(true);

    hiddenGetter.mockReturnValue(false);
    document.dispatchEvent(new Event("visibilitychange"));

    expect(dom.homeEqualizer.classList.contains("eq-frozen")).toBe(false);
  });
});
