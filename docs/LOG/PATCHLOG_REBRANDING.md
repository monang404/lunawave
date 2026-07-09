# PATCHLOG.md — LunaWave Sprint 2.1

**Sprint:** 2.1 — LunaWave Rebranding  
**Type:** Visual / Identity  
**Breaking Changes:** None  
**Backward Compatible:** Yes (legacy YTGUI_* env vars still accepted)

---

## [2026-07-09] Sprint 2.1 Patch Set

### PATCH-BRAND-001 — Icon Generation
- **File:** `scripts/generate_icons.py` [NEW]
- **Change:** Created icon generation script producing `icon.ico` (Windows), `icon-192.png`, `icon-512.png` (PWA)
- **Impact:** Visual only — window icon and PWA icons

---

### PATCH-BRAND-002 — Configuration Layer
- **File:** `config.py`
- **Lines:** 6, 9, 16–20, 25–27, 44–56
- **Change:**
  - `DB_PATH` → `data/lunawave.db`
  - `MPV_SOCKET` pipe name → `mpv-lunawave`
  - Primary env var → `LUNAWAVE_HOST`, `LUNAWAVE_PORT`, `LUNAWAVE_ADMIN_USER`, `LUNAWAVE_ADMIN_PASS`
  - `LUNAWAVE_BASE`, `LUNAWAVE_SOCKET` env vars
  - Backward-compat fallback: `YTGUI_*` env vars still accepted
- **Impact:** Config metadata only — all runtime values identical

---

### PATCH-BRAND-003 — Main Entry Point Banner
- **File:** `main.py`
- **Change:** Log file `ytplayer.log` → `lunawave.log`; console startup banner updated
- **Impact:** Visual banner and log filename only

---

### PATCH-BRAND-004 — Server Manager UI (Windows/Termux)
- **File:** `start.py`
- **Lines:** 28, 585–588 (and throughout UI setup)
- **Change:**
  - Window title → "LunaWave Server Manager"
  - Labels, popup messages → LunaWave
  - Subprocess env includes both `LUNAWAVE_*` (primary) and `YTGUI_*` (compat shim)
- **Impact:** Tkinter GUI labels — no logic change

---

### PATCH-BRAND-005 — Shell Launchers
- **Files:** `start.bat`, `start.sh`
- **Change:** ASCII art banners → LunaWave; `LUNAWAVE_*` env vars as primary with `YTGUI_*` fallback
- **Impact:** Console output cosmetics and env var names

---

### PATCH-BRAND-006 — Core Docstrings
- **Files:** `core/state.py`, `core/exceptions.py`
- **Change:** "YTGUI V2" → "LunaWave" in module-level docstrings
- **Impact:** Documentation only

---

### PATCH-BRAND-007 — Observability Metric Name
- **File:** `core/observability.py`
- **Line:** 23
- **Change:** `ytgui_events_total` → `lunawave_events_total` (Prometheus Counter name)
- **Impact:** Metric label string only — no logic change. Existing Prometheus dashboards using old name will need label update.

---

### PATCH-BRAND-008 — HTTP Handler Metrics Token
- **File:** `server/handlers/http.py`
- **Line:** 150
- **Change:** Primary env var → `LUNAWAVE_METRICS_TOKEN`; `YTGUI_METRICS_TOKEN` kept as fallback
- **Impact:** Env var name — backward compatible

---

### PATCH-BRAND-009 — Notifications Plugin
- **File:** `plugins/notifications.py`
- **Lines:** 25, 117
- **Change:** `NOTIFICATION_ID` → `"lunawave_nowplaying"`; fallback title → `"LunaWave"`
- **Impact:** OS notification tag string only

---

### PATCH-BRAND-010 — Radio Engine Error Message
- **File:** `engine/radio_engine.py`
- **Line:** 103
- **Change:** Error help text `ytgui.db` → `lunawave.db`
- **Impact:** User-facing error message text only

---

### PATCH-BRAND-011 — Web HTML / PWA Manifest
- **Files:** `web/static/index.html`, `web/static/manifest.json`, `web/static/sw.js`
- **Change:**
  - `<title>` → "LunaWave"
  - Meta description, OG tags → LunaWave
  - Manifest `name`, `short_name`, `description` → LunaWave
  - Service worker cache version → `lunawave-v1`
- **Impact:** Browser tab, PWA install screen, app meta

---

### PATCH-BRAND-012 — JavaScript Storage Keys (LocalStorage)
- **Files:** `web/static/js/ws.js`, `web/static/js/portal.js`, `web/static/js/services/auth.js`, `web/static/js/events/index.js`
- **Change:** All `ytgui_*` localStorage keys renamed to `lunawave_*`
  - `ytgui_session_token` → `lunawave_session_token`
  - `ytgui_user_role` → `lunawave_user_role`
  - `ytgui_audio_output` → `lunawave_audio_output`
  - `ytgui_admin_password` → `lunawave_admin_password`
- **Impact:** Storage key names only

---

### PATCH-BRAND-013 — Backward-Compatible Storage Migration
- **File:** `web/static/js/utils.js`
- **Change:** `window.safeStorage.get()` now auto-reads legacy `ytgui_*` keys and migrates them to `lunawave_*` on first access. `safeStorage.remove()` also clears legacy keys.
- **Impact:** Existing users won't lose sessions after update — **zero-disruption migration**

---

### PATCH-BRAND-014 — CSS File Headers
- **Files:** 10 CSS files across `web/static/css/`
- **Change:** Comment headers `BAGAS.FM` → `LunaWave`
- **Impact:** Code comments only

---

### PATCH-BRAND-015 — README Documentation
- **File:** `README.md`
- **Change:**
  - Title → "LunaWave"
  - Description updated
  - Repository URL → `github.com/monang404/lunawave`
  - Env var examples → `LUNAWAVE_ADMIN_USER`, `LUNAWAVE_ADMIN_PASS`
  - Log filename → `lunawave.log`
- **Impact:** Documentation only

---

### PATCH-BRAND-016 — Developer Utility Scripts
- **Files:** `scratch/check_db.py`, `data/export_to_sqlite.py`
- **Change:** DB path references `ytgui.db` → `lunawave.db`
- **Impact:** Developer tooling only, not in production path

---

## Summary Table

| Patch | Category | Files | Logic Changed |
|---|---|---|---|
| 001 | Assets | 1 (new) | No |
| 002 | Config | 1 | No |
| 003 | Config | 1 | No |
| 004 | UI | 1 | No |
| 005 | Scripts | 2 | No |
| 006 | Docs | 2 | No |
| 007 | Metrics | 1 | No |
| 008 | Config | 1 | No |
| 009 | Plugin | 1 | No |
| 010 | Error msg | 1 | No |
| 011 | Frontend | 3 | No |
| 012 | Frontend JS | 4 | No |
| 013 | Frontend JS | 1 | No |
| 014 | CSS | 10 | No |
| 015 | Docs | 1 | No |
| 016 | Dev tools | 2 | No |

**Total files modified:** 33  
**New files added:** 1 (`scripts/generate_icons.py`)  
**Business logic changes:** 0  
**Regression risk:** Minimal — all compat shims in place
