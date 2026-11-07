# Laptop validation — 7 November 2026

The user confirmed that the mouse-sticking issue is fixed and that Google Meet
and Zoom sharing were verified on this laptop. These are user-reported results;
meeting client versions, capture selections, and recordings were not supplied.
They do not establish compatibility with every capture mode or another laptop.

The native companion was re-enabled at the user's request. The running
Hyprland build is 0.56.2, commit
`efb50993780079460b0cbed1363e2166a2de1d9f`.
`hyprctl configerrors` was clean and `ghostnotes:status -j` reported
`compositor-omit` after enabling the companion.

Direct GPU/KMS and direct X11 capture remain outside the companion's protection.
