# Ubuntu GNOME capture prototype

Target: Ubuntu 24.04, GNOME Shell 46, Mutter **46.2-1ubuntu0.24.04.18**,
Wayland desktop with Ghost Notes running on XWayland. The implementation is
experimental. The current setup scripts are restricted to the dedicated test VM.

## Verified behavior

Real Mutter/PipeWire monitor and area captures omit a private note while the
note stays visible locally. Clicking the existing monitor-and-arrow button
includes that note in capture; clicking again excludes it. Captured private
frames matched the note-free live background exactly in the controlled test.

The manager remains visible. Direct X11 texture reads, GPU/KMS recording, and
ordinary GNOME screenshot paths are outside this integration's scope. Live
Google Meet/Zoom calls, additional graphics hardware, fractional scaling, and
multiple monitors still need validation.

## Capture architecture

Mutter can copy physical-display pixels directly into a DMA-BUF screencast.
Filtering only offscreen paints would miss that path. The patch marks capture
paints and forces a clean capture scene for monitor streams when
`GHOST_NOTES_CAPTURE_EXCLUSION=1`. A native actor effect omits the exact private
note class/title only from those marked paints. The active effect also prevents
that note from occluding the content behind it during Mutter's culling pass.
The existing sharing button changes the title, so explicitly shared notes paint
normally. CPU note-window capture clears its pixels; GPU note-window capture
uses a marked paint. Those explicit note-window streams have not yet been tested.

## Build and activation in the test VM

`prepare-build-in-vm.sh` enables Ubuntu source repositories, aligns the stock
Mutter maintenance revision with its available signed source, installs build
dependencies, and runs `build-user.sh`. The result is staged under
`~/ghost-notes-gnome/stage/usr` with a library hash manifest. Building alone does
not activate the prototype.

`enable-in-vm.sh` installs only the patched Mutter core library with
`dpkg-divert`, retaining the original Ubuntu library as `.distrib`. Standard
Clutter/Cogl libraries and typelibs stay in use; this avoids loading duplicate
GObject types through GNOME Shell's compiled-in library search paths. A user
service override enables the capture flag only for the Wayland Shell service.
Restarting GDM activates it. See [ROLLBACK.md](ROLLBACK.md) before enabling.

`status.py` verifies the root-owned manifest, exact package revision, library
hash, opt-in Wayland process, and loaded library inode. The app claims protection
only after that verification; system updates that invalidate the revision cause
it to report unsupported until the companion is rebuilt.

`capture-frame.py` obtains a real PipeWire frame through Mutter's screencast
API. `compare-private-shared.mjs` checks private/shared/private monitor and area
frames against a fixed public background. Fixture scripts use synthetic notes
and an isolated profile; their basic password-store setting is only for those
synthetic fixtures. The normal profile continues using its encrypted keyring.

Source architecture references: GNOME/mutter tag 46.2 and Ubuntu's matching
source package, especially `meta-screen-cast-monitor-stream-src.c`,
`meta-screen-cast-area-stream-src.c`, `meta-window-actor.c`, and `meta-cullable.c`.
Modified upstream files retain Mutter's licensing and attribution.
