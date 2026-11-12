# Ubuntu GNOME capture validation — 12 November 2026

Experimental integration tested in the `ghost-notes-ubuntu` VM: Ubuntu 24.04.5 LTS, GNOME Shell 46.0, Mutter `46.2-1ubuntu0.24.04.18`, Wayland, software rendering, 1280 × 800 at scale 1.

The note stays visible on the local display while the real Mutter ScreenCast/PipeWire stream shows the live content behind it. Turning on the note’s sharing button makes it appear in the stream; turning it off hides it again.

| View                                   | Public test fixture                 |
| -------------------------------------- | ----------------------------------- |
| Local display, private note visible    | ![Local display](local-display.png) |
| PipeWire capture, private note omitted | ![Captured frame](shared-frame.png) |

## Pixel checks

A 360 × 220 note covers 79,200 pixels. Each capture was compared against the same live background with the note hidden. Both full-monitor and rectangular-area streams were tested.

| Integration                            | Private | Shared | Private again |
| -------------------------------------- | ------: | -----: | ------------: |
| Enabled, monitor and area              |       0 | 79,200 |             0 |
| Stock Ubuntu control, monitor and area |  79,200 | 79,200 |        79,200 |

Values are different pixels within the note region. Zero means the capture exactly matches the unobstructed background. Raw results are in [prototype.json](prototype.json) and [stock-control.json](stock-control.json).

## Other verification

- Disabled the companion, restored the original system library, restarted GNOME and ran the stock control above. The app correctly reported capture protection unavailable.
- Re-enabled the companion, restarted GNOME and repeated successful exclusion tests. The VM is left with the companion enabled.
- App tests on the host and inside Ubuntu: 131 passed, 7 skipped, 0 failed.
- Normal profile uses encrypted GNOME libsecret storage; runtime status is saved in [normal-profile.json](normal-profile.json). Normal startup was restored and debugging ports removed from the running app.
- The fixture and capture tests use synthetic public text, separate from the normal encrypted profile.

## Remaining validation

A live Google Meet/Zoom call inside Ubuntu still needs manual testing. Physical GPU/DMA-BUF capture, multiple monitors, fractional scaling and explicit note-window streams have not been independently tested. Screenshots and direct X11/KMS capture are outside this integration’s scope. This is a VM prototype for the exact Mutter version above, not a general Ubuntu installer.

Implementation, activation and rollback instructions: [GNOME companion](../../integrations/gnome-capture/README.md).
