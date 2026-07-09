# LunaWave Patch Log

## [Sprint 3.2] - Safe Extract Module: start.py → launcher/

### Added
- Created `launcher/` directory module to serve as the new location for internal launcher scripts.
- Extracted and separated `process.py` to handle `ServerProcess` instantiation, lifecycle, and logs stream management.
- Extracted and separated `network.py` for dealing with finding processes on specific ports, checking connections, and freeing system ports.
- Created `gui.py` which houses the `ServerManager` Tkinter logic interface previously located in `start.py`.
- Formed the `__main__.py` entry point wrapper that launches the `gui.py` Tkinter app conditionally on environmental support.
- Stubbed out `updater.py` as an empty module for future OTA update requirements.

### Changed
- `start.py` has been completely hollowed out and converted into a lightweight bootstrap file that safely executes the `launcher/` module functions. This preserves backwards compatibility with `python start.py`.

### Kept Intact
- All core business logic remains identically functioning.
- App startup flow logic and dependencies are completely untouched.
