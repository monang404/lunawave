import { describe, it, expect, vi, beforeEach } from "vitest";

import { on } from "../../web/static/shared/js/bus.js";
import { store } from "../../web/static/shared/js/store.js";
import { dom } from "../../web/static/shared/js/dom.js";
import * as toast from "../../web/static/shared/js/render/toast.js";
import * as search from "../../web/static/shared/js/render/search.js";
import * as discoverTab from "../../web/static/shared/js/render/discover-tab.js";

// Mock out UI renderers
vi.mock("../../web/static/shared/js/render/toast.js", () => ({ showLogToast: vi.fn(), showPersistentToast: vi.fn(), hidePersistentToast: vi.fn(), showConnectionToast: vi.fn(), hideConnectionToast: vi.fn() }));
vi.mock("../../web/static/shared/js/services/auth.js", () => ({ applyRoleUI: vi.fn(), login: vi.fn(), logout: vi.fn() }));
vi.mock("../../web/static/shared/js/render/full-state.js", () => ({ renderFullState: vi.fn(), applyFullState: vi.fn() }));
vi.mock("../../web/static/shared/js/render/search.js", () => ({ renderSearchResults: vi.fn(), updateSearchPlayingState: vi.fn() }));
vi.mock("../../web/static/shared/js/render/discover-tab.js", () => ({ renderDiscoverTab: vi.fn(), renderRecentRow: vi.fn(), updateDiscoverPlayingState: vi.fn() }));
vi.mock("../../web/static/shared/js/render/now-playing.js", () => ({ renderNowPlaying: vi.fn(), syncPlayerStateAttr: vi.fn() }));
vi.mock("../../web/static/shared/js/render/player.js", () => ({ renderPlayerState: vi.fn(), renderProgress: vi.fn(), renderPlayBtn: vi.fn(), renderPlayerBar: vi.fn(), resetAnchorClock: vi.fn(), setPositionAnchor: vi.fn() }));
vi.mock("../../web/static/shared/js/render/queue.js", () => ({ renderQueue: vi.fn() }));
vi.mock("../../web/static/shared/js/render/radio-tab.js", () => ({ renderRadio: vi.fn() }));
vi.mock("../../web/static/shared/js/render/lyrics.js", () => ({ renderLyrics: vi.fn(), syncLocalLyrics: vi.fn() }));
vi.mock("../../web/static/shared/js/audio/playback-sync.js", () => ({ syncBrowserAudio: vi.fn(), getOrInitAudio: vi.fn(), _resumeAndPlay: vi.fn() }));

// Setup DOM mocks
dom.loginErrorMsg = { textContent: "" };
dom.portalLoginForm = { classList: { add: vi.fn(), remove: vi.fn() } };
dom.setupSubmitBtn = { disabled: true, textContent: "" };
dom.setupErrorMsg = { textContent: "" };
dom.setupConfirmErrorMsg = { textContent: "" };
dom.setupScreen = { classList: { add: vi.fn(), remove: vi.fn() } };
dom.portalScreen = { classList: { add: vi.fn(), remove: vi.fn() } };
dom.adminUsername = { value: "someuser" };
dom.logToast = { textContent: "", classList: { add: vi.fn(), remove: vi.fn() } };
dom.statusDot = { classList: { add: vi.fn(), remove: vi.fn() } };
dom.statusText = { textContent: "" };
dom.outputToggleBtn = { classList: { add: vi.fn(), remove: vi.fn() }, textContent: "" };

// Mock globalThis.safeStorage for ES modules
globalThis.safeStorage = { set: vi.fn(), remove: vi.fn(), get: vi.fn() };

import * as wsModule from "../../web/static/shared/js/ws.js";

// vi.mock() above replaces toast.js/search.js/discover-tab.js entirely, so the
// real init*BusSubscriptions() (which call bus.on(...)) never run -- normally
// main.js calls these at startup. Without this, ws.js's bus(...) emits have no
// listeners and the mocked render fns below are never invoked. Wire them here
// to mirror what main.js does in the real app.
on("toast:log", ({ message }) => toast.showLogToast(message));
on("toast:connection-show", ({ text, type }) => toast.showConnectionToast(text, type));
on("toast:connection-hide", () => toast.hideConnectionToast());
on("search:results", (data) => search.renderSearchResults(data));
on("discover:tab-changed", () => discoverTab.renderDiscoverTab());
on("discover:recent-changed", (data) => discoverTab.renderRecentRow(data));

describe("WebSocket Message Router", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(store, { status: "IDLE", userRole: "client", is_online: true });
  });

  it("handles auth_status success", () => {
    wsModule.handleServerMessage({ type: "auth_status", data: { success: true, token: "abc" } });
    expect(store.userRole).toBe("admin");
    expect(globalThis.safeStorage.set).toHaveBeenCalledWith("lunawave_session_token", "abc");
    expect(toast.showLogToast).toHaveBeenCalledWith("Akses Admin Diterima!");
  });

  it("handles setup_status success -- switches from setup-screen to portal-screen", () => {
    wsModule.handleServerMessage({ type: "setup_status", data: { success: true } });
    expect(dom.setupSubmitBtn.disabled).toBe(false);
    expect(dom.setupScreen.classList.remove).toHaveBeenCalledWith("portal-active");
    expect(dom.portalScreen.classList.add).toHaveBeenCalledWith("portal-active");
    expect(dom.adminUsername.value).toBe("");
    expect(toast.showLogToast).toHaveBeenCalledWith("Akun admin berhasil dibuat! Silakan login.");
  });

  it("handles setup_status failure -- keeps setup-screen, shows server message", () => {
    dom.setupScreen.classList.remove.mockClear();
    dom.portalScreen.classList.add.mockClear();
    wsModule.handleServerMessage({
      type: "setup_status",
      data: { success: false, message: "Akun admin sudah pernah dibuat. Silakan login." },
    });
    expect(dom.setupSubmitBtn.disabled).toBe(false);
    expect(dom.setupErrorMsg.textContent).toBe("Akun admin sudah pernah dibuat. Silakan login.");
    expect(dom.setupScreen.classList.remove).not.toHaveBeenCalled();
    expect(dom.portalScreen.classList.add).not.toHaveBeenCalled();
  });

  it("handles log", () => {
    wsModule.handleServerMessage({ type: "log", data: "Test log message" });
    expect(toast.showLogToast).toHaveBeenCalledWith("Test log message");
  });

  it("handles error", () => {
    wsModule.handleServerMessage({ type: "error", data: "Test error" });
    expect(toast.showLogToast).toHaveBeenCalledWith("Error: Test error");
  });

  it("handles search_results", () => {
    wsModule.handleServerMessage({ type: "search_results", data: [] });
    expect(search.renderSearchResults).toHaveBeenCalledWith([]);
  });

  it("handles discover_data and stores favorites alongside recent/cached", () => {
    wsModule.handleServerMessage({
      type: "discover_data",
      data: {
        recent: [{ video_id: "r1" }],
        favorites: [{ video_id: "f1" }],
        cached_tracks: [{ video_id: "c1" }],
        featured_artists: [],
        featured_genres: [],
      },
    });
    expect(store.discover_recent).toEqual([{ video_id: "r1" }]);
    expect(store.discover_favorites).toEqual([{ video_id: "f1" }]);
    expect(store.discover_cached).toEqual([{ video_id: "c1" }]);
    expect(discoverTab.renderDiscoverTab).toHaveBeenCalled();
  });

  it("defaults discover_favorites to empty array when server omits it", () => {
    wsModule.handleServerMessage({
      type: "discover_data",
      data: { recent: [], cached_tracks: [], featured_artists: [], featured_genres: [] },
    });
    expect(store.discover_favorites).toEqual([]);
  });
});
