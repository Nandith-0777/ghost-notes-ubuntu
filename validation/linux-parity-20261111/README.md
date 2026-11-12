# Per-note screen-sharing visibility — 11 November 2026

- Live Omarchy 4.5.0-3 / Hyprland 0.56.2, supported exact build.
- Disposable profile: toolbar toggled private → shared → private.
- `no_screen_share` changed true → false → true; initial window identity remained unchanged.
- Configuration reload preserved the selected shared mode; configuration errors were empty.
- Wrong note IDs and non-boolean sharing IPC requests were rejected.
- Capture comparison used a temporary GN-TEST-SHARING headless output and public patterned fixture only. Private and private-again captures matched the background-only baseline exactly; shared capture differed. The native companion processed four capture frames.
- A saved shared note reopened after app restart with the toolbar active, stable initial identity, and capture exclusion disabled.
- Source tests: 129 passed, 7 skipped, 0 failed. Bundled app and installer tests: 142 passed, 7 skipped, 0 failed.
- No new Google Meet/Zoom call, physical Windows test, or physical macOS test was performed for this change. macOS ScreenCaptureKit can bypass Electron protection.

The disposable capture images contained only test content and were not committed.
