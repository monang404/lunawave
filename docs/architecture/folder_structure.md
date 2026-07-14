# Folder Structure

← [architecture/overview.md](overview.md) | [Blueprint.md](../Blueprint.md)

Legenda: **✅** tidak berubah · **🆕** file/folder baru · **🔧** opsional

---

## Backend

```
lunawave/
├── main.py                              wiring saja, ~80 baris
├── config.py                            config murni, tanpa password gen
├── config_security.py                   🆕 password generation
├── start.py                             ✅
├── start.sh                             ✅
├── start.bat                            ✅
├── requirements.txt
├── requirements-dev.txt                 🆕 pytest, ruff, mypy, bandit, pip-audit, import-linter
├── pyproject.toml                       🆕 [tool.coverage] [tool.mypy] [tool.bandit] [tool.ruff]
├── .importlinter                        🆕 aturan arah dependency
│
├── core/
│   ├── state.py                         ✅
│   ├── event_bus.py                     ✅
│   ├── command_bus.py                   ✅
│   ├── commands.py                      🆕 konstanta CMD_* dipisah dari command_bus
│   ├── events.py                        ✅
│   ├── ports.py                         ✅
│   ├── security.py                      ✅
│   ├── task_utils.py                    ✅
│   ├── observability.py                 ✅
│   ├── exceptions.py                    ✅
│   └── log_config.py                    ✅
│
├── adapters/                            🆕 adapter ke sistem eksternal
│   ├── mpv/
│   │   ├── connection.py                🆕 connect/reconnect/close socket
│   │   ├── ipc.py                       🆕 send command, pending futures
│   │   ├── observer.py                  🆕 event loop → publish ke bus
│   │   └── __init__.py                  🆕 facade MpvController
│   └── ytdlp/
│       ├── searcher.py                  🆕 search(query) → TrackInfo
│       ├── resolver.py                  🆕 get_stream_url(video_id)
│       ├── downloader.py                🆕 download_mp3 + progress hook
│       └── __init__.py                  🆕 facade YtDlpClient
│
├── engine/
│   ├── command_router.py                ✅
│   ├── download_manager.py              ✅
│   ├── queue_manager.py                 ✅
│   ├── volume_service.py                ✅
│   ├── radio/                           🆕 pecahan radio_engine.py
│   │   ├── prefetcher.py
│   │   ├── artist_selector.py
│   │   ├── track_filter.py              akar bug radio mode
│   │   ├── engine.py                    orchestrator, export RadioMode
│   │   └── __init__.py
│   └── playback/
│       ├── controller.py                slim, orchestrator saja
│       ├── queue_ops.py                 🆕 pecahan controller.py
│       ├── mode_ops.py                  🆕 pecahan controller.py
│       └── track_loader.py              ✅
│
├── persistence/                         🆕 pecahan cache/db.py
│   ├── db.py
│   ├── track_repo.py
│   ├── session_repo.py
│   ├── artist_repo.py
│   ├── genre_repo.py
│   ├── library_repo.py
│   ├── schema.sql                       pindah dari cache/schema.sql
│   └── __init__.py                      facade Database, backward-compat
│
├── cache/
│   ├── resolver.py                      ✅
│   └── mp3/                             ✅
│
├── server/
│   ├── app.py                           ✅
│   ├── middleware.py                    ✅
│   ├── serializers.py                   ✅
│   ├── connection_manager.py            🆕 cut dari websocket.py
│   ├── handlers/
│   │   ├── auth.py                      ✅
│   │   ├── http.py                      ✅
│   │   ├── event_listeners.py           ✅
│   │   ├── websocket.py                 slim: lifecycle + routing saja
│   │   ├── ws_playback.py               🆕
│   │   ├── ws_queue.py                  🆕
│   │   ├── ws_discovery.py              🆕
│   │   └── ws_download.py               🆕
│   └── services/
│       ├── broadcast_service.py         ✅
│       └── stream_prefetch.py           ✅
│
├── services/
│   └── discover_service.py              ✅
│
├── plugins/
│   ├── lyrics_fetcher.py                🆕 pecahan lyrics.py
│   ├── lyrics_parser.py                 🆕
│   ├── lyrics_sync.py                   🆕
│   ├── notifications.py                 ✅
│   └── sponsorblock.py                  ✅
│
├── launcher/
│   ├── process.py                       ✅
│   ├── network.py                       ✅
│   ├── updater.py                       ✅ (stub)
│   └── gui/                             🆕 pecahan gui.py (756 baris)
│       ├── app.py
│       ├── ui_builder.py
│       ├── status_panel.py
│       ├── log_panel.py
│       ├── dep_checker.py
│       └── __init__.py
│
├── automation/
│   ├── doctor.py                        orchestrator health check
│   ├── run_all.py                       entry point semua generator + checks
│   ├── find_owner.py                    lookup ownership modul/class/fungsi
│   ├── architecture_lint.py             validasi import boundary
│   ├── generate_file_index.py           generate FILE_INDEX.md
│   ├── generate_report.py               update statistik REPORT.md
│   ├── verify_docs.py                   thin CLI → verify_docs/
│   ├── verify_security.py               cek .gitignore credential & DB
│   ├── verify_structure.py              cek file besar & pending items
│   ├── verify_docs/                     package: helpers, checks_*, render
│   ├── shared/                          package: check_result, skip_dirs, generated_block
│   └── archive/                         scripts lama (tidak aktif)
│
├── data/
│   ├── artists_enriched.json            ✅  data statis, source of truth artis
│   └── lunawave.db                      ✅  file database runtime (di-gitignore)
│
├── scratch/                             di luar arsitektur — biarkan
│   └── check_db.py
│
└── docs/                                ← dokumentasi hub
```

---

## Test

```
tests/
├── conftest.py                          fixture bersama: event loop, temp SQLite
├── fakes/
│   ├── fake_audio_player.py             AudioPlayerPort
│   ├── fake_media_extractor.py          MediaExtractorPort
│   ├── fake_lyrics_provider.py          LyricsProvider
│   └── fake_sponsorblock_provider.py    SponsorBlockProvider
├── unit/
│   ├── test_main.py
│   ├── test_config.py
│   ├── test_config_security.py
│   ├── core/                            (11 file)
│   ├── adapters/
│   │   ├── mpv/                         (3 file)
│   │   └── ytdlp/                       (3 file)
│   ├── engine/
│   │   ├── test_command_router.py
│   │   ├── test_download_manager.py
│   │   ├── test_queue_manager.py
│   │   ├── test_volume_service.py
│   │   ├── radio/                       (4 file — test_track_filter.py prioritas tertinggi)
│   │   └── playback/                    (4 file)
│   ├── persistence/                     (6 file)
│   ├── cache/
│   │   └── test_resolver.py
│   ├── server/
│   │   ├── test_app.py
│   │   ├── test_middleware.py
│   │   ├── test_serializers.py
│   │   ├── test_connection_manager.py
│   │   ├── handlers/                    (8 file)
│   │   └── services/                    (2 file)
│   ├── services/
│   │   └── test_discover_service.py
│   ├── plugins/                         (5 file)
│   ├── launcher/
│   │   ├── test_process.py
│   │   ├── test_network.py
│   │   ├── test_updater.py
│   │   └── gui/                         (3 file — app.py & ui_builder.py: manual QA)
│   └── automation/
│       └── test_export_to_sqlite.py     (opsional)
├── integration/
│   ├── test_websocket_flow.py
│   ├── test_playback_flow.py
│   ├── test_radio_flow.py
│   └── test_download_flow.py
└── frontend/                            opsional, prioritas rendah
    ├── utils/
    │   └── format.test.js
    ├── test_store.test.js
    └── test_ws-routing.test.js
```

Detail testing → [testing/unit_testing.md](../testing/unit_testing.md)

---

## Frontend

```
web/static/
├── index.html                           ✅ tidak dipecah
├── manifest.json                        ✅ audit isi
├── sw.js                                ✅ audit precache list
│
├── js/
│   ├── config.js                        ✅
│   ├── store.js                         ✅
│   ├── dom.js                           ✅
│   ├── main.js                          ✅
│   ├── portal.js                        ✅
│   ├── ws.js                            slim ~190 baris (render logic dipindah)
│   ├── audio/                           🆕 pecahan audio.js
│   │   ├── playback-sync.js
│   │   └── visualizer.js
│   ├── utils/                           🆕 pecahan utils.js
│   │   ├── format.js
│   │   └── toast.js
│   ├── events/
│   │   ├── index.js                     ✅
│   │   ├── queue-events.js              ✅
│   │   ├── lyrics-events.js             ✅
│   │   ├── settings-events.js           ✅
│   │   ├── transport-events.js          🆕 pecahan player-events.js
│   │   ├── progress-events.js           🆕
│   │   ├── search-input-events.js       🆕
│   │   ├── action-modal-events.js       🆕
│   │   ├── click-delegation-events.js   🆕
│   │   └── keyboard-shortcut-events.js  🆕
│   ├── render/
│   │   ├── player.js                    ✅
│   │   ├── now-playing.js               ✅
│   │   ├── lyrics.js                    ✅
│   │   ├── search.js                    ✅
│   │   ├── queue.js                     ✅
│   │   ├── discover-tab.js              🆕 pecahan discover.js
│   │   ├── radio-tab.js                 🆕
│   │   └── full-state.js                🆕 pindahan dari ws.js
│   ├── services/
│   │   └── auth.js                      ✅
│   └── platform/
│       ├── keyboard.js                  ✅
│       ├── touch.js                     ✅
│       └── viewport.js                  ✅
│
├── css/
│   ├── portal.css                       ✅
│   ├── tokens.css                       ✅
│   ├── base/                            ✅
│   ├── layout/                          ✅
│   ├── platform/                        ✅
│   ├── components/
│   │   ├── toasts.css                   ✅
│   │   ├── lyrics.css                   ✅
│   │   ├── queue.css                    ✅
│   │   ├── search.css                   ✅
│   │   ├── settings-sheet.css           ✅
│   │   ├── player-controls.css          ✅
│   │   ├── player-bar/                  🔧 hanya kalau cascade bisa dipisah bersih
│   │   │   ├── layout.css
│   │   │   ├── progress.css
│   │   │   └── controls.css
│   │   └── cards/                       🔧 prioritas rendah
│   │       ├── discover-cards.css
│   │       └── search-cards.css
│   └── vendor/
│       ├── tabler-icons.min.css         ✅
│       └── fonts/                       ✅
│
└── icons/
    ├── icon-192.png                     ✅
    └── icon-512.png                     ✅
```

---

## Root (Open Source)

```
lunawave-main/
├── README.md                            update: instruksi run-from-zero akurat
├── LICENSE                              🆕 MIT
├── CHANGELOG.md                         🆕
├── CONTRIBUTING.md                      🆕
├── SECURITY.md                          🆕
├── .gitignore                           ✅
├── .editorconfig                        🆕
├── .pre-commit-config.yaml              🆕
└── .github/
    ├── workflows/
    │   ├── ci.yml                       update: jadikan jujur
    │   └── release.yml                  🆕 auto-release on tag
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md                🆕
    │   └── feature_request.md           🆕
    └── PULL_REQUEST_TEMPLATE.md         🆕
```

---

## Dokumen Terkait

- [architecture/backend.md](backend.md) — Detail tanggung jawab tiap modul backend
- [architecture/frontend.md](frontend.md) — Detail tanggung jawab tiap modul frontend
- [development/project_structure.md](../development/project_structure.md) — Peta risiko perubahan
