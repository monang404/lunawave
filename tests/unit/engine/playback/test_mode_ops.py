"""
Module: tests.unit.engine.playback.test_mode_ops

Purpose:
    Unit tests for playback mode operations and toggles.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.event_bus
    - core.state
    - engine.playback.mode_ops
    - tests.fakes.fake_audio_player

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio

import pytest

from core.event_bus import EventBus
from core.state import AppState, AudioOutput, PlaybackMode, PlayerStatus
from engine.playback.mode_ops import ModeOps
from tests.fakes.fake_audio_player import FakeAudioPlayer


class MockArtistSelector:
    def __init__(self):
        self.reset_rotation_called = False

    def reset_rotation(self):
        self.reset_rotation_called = True


class MockRadioMode:
    def __init__(self):
        self.deactivated = False
        self.artist_selector = MockArtistSelector()

    async def on_deactivated(self):
        self.deactivated = True


@pytest.fixture
def setup_mode_ops():
    state = AppState()
    bus = EventBus()
    lock = asyncio.Lock()
    mpv = FakeAudioPlayer()
    radio_mode = MockRadioMode()
    ops = ModeOps(state, bus, lock, mpv, radio_mode)
    return ops, state, mpv, radio_mode


@pytest.mark.asyncio
async def test_set_mode_to_radio(setup_mode_ops):
    ops, state, mpv, radio = setup_mode_ops

    should_activate = await ops.set_mode(PlaybackMode.RADIO)
    assert should_activate is True
    assert state.playback_mode == PlaybackMode.RADIO
    assert state.status == PlayerStatus.LOADING


@pytest.mark.asyncio
async def test_set_mode_from_radio(setup_mode_ops):
    ops, state, mpv, radio = setup_mode_ops
    state.playback_mode = PlaybackMode.RADIO

    should_activate = await ops.set_mode(PlaybackMode.QUEUE)
    assert should_activate is False
    assert state.playback_mode == PlaybackMode.QUEUE
    assert radio.deactivated is True
    assert mpv.is_playing is False
    assert state.status == PlayerStatus.IDLE


@pytest.mark.asyncio
async def test_randomize_radio(setup_mode_ops):
    ops, state, mpv, radio = setup_mode_ops
    state.playback_mode = PlaybackMode.RADIO

    should_fetch, seed = await ops.randomize_radio({"seed_artist": "Artist A"})
    assert should_fetch is True
    assert seed == "Artist A"
    assert radio.artist_selector.reset_rotation_called is True
    assert state.status == PlayerStatus.LOADING


@pytest.mark.asyncio
async def test_set_output(setup_mode_ops):
    ops, state, mpv, radio = setup_mode_ops
    state.volume = 50

    await ops.set_output(AudioOutput.BROWSER)
    assert state.audio_output == AudioOutput.BROWSER
    assert mpv.volume == 0

    await ops.set_output(AudioOutput.DEVICE)
    assert state.audio_output == AudioOutput.DEVICE
    assert mpv.volume == 50


@pytest.mark.asyncio
async def test_toggle_sponsorblock(setup_mode_ops):
    ops, state, mpv, radio = setup_mode_ops

    await ops.toggle_sponsorblock(True)
    assert state.sponsorblock_active is True
