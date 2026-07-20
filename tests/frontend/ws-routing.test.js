import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock globals
global.store = { status: "IDLE", userRole: "client", is_online: true };
global.dom = {
  loginErrorMsg: {},
  portalLoginForm: { classList: { add: vi.fn() } },
  setupSubmitBtn: { disabled: true, textContent: "" },
  setupErrorMsg: { textContent: "" },
  setupConfirmErrorMsg: { textContent: "" },
  setupScreen: { classList: { add: vi.fn(), remove: vi.fn() } },
  portalScreen: { classList: { add: vi.fn(), remove: vi.fn() } },
  adminUsername: { value: "someuser" },
};
global.window = { safeStorage: { set: vi.fn(), remove: vi.fn(), get: vi.fn() } };
global.showLogToast = vi.fn();
global.applyRoleUI = vi.fn();
global.renderFullState = vi.fn();
global.renderSearchResults = vi.fn();
global.renderDiscoverTab = vi.fn();
global.renderRecentRow = vi.fn();
global.renderPlayerBar = vi.fn();
global.renderSettingsSheet = vi.fn();

const wsModule = require("../../web/static/js/ws.js");

describe("WebSocket Message Router", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("handles auth_status success", () => {
    wsModule.handleServerMessage({ type: "auth_status", data: { success: true, token: "abc" } });
    expect(global.store.userRole).toBe("admin");
    expect(global.window.safeStorage.set).toHaveBeenCalledWith("lunawave_session_token", "abc");
    expect(global.showLogToast).toHaveBeenCalledWith("Akses Admin Diterima!");
  });

  it("handles setup_status success -- switches from setup-screen to portal-screen", () => {
    wsModule.handleServerMessage({ type: "setup_status", data: { success: true } });
    expect(global.dom.setupSubmitBtn.disabled).toBe(false);
    expect(global.dom.setupScreen.classList.remove).toHaveBeenCalledWith("portal-active");
    expect(global.dom.portalScreen.classList.add).toHaveBeenCalledWith("portal-active");
    expect(global.dom.adminUsername.value).toBe("");
    expect(global.showLogToast).toHaveBeenCalledWith("Akun admin berhasil dibuat! Silakan login.");
  });

  it("handles setup_status failure -- keeps setup-screen, shows server message", () => {
    global.dom.setupScreen.classList.remove.mockClear();
    global.dom.portalScreen.classList.add.mockClear();
    wsModule.handleServerMessage({
      type: "setup_status",
      data: { success: false, message: "Akun admin sudah pernah dibuat. Silakan login." },
    });
    expect(global.dom.setupSubmitBtn.disabled).toBe(false);
    expect(global.dom.setupErrorMsg.textContent).toBe("Akun admin sudah pernah dibuat. Silakan login.");
    expect(global.dom.setupScreen.classList.remove).not.toHaveBeenCalled();
    expect(global.dom.portalScreen.classList.add).not.toHaveBeenCalled();
  });

  it("handles log", () => {
    wsModule.handleServerMessage({ type: "log", data: "Test log message" });
    expect(global.showLogToast).toHaveBeenCalledWith("Test log message");
  });

  it("handles error", () => {
    wsModule.handleServerMessage({ type: "error", data: "Test error" });
    expect(global.showLogToast).toHaveBeenCalledWith("Error: Test error");
  });

  it("handles search_results", () => {
    wsModule.handleServerMessage({ type: "search_results", data: [] });
    expect(global.renderSearchResults).toHaveBeenCalledWith([]);
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
    expect(global.store.discover_recent).toEqual([{ video_id: "r1" }]);
    expect(global.store.discover_favorites).toEqual([{ video_id: "f1" }]);
    expect(global.store.discover_cached).toEqual([{ video_id: "c1" }]);
    expect(global.renderDiscoverTab).toHaveBeenCalled();
  });

  it("defaults discover_favorites to empty array when server omits it", () => {
    wsModule.handleServerMessage({
      type: "discover_data",
      data: { recent: [], cached_tracks: [], featured_artists: [], featured_genres: [] },
    });
    expect(global.store.discover_favorites).toEqual([]);
  });
});
