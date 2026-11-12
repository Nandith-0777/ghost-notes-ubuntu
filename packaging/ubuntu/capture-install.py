#!/usr/bin/env python3
"""Activate or restore only the compositor library owned by this package."""
from pathlib import Path
import hashlib
import json
import os
import pwd
import subprocess
import sys
import tempfile

PACKAGE = 'ghost-notes-ubuntu'
LIBRARY = Path('/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0')
BACKUP = Path('/var/lib/ghost-notes/stock') / LIBRARY.name
PAYLOAD = Path('/usr/lib/ghost-notes-ubuntu')
MARKER = Path('/var/lib/ghost-notes/mutter-capture.json')
OVERRIDE = Path('/etc/systemd/user/org.gnome.Shell@wayland.service.d/60-ghost-notes-capture.conf')
UNIT = '[Service]\nEnvironment=GHOST_NOTES_CAPTURE_EXCLUSION=1\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owner():
    return subprocess.check_output(
        ['dpkg-divert', '--listpackage', str(LIBRARY)], text=True
    ).strip()


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.ghost-notes-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def notify_restart():
    for user in Path('/run/user').glob('[0-9]*'):
        if (user / 'bus').exists():
            subprocess.run([
                'runuser', '-u', pwd.getpwuid(int(user.name)).pw_name,
                '--', 'env', 'XDG_RUNTIME_DIR=' + str(user),
                'DBUS_SESSION_BUS_ADDRESS=unix:path=' + str(user / 'bus'),
                'systemctl', '--user', 'daemon-reload',
            ], check=False)
    Path('/run/reboot-required').touch()
    pending = Path('/run/reboot-required.pkgs')
    lines = pending.read_text().splitlines() if pending.exists() else []
    if PACKAGE not in lines:
        pending.write_text('\n'.join(lines + [PACKAGE]) + '\n')


def enable():
    manifest = json.loads((PAYLOAD / 'manifest.json').read_text())
    version = subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Version}', 'libmutter-14-0'], text=True
    ).strip()
    if version != manifest['sourceVersion']:
        raise RuntimeError('Ubuntu compositor changed; refusing activation')
    source = PAYLOAD / LIBRARY.name
    if sha(source) != manifest['sha256']:
        raise RuntimeError('Bundled capture component failed verification')
    linkage = subprocess.run(
        ['ldd', str(source)], text=True, capture_output=True, check=False
    )
    if linkage.returncode or 'not found' in linkage.stdout:
        raise RuntimeError('A capture runtime dependency is missing; refusing compositor activation')
    previous_owner = owner()
    if previous_owner not in ['', PACKAGE]:
        raise RuntimeError('Another integration owns the compositor library')
    if previous_owner == PACKAGE and MARKER.exists():
        old = json.loads(MARKER.read_text())
        if sha(LIBRARY) != old['sha256']:
            raise RuntimeError('Active compositor differs from our installation')
    if not previous_owner:
        if BACKUP.exists():
            raise RuntimeError('Unexpected compositor backup already exists')
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['dpkg-divert', '--package', PACKAGE, '--divert', str(BACKUP), '--rename',
                        '--add', str(LIBRARY)], check=True)
    if not BACKUP.is_file():
        raise RuntimeError('Stock compositor backup is missing')
    old_library = LIBRARY.read_bytes() if LIBRARY.exists() else None
    old_marker = MARKER.read_bytes() if MARKER.exists() else None
    try:
        atomic_write(LIBRARY, source.read_bytes())
        marker = {**manifest, 'library': str(LIBRARY)}
        atomic_write(MARKER, (json.dumps(marker, indent=2) + '\n').encode())
        atomic_write(OVERRIDE, UNIT.encode())
        notify_restart()
    except BaseException:
        if not previous_owner:
            LIBRARY.unlink(missing_ok=True)
            subprocess.run(['dpkg-divert', '--package', PACKAGE, '--divert', str(BACKUP), '--rename',
                            '--remove', str(LIBRARY)], check=True)
            MARKER.unlink(missing_ok=True)
            OVERRIDE.unlink(missing_ok=True)
        else:
            if old_library is not None:
                atomic_write(LIBRARY, old_library)
            if old_marker is not None:
                atomic_write(MARKER, old_marker)
        raise


def disable():
    if owner() == PACKAGE:
        if not BACKUP.is_file():
            raise RuntimeError('Stock compositor backup missing; refusing removal')
        if LIBRARY.exists():
            marker = json.loads(MARKER.read_text())
            if sha(LIBRARY) != marker['sha256']:
                raise RuntimeError('Compositor changed; refusing to delete another modification')
            LIBRARY.unlink()
        subprocess.run(['dpkg-divert', '--package', PACKAGE, '--divert', str(BACKUP), '--rename',
                        '--remove', str(LIBRARY)], check=True)
    elif owner():
        raise RuntimeError('Another integration owns the compositor library')
    MARKER.unlink(missing_ok=True)
    if OVERRIDE.exists():
        if OVERRIDE.read_text() != UNIT:
            raise RuntimeError('Capture service override was edited; refusing to discard it')
        OVERRIDE.unlink()
    notify_restart()


if __name__ == '__main__':
    if os.geteuid() != 0 or sys.argv[1:] not in [['enable'], ['disable']]:
        raise SystemExit('Use the Ubuntu package manager to install or remove Ghost Notes')
    try:
        {'enable': enable, 'disable': disable}[sys.argv[1]]()
    except Exception as error:
        raise SystemExit(str(error))
