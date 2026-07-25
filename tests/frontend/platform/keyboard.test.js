import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { store } from "../../../web/static/shared/js/store.js";

vi.mock("../../../web/static/shared/js/ws.js", () => ({ wsSend: vi.fn() }));

// NOTE on test ordering: platform/keyboard.js is an IIFE that attaches a
// `document.addEventListener('keydown', ...)` listener at *import* time,
// permanently, based on the matchMedia('(pointer: fine)') value evaluated
// right then. There is no teardown/unsubscribe exported by the module.
// So: the "touch device -> no listener" case is asserted FIRST (before any
// desktop-mode import has attached a listener to the shared jsdom
// `document`), and all later assertions rely on `toHaveBeenCalledWith`
// (not exact call counts), since re-importing after vi.resetModules() adds
// an *additional* listener that reacts consistently to the same store
// state -- it never contradicts an already-made assertion.
describe("platform/keyboard.js", () => {
  beforeEach(() => {
    vi.resetModules();
    store.userRole = "admin";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("registers no behavior on touch devices (pointer: fine not matched)", async () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockReturnValue({ matches: false })
    );
    await import("../../../web/static/shared/js/platform/keyboard.js");
    const { wsSend } = await import("../../../web/static/shared/js/ws.js");

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ArrowRight" }));
    expect(wsSend).not.toHaveBeenCalled();
  });

  it("sends 'next' on ArrowRight for an admin on desktop (pointer: fine)", async () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));
    await import("../../../web/static/shared/js/platform/keyboard.js");
    const { wsSend } = await import("../../../web/static/shared/js/ws.js");

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ArrowRight" }));
    expect(wsSend).toHaveBeenCalledWith("next");
  });

  it("sends 'prev' on ArrowLeft for an admin on desktop", async () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));
    await import("../../../web/static/shared/js/platform/keyboard.js");
    const { wsSend } = await import("../../../web/static/shared/js/ws.js");

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ArrowLeft" }));
    expect(wsSend).toHaveBeenCalledWith("prev");
  });

  it("ignores arrow keys for a non-admin user", async () => {
    store.userRole = "client";
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));
    await import("../../../web/static/shared/js/platform/keyboard.js");
    const { wsSend } = await import("../../../web/static/shared/js/ws.js");
    wsSend.mockClear();

    document.dispatchEvent(new KeyboardEvent("keydown", { code: "ArrowRight" }));
    expect(wsSend).not.toHaveBeenCalled();
  });

  it("ignores arrow keys while typing inside an input/textarea", async () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));
    await import("../../../web/static/shared/js/platform/keyboard.js");
    const { wsSend } = await import("../../../web/static/shared/js/ws.js");
    wsSend.mockClear();

    const input = document.createElement("input");
    document.body.appendChild(input);
    const event = new KeyboardEvent("keydown", { code: "ArrowRight" });
    Object.defineProperty(event, "target", { value: input });
    document.dispatchEvent(event);

    expect(wsSend).not.toHaveBeenCalled();
    input.remove();
  });
});
