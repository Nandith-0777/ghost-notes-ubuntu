# Prototype rollback

The Ubuntu VM disk has an offline internal snapshot named
`before-gnome-capture`. The original Omarchy installation is separate.

## Restore the standard Ubuntu compositor

Inside the VM, run:

```sh
sudo bash ~/ghost-notes-gnome/disable-in-vm.sh
sudo systemctl restart gdm3
```

The helper verifies the installed prototype hash, removes only its own core
library override, and uses `dpkg-divert` to restore Ubuntu's retained original:
`/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0.distrib`.
It also removes this user-service override:
`~/.config/systemd/user/org.gnome.Shell@wayland.service.d/ghost-notes-capture.conf`.
An SSH connection to the guest provides a rollback path if its desktop fails.
Restarting GDM closes that VM's graphical session; save work first.

Build output under `~/ghost-notes-gnome/stage` is inactive. An earlier private
library-path experiment left files under `/opt/ghost-notes/mutter`; those files
are inactive too. The active override explicitly unsets those private library
search paths to avoid duplicate Clutter type registration.

## Restore the entire pre-experiment disk

Power off the VM first. Then run on the host:

```sh
qemu-img snapshot -a before-gnome-capture /home/nandith/Work/ghost-notes-ubuntu-vm/ubuntu.qcow2
```

This restores the complete old disk and discards later guest changes. The
library rollback above preserves later guest data and is the preferred option.
