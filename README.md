<p align="center">
  <img src="docs/favicon.svg" alt="Ghost Notes" width="96" height="96" />
</p>

<h1 align="center">Ghost Notes · Ubuntu</h1>

<p align="center"><b>Your notes stay on your screen. Your audience sees what is behind them.</b></p>

<p align="center">
  <a href="https://github.com/Nandith-0777/ghost-notes-ubuntu/actions/workflows/ci.yml"><img src="https://github.com/Nandith-0777/ghost-notes-ubuntu/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu 24.04 LTS" />
  <img src="https://img.shields.io/badge/status-experimental-8a63d2" alt="Experimental" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="Apache 2.0" /></a>
</p>

An experimental Ubuntu integration for [Ghost Notes / Invisible Notes](https://github.com/navyabijoy/invisible-notes): floating notes with workspaces, formatting, encrypted local storage, click-through mode and per-note screen-sharing controls.

## Current support

**Verified environment:** Ubuntu **24.04.5 LTS**, default GNOME **46**, Mutter **`46.2-1ubuntu0.24.04.18`**, a Wayland session with the app running through XWayland. Testing used a VM with software rendering, one monitor and scale 1.

- **Google Meet:** invisibility verified manually in the Ubuntu VM.
- **Monitor and area capture:** real Mutter/PipeWire tests show the live background instead of private notes. The sharing toggle makes a note visible again.
- **Ghost mode:** the note body passes clicks through; the toolbar and resize edges remain interactive. Turning ghost mode off with a real mouse click was verified during an active capture stream.
- **Storage:** the normal profile uses GNOME libsecret encryption.
- **Regression tests:** 132 passed, 7 skipped, 0 failed.

**This is an experimental preview, not a universal Ubuntu installer.** Other Ubuntu releases and Mutter revisions are not yet supported. Zoom, physical GPU capture paths, multiple monitors and fractional scaling still need testing. Direct X11/KMS capture and ordinary screenshots bypass this exclusion. The Notes Manager remains visible.

## See the difference

These images use only a synthetic public note and test background.

| Your display                                                                        | Screen-sharing capture                                                                               |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| ![Private note visible locally](validation/ubuntu-gnome-20261112/local-display.png) | ![Capture showing the background behind the note](validation/ubuntu-gnome-20261112/shared-frame.png) |

[Read the capture tests, pixel comparisons and rollback results](validation/ubuntu-gnome-20261112/README.md).

## Ubuntu installer preview

An amd64 `.deb` installer has passed VM installation testing for the exact Ubuntu/Mutter target
above. It bundles Electron and the prebuilt invisibility companion, installs
runtime dependencies through Ubuntu’s package manager, and adds Ghost Notes to
the app launcher. No Node.js, npm, Git or compiler is required on the target
machine. Restart Ubuntu once after installation. The preview refuses unsupported
compositor versions and restores the original library on removal.

[Installer build, install and removal details](packaging/ubuntu/README.md).
[Clean-VM package test results](validation/ubuntu-deb-20261113/README.md).

## Run the app for development

```sh
git clone https://github.com/Nandith-0777/ghost-notes-ubuntu.git
cd ghost-notes-ubuntu
npm ci
npm start
```

**These commands run the app; they do not enable invisibility on stock Ubuntu.** Capture exclusion requires the matching compositor companion described below. Enabling it changes a system Mutter library and requires restarting the desktop session, so save your work first.

## Enable the experimental integration

Read the [GNOME integration guide](integrations/gnome-capture/README.md) and [rollback instructions](integrations/gnome-capture/ROLLBACK.md). The source build/activation scripts target the dedicated development VM. The binary package uses separate, package-managed installation and removal hooks. The stock library is retained, and rollback was tested.

Ubuntu uses a modified Mutter compositor that omits private note windows from marked screen-capture paints while drawing them normally on your display. It also avoids copying the physical screen framebuffer into the capture. The app verifies the companion’s version, library hash and active session before reporting protection available. A compositor update requires rebuilding and revalidation.

## Note controls

- **Ghost:** enable click-through on the note body. The toolbar stays usable. This controls mouse interaction.
- **Pin:** keep the note above other apps. Ghost mode temporarily keeps it on top, so pin changes are locked until ghost mode is off.
- **Monitor-and-arrow:** explicitly include that note in screen sharing. Orange means sharing is enabled; switch it off to request capture exclusion.

General app documentation: [features, workspaces, formatting, backups and shortcuts](README-APP.md). That document also contains inherited Windows, macOS and Omarchy information; the Ubuntu support statement above governs this repository.

## Development and roadmap

```sh
npm run format:check
node --test
```

Next targets are Ubuntu 26.04 LTS, then 22.04 LTS, initially with the default GNOME/Wayland desktop. They are planned work, not current compatibility claims. CI runs app tests; native compositor behavior is validated separately inside the VM.

## Developers and credit

- **Main developer — [Navya Bijoy](https://github.com/navyabijoy):** creator of Ghost Notes / Invisible Notes and the original application.
- **Co-developer — [Nandith Narayanan](https://github.com/Nandith-0777):** Linux and Omarchy integration, Ubuntu GNOME capture integration, interface and input improvements.

This repository preserves the original Git history and attribution. Mutter source modifications retain upstream licensing and attribution; see the integration guide. The app is licensed under [Apache 2.0](LICENSE).
