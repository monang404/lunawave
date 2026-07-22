"""
Module: server.handlers

Purpose:
    Shared, typed accessors for values stashed on `request.app[...]` by
    server.app.create_app(). Handlers should use these instead of raw
    `request.app[KEY]` lookups so the type of each value is explicit
    (T3.7 — dulu rencana ini ditulis untuk `request.app["db"]`, tapi
    setelah T2.2 memecah `Database` God Facade, tidak ada lagi key
    tunggal "db" — sudah jadi beberapa key spesifik: "repos", "tracks",
    "conn", dst. Accessor di bawah menutupi semua key itu).

Responsibilities:
    - Provide get_*() helper functions with return type annotations.
    - Import and re-export web.AppKey constants from server.app.

Depends on:
    - core.ports
    - core.state
    - engine.playback.controller
    - persistence
    - server.connection_manager

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop) — pure accessors, no shared mutable state.
"""

from typing import TYPE_CHECKING

from aiohttp import web

from core.ports import MediaExtractorPort, TrackRepositoryPort
from core.state import AppState
from server.app import CONN, MANAGER, PLAYBACK_CONTROLLER, REPOS, STATE, TRACKS, YTDLP

if TYPE_CHECKING:
    from engine.playback.controller import PlaybackController
    from persistence import Repositories
    from server.connection_manager import ConnectionManager


def get_repos(request: web.Request) -> "Repositories":
    return request.app[REPOS]


def get_tracks_repo(request: web.Request) -> TrackRepositoryPort:
    return request.app[TRACKS]


def get_conn(request: web.Request):
    return request.app[CONN]


def get_state(request: web.Request) -> AppState:
    return request.app[STATE]


def get_manager(request: web.Request) -> "ConnectionManager":
    return request.app[MANAGER]


def get_ytdlp(request: web.Request) -> MediaExtractorPort:
    return request.app[YTDLP]


def get_playback_controller(request: web.Request) -> "PlaybackController":
    return request.app[PLAYBACK_CONTROLLER]
