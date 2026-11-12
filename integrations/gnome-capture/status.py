#!/usr/bin/env python3
"""Read-only, fail-closed verification of the experimental Mutter companion."""
from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess

MARKER = Path('/var/lib/ghost-notes/mutter-capture.json')
LIBRARY = Path('/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0')


def status():
    unsupported = {
        'protocol': 1,
        'provider': 'gnome-mutter',
        'mode': 'unsupported',
        'experimental': True,
    }
    try:
        marker_stat = MARKER.stat()
        if marker_stat.st_uid != 0 or marker_stat.st_mode & (
            stat.S_IWGRP | stat.S_IWOTH
        ):
            return unsupported
        manifest = json.loads(MARKER.read_text())
        if (
            manifest.get('protocol') != 1
            or manifest.get('provider') != 'gnome-mutter'
            or manifest.get('library') != str(LIBRARY)
            or not manifest.get('sourceVersion', '').startswith('46.2-')
        ):
            return unsupported
        version = subprocess.check_output(
            ['dpkg-query', '-W', '-f=${source:Version}', 'libmutter-14-0'],
            text=True,
            timeout=1,
        ).strip()
        if version != manifest['sourceVersion']:
            return unsupported
        info = LIBRARY.stat()
        if info.st_uid != 0 or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            return unsupported
        if hashlib.sha256(LIBRARY.read_bytes()).hexdigest() != manifest['sha256']:
            return unsupported
        matches = []
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                if (
                    proc.stat().st_uid != os.getuid()
                    or (proc / 'comm').read_text().strip() != 'gnome-shell'
                ):
                    continue
                env = (proc / 'environ').read_bytes().split(bytes([0]))
                if (
                    b'GHOST_NOTES_CAPTURE_EXCLUSION=1' not in env
                    or b'XDG_SESSION_TYPE=wayland' not in env
                ):
                    continue
                for line in (proc / 'maps').read_text().splitlines():
                    fields = line.split(None, 5)
                    if (
                        len(fields) == 6
                        and fields[5] == str(LIBRARY)
                        and int(fields[4]) == info.st_ino
                    ):
                        matches.append(proc.name)
                        break
            except (OSError, ValueError, ProcessLookupError):
                continue
        if len(matches) != 1:
            return unsupported
        return {**unsupported, 'mode': 'compositor-omit', 'sourceVersion': version}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return unsupported


if __name__ == '__main__':
    print(json.dumps(status()))
