from unittest.mock import MagicMock

from engine.mpv_controller import MpvController


def test_mpv_controller_initialization():
    bus_mock = MagicMock()
    # If time module is not imported properly, this might fail or the module wouldn't load
    controller = MpvController(event_bus=bus_mock)
    assert controller is not None
