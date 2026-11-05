# Linux parity work — 5 November 2026

Implemented and installed on this machine: a Hyprland companion plugin for true
capture omission and fullscreen pinning, plus Linux ghost-mode input recovery.
This is a substantial improvement on the October black-mask implementation. It
is not complete parity across all Linux desktops and recording APIs.

## Environment

Omarchy 4.0.6, Linux 7.2.15-1-omarchy, Hyprland v0.56.2
(`efb50993780079460b0cbed1363e2166a2de1d9f`), Electron 43.6.0,
xdg-desktop-portal-hyprland 1.4.1, Intel graphics.

Tests used a nested compositor, disposable notes under `/tmp`, a public
checkerboard background and headless outputs. The real notes database was not
opened or captured. The companion was subsequently installed into the real
user's existing Ghost Notes integration; `hyprctl reload` and `configerrors`
were clean, and `ghostnotes:status -j` reported `compositor-omit`.

## Verified

| Check                                                                                                                                                               | Result                                                                                                          | Evidence                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Full-output capture at 100%                                                                                                                                         | Protected capture matches note-free background pixel for pixel                                                  | `capture-100.json`                                    |
| Full-output and region capture at 125%                                                                                                                              | Zero differing pixels                                                                                           | `capture-125.json`                                    |
| Rotated output at 125%                                                                                                                                              | Zero differing pixels for full-output and region capture                                                        | `capture-rotated.json`                                |
| Pinned note above focused fullscreen app                                                                                                                            | Unprotected control contains note; protected full/region capture has zero difference from background            | `capture-fullscreen.json`                             |
| Ghost input at 100% and 125%, including fullscreen                                                                                                                  | Virtual-pointer body click reaches underlying app, toolbar hover recovers input, toolbar click exits ghost mode | `scripts/validate-ghost-pointer.mjs`                  |
| Editor, color, opacity, text size, monospace, bubble collapse/restore, PNG paste, pin/ghost state, new-note command, manager shortcut, workspace/theme, hide/reopen | All 14 smoke checks passed                                                                                      | `desktop-results.json`                                |
| Actual portal recording                                                                                                                                             | Chromium MediaRecorder recorded VP8 video via portal/PipeWire with notes omitted                                | `portal-recording.webm`, `portal-recording-frame.png` |
| Automated tests                                                                                                                                                     | 107 tests: 100 passed, 7 platform skips, 0 failures                                                             | `unit-tests.json`                                     |

The controls disable the privacy rule for disposable notes and require visible
note pixels before accepting omission. Region tests use the same physical
location with the note moved away as their reference. The public fixture's
focus stays constant to avoid treating a focus-border change as a privacy bug.

The input test uses the Wayland virtual-pointer protocol through the compositor,
not DOM mouse events or direct calls to the ghost-mode handler. It verifies
actual click delivery, although it does not test a physical hardware mouse.

The input checks also pass with Omarchy's `xwayland:force_zero_scaling = true`
at 125% monitor scaling after a clean app launch. Recovery converts compositor
window geometry to Electron client coordinates, accounting for their different
origins and sizes. The companion exposes only geometry, not note content.

## Recording compatibility found during testing

The isolated portal initially negotiated an Intel DMA-BUF modifier that neither
GPU Screen Recorder nor Chromium could consume successfully. GPU Screen
Recorder then rejected the shared-memory fallback; that recorder run failed.
This is not recorded as a successful privacy test.

Setting `screencopy:force_shm = true` **only in the isolated portal configuration**
allowed Chromium's real portal capture to work. The attached VP8 recording is
1280×720, approximately 2.4 seconds long; its decoded frame was visually checked
and shows the checkerboard through the protected note area. The private D-Bus
session used a fixed picker selecting only the disposable `GN-TEST` output.
No real-desktop picker or screen was captured. The real portal configuration
and Omarchy's recorder defaults were not changed.

Omarchy's installed recorder normally uses direct GPU/KMS capture. Its optional
`OMARCHY_SCREENRECORD_USE_PORTAL=true` path requires compatible DMA-BUF capture;
its explicit `--fullscreen` option still chooses KMS. Therefore the default
Omarchy recording workflow is **not** claimed to exclude notes. A supported
portal consumer such as the tested Chromium path must be used instead.

Direct packaged launches now override inherited desktop-wide Wayland defaults
with XWayland when `DISPLAY` is available. If Chromium has already selected
Wayland, the app relaunches once with an explicit early X11 flag before opening
the note store, rather than changing an initialized GPU backend in place. An explicit `--ozone-platform=wayland`
argument remains honored. This avoids relying on desktop-entry flags for the
tested positioning, bubble and input behavior.

The final unpacked packaged binary was launched directly without an Ozone flag.
It selected XWayland, passed the force-zero-scaling pointer checks, opened the
manager, and preserved both visible and hidden disposable notes with
`gnome_libsecret` encryption active. See `packaged-results.json`.

## Remaining work before claiming complete parity

- Fix or work around portal DMA-BUF negotiation with compatible GPU consumers;
  validate a production meeting application and the user's recording workflow.
- Direct GPU/KMS and direct X11/window-texture consumers bypass compositor
  omission. The app cannot make those capture the background while the same
  physical display contains a visible note through an Electron setting.
- GNOME, KDE, other compositors and other Hyprland builds require their own
  integration and tests. Native Wayland positioning/bubble parity is unchanged.
- HDR, multi-stream/high-refresh recording, session-lock transitions, protected
  popups/layers and long-running capture performance need dedicated tests.

The first exploratory plugin attempt aborted the disposable nested compositor
because its weak session pointer referred to a unique-owned object. The fix
keeps a weak reference rather than locking it to a shared reference. Subsequent
capture and input tests passed. The real compositor was not affected by that
test crash. The companion remains tied to the exact compositor build hash.
