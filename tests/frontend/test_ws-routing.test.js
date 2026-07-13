import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock globals
global.store = { status: "IDLE", userRole: "client", is_online: true };
global.dom = { loginErrorMsg: {}, portalLoginForm: { classList: { add: vi.fn() } } };
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
});
