from main import __version__


def test_version_is_parsed_correctly():
    # It should not be the hardcoded 1.0.0 anymore, but parse from pyproject.toml
    # which is "0.1.0" or whatever is in there.
    assert __version__ != "1.0.0"
    assert "." in __version__
    assert __version__ != "0.0.0-unknown"
