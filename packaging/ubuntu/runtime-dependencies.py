#!/usr/bin/env python3
"""Derive native runtime requirements from Ubuntu's installed symbol metadata."""
from pathlib import Path
import argparse
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--electron', type=Path, required=True)
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='ghost-shlibdeps-') as folder:
    root = Path(folder)
    (root / 'debian').mkdir()
    (root / 'debian/control').write_text(
        'Source: ghost-notes-ubuntu\nSection: utils\nPriority: optional\n'
        'Maintainer: Nandith Narayanan <184540937+Nandith-0777@users.noreply.github.com>\n'
        'Standards-Version: 4.7.0\n\n'
        'Package: ghost-notes-ubuntu\nArchitecture: amd64\nDescription: Ghost Notes Ubuntu preview\n'
    )
    result = subprocess.check_output([
        'dpkg-shlibdeps', '--ignore-missing-info', '-O',
        '-e' + str(args.library.resolve()),
        '-e' + str((args.electron / 'electron').resolve()),
        '-l' + str(args.electron.resolve()),
    ], cwd=root, text=True)
    lines = [line for line in result.splitlines() if line.startswith('shlibs:Depends=')]
    if len(lines) != 1:
        raise SystemExit('Could not derive runtime dependencies')
    print(lines[0].split('=', 1)[1])
