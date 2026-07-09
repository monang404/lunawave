# REBRANDING_REPORT.md — LunaWave Sprint 2.1

**Date:** 2026-07-09  
**Sprint:** 2.1 — Visual Rebranding Only  
**Objective:** Replace all legacy identities (YTGUI, ytgui, bagas.fm, YT Termux Player) with **LunaWave**. Zero regressions in business logic, APIs, or backend.

---

## ✅ Syntax Verification

All modified Python files pass `python -m py_compile` with **zero errors**.

```
config.py              ✅ OK
main.py                ✅ OK
start.py               ✅ OK
core/state.py          ✅ OK
core/exceptions.py     ✅ OK
core/observability.py  ✅ OK
engine/radio_engine.py ✅ OK
plugins/notifications.py ✅ OK
server/handlers/http.py  ✅ OK
```

---

## 📂 Files Changed

### Python — Backend / Config

| File | Change |
|---|---|
| `config.py` | DB path → `lunawave.db`; socket name → `mpv-lunawave`; env vars primary → `LUNAWAVE_*` |
| `main.py` | Log filename → `lunawave.log`; CLI startup banner → LunaWave |
| `start.py` | Window title, Labels, Popup text → LunaWave; subprocess env primary → `LUNAWAVE_*` |
| `core/state.py` | Docstring: "YTGUI V2" → "LunaWave" |
| `core/exceptions.py` | Docstring updated to LunaWave |
| `core/observability.py` | Prometheus metric `ytgui_events_total` → `lunawave_events_total` |
| `engine/radio_engine.py` | Error message CLI example path `ytgui.db` → `lunawave.db` |
| `plugins/notifications.py` | `NOTIFICATION_ID` → `lunawave_nowplaying`; fallback title → "LunaWave" |
| `server/handlers/http.py` | Metrics token env var primary → `LUNAWAVE_METRICS_TOKEN` |

### Shell / Batch Scripts

| File | Change |
|---|---|
| `start.bat` | ASCII art banner → LunaWave; env vars primary → `LUNAWAVE_*` |
| `start.sh` | ASCII art banner → LunaWave; env vars primary → `LUNAWAVE_*` |

### Web Frontend — HTML / JS

| File | Change |
|---|---|
| `web/static/index.html` | `<title>`, meta description, portal heading, favicon links |
| `web/static/manifest.json` | `name`, `short_name`, `description` |
| `web/static/sw.js` | Cache version string, comment headers |
| `web/static/js/utils.js` | `safeStorage` upgraded with **legacy key migration** (auto-migrates `ytgui_*` → `lunawave_*` on first read) |
| `web/static/js/ws.js` | Storage keys: `lunawave_session_token`, `lunawave_user_role`, `lunawave_audio_output` |
| `web/static/js/portal.js` | Storage key read: `lunawave_user_role` |
| `web/static/js/services/auth.js` | Storage key removes on logout: `lunawave_*` |
| `web/static/js/events/index.js` | Storage key set: `lunawave_user_role` |

### Web Frontend — CSS

| File | Change |
|---|---|
| `web/static/css/tokens.css` | Header comment: `BAGAS.FM` → `LunaWave` |
| `web/static/css/portal.css` | Header comment |
| `web/static/css/components/player-bar.css` | Header comment |
| `web/static/css/layout/nav.css` | Header comment |
| `web/static/css/layout/grid.css` | Header comment |
| `web/static/css/layout/app-shell.css` | Header comment |
| `web/static/css/base/typography.css` | Header comment |
| `web/static/css/base/reset.css` | Header comment |
| `web/static/css/base/animations.css` | Header comment |
| `web/static/css/platform/mobile.css` | Header comment |

### Documentation & Scripts

| File | Change |
|---|---|
| `README.md` | Title, description, repo URLs, env var names, feature bullets, log filename |
| `scratch/check_db.py` | DB path → `lunawave.db` |
| `data/export_to_sqlite.py` | DB filename → `lunawave.db` |
| `scripts/generate_icons.py` | New file — LunaWave icon generator |

---

## 🔁 Intentional Backward-Compatibility Shims

These `YTGUI_*` references are **intentionally preserved** to ensure existing deployments continue working without reconfiguration:

| Location | Pattern | Reason |
|---|---|---|
| `config.py:44-56` | `os.environ.get("LUNAWAVE_*", os.environ.get("YTGUI_*"))` | Env var fallback chain |
| `start.bat:23-26` | `if defined YTGUI_* set LUNAWAVE_*=...` | Windows legacy env bridge |
| `start.sh:6-10` | `${LUNAWAVE_*:-${YTGUI_*:-default}}` | Shell legacy env bridge |
| `start.py:28,587-588` | Port/host legacy fallback + subprocess shim | Config + subprocess compat |
| `server/handlers/http.py:150` | Metrics token fallback | HTTP handler compat |
| `web/static/js/utils.js:13,30` | `safeStorage` legacy key migration | Browser localStorage compat |
| `README.md:7` | "sebelumnya YT Termux Player/bagas.fm" | Historical attribution (correct) |

---

## 🚫 Not Changed (As Required)

- Business logic (playback, queue, search, download, radio)
- Backend API routes and WebSocket messages
- Database schema and data
- Event/Command bus architecture
- State management structure
- Service and repository layers

---

## 🎯 Result

**Application identity is now 100% LunaWave** at all user-visible surfaces while maintaining full backward compatibility for existing configurations.
