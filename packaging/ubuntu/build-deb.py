#!/usr/bin/env python3
"""Build the exact-version Ubuntu preview from explicit, verified binary inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile

VERSION = '1.2.2+ubuntu24.04.2'
MUTTER = '46.2-1ubuntu0.24.04.18'
LIBRARY = 'libmutter-14.so.0.0.0'
ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / 'packaging/ubuntu'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source, destination, mode=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if mode is not None:
        destination.chmod(mode)


def build(electron, companion, output):
    manifest = json.loads((companion / 'manifest.json').read_text())
    if (manifest.get('protocol') != 1 or
            manifest.get('provider') != 'gnome-mutter' or
            manifest.get('sourceVersion') != MUTTER or
            manifest.get('sha256') != digest(companion / LIBRARY)):
        raise ValueError('Unsupported or corrupt companion input')
    source = companion / 'mutter-source.tar.xz'
    if manifest.get('sourceSha256') != digest(source):
        raise ValueError('Corresponding source hash does not match')
    with tarfile.open(source) as archive:
        names = archive.getnames()
        if not any(n.endswith('/src/compositor/meta-window-actor.c') for n in names):
            raise ValueError('Corresponding Mutter source is missing')
        if not any(n.endswith('/build-user.sh') for n in names):
            raise ValueError('Companion build instructions are missing')
    if not (electron / 'electron').is_file() or not (electron / 'chrome-sandbox').is_file():
        raise ValueError('Expected a complete Electron Linux amd64 distribution')
    header = (electron / 'electron').read_bytes()[:20]
    if header[:5] != b'\x7fELF\x02' or header[18:20] != b'\x3e\x00':
        raise ValueError('Electron must be Linux amd64 ELF')
    native_dependencies = manifest.get('runtimeDependencies', '')
    if 'libdisplay-info1' not in native_dependencies or '\n' in native_dependencies:
        raise ValueError('Verified native runtime dependency metadata is required')
    output.mkdir(parents=True, exist_ok=True)
    result = output / ('ghost-notes-ubuntu_' + VERSION + '_amd64.deb')
    with tempfile.TemporaryDirectory(prefix='ghost-notes-deb-') as temp:
        stage = Path(temp)
        app = stage / 'opt/ghost-notes-ubuntu/app'
        app.mkdir(parents=True)
        # Include runtime modules without copying development dependencies or user data.
        for file in ROOT.glob('*.js'):
            copy(file, app / file.name)
        for folder in ['note', 'manager', 'build']:
            for file in (ROOT / folder).rglob('*'):
                if file.is_file() and 'Release' not in file.parts:
                    copy(file, app / file.relative_to(ROOT))
        for name in ['status.py', 'input-region.py']:
            copy(ROOT / 'integrations/gnome-capture' / name,
                 app / 'integrations/gnome-capture' / name)
        package = json.loads((ROOT / 'package.json').read_text())
        package = {key: package[key] for key in ['name', 'version', 'main', 'description', 'author', 'license', 'desktopName']}
        (app / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
        shutil.copytree(electron, stage / 'opt/ghost-notes-ubuntu/electron')
        # dpkg archive owns all files as root; sandbox is the only setuid executable.
        for path in stage.rglob('*'):
            if path.is_file() and not path.is_symlink():
                path.chmod(0o755 if path.stat().st_mode & 0o111 else 0o644)
        (stage / 'opt/ghost-notes-ubuntu/electron/chrome-sandbox').chmod(0o4755)
        payload = stage / 'usr/lib/ghost-notes-ubuntu'
        for name in [LIBRARY, 'manifest.json']:
            copy(companion / name, payload / name, 0o644)
        copy(TEMPLATES / 'capture-install.py', payload / 'capture-install.py', 0o644)
        copy(TEMPLATES / 'ghost-notes', stage / 'usr/bin/ghost-notes', 0o755)
        copy(TEMPLATES / 'ghost-notes.desktop', stage / 'usr/share/applications/ghost-notes.desktop', 0o644)
        copy(ROOT / 'build/icon.png', stage / 'usr/share/icons/hicolor/512x512/apps/ghost-notes.png', 0o644)
        docs = stage / 'usr/share/doc/ghost-notes-ubuntu'
        copy(ROOT / 'LICENSE', docs / 'copyright', 0o644)
        copy(TEMPLATES / 'README.md', docs / 'README.md', 0o644)
        copy(source, docs / 'mutter-source.tar.xz', 0o644)
        (docs / 'build-info.json').write_text(json.dumps({
            'packageVersion': VERSION, 'companion': manifest,
            'electronVersion': (electron / 'version').read_text().strip(),
            'appCommit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
            'experimental': True,
        }, indent=2) + '\n')
        metadata = stage / 'DEBIAN'
        metadata.mkdir()
        dependencies = [
            'libmutter-14-0 (= ' + MUTTER + ')', 'gnome-shell (>= 46)',
            'gnome-shell (<< 47)', 'mutter-common (= ' + MUTTER + ')',
            'mutter-common-bin (= ' + MUTTER + ')', 'gnome-keyring',
            'python3', 'zenity', 'libsecret-1-0', 'libx11-6', 'libxext6',
            'libasound2t64', 'libatk-bridge2.0-0t64', 'libatk1.0-0t64',
            'libatspi2.0-0t64', 'libc6 (>= 2.39)', 'libcairo2', 'libcups2t64',
            'libdbus-1-3', 'libdrm2', 'libexpat1', 'libgbm1', 'libglib2.0-0t64',
            'libgtk-3-0t64', 'libnspr4', 'libnss3', 'libpango-1.0-0',
            'libudev1', 'libxcomposite1', 'libxdamage1', 'libxfixes3',
            'libxkbcommon0', 'libxrandr2', 'libxcb1', 'libxshmfence1',
        ]
        # Prefer symbol-derived constraints over unversioned runtime declarations.
        derived = native_dependencies.split(', ')
        names = {item.split(' (', 1)[0] for item in derived}
        dependencies = [item for item in dependencies if ' (' in item or item not in names]
        versioned = {item.split(' (', 1)[0] for item in dependencies if ' (' in item}
        dependencies += [item for item in derived if item.split(' (', 1)[0] not in versioned]
        size = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file()) // 1024
        (metadata / 'control').write_text(
            'Package: ghost-notes-ubuntu\nVersion: ' + VERSION + '\n'
            'Section: utils\nPriority: optional\nArchitecture: amd64\n'
            'Maintainer: Nandith Narayanan <184540937+Nandith-0777@users.noreply.github.com>\n'
            'Homepage: https://github.com/Nandith-0777/ghost-notes-ubuntu\n'
            'Installed-Size: ' + str(size) + '\nDepends: ' + ', '.join(dependencies) + '\n'
            'Description: Floating notes with experimental Ubuntu capture exclusion\n'
            ' Ghost Notes by Navya Bijoy, with Ubuntu integration by Nandith Narayanan.\n'
            ' This preview supports Ubuntu 24.04 GNOME Wayland and an exact Mutter\n'
            ' revision. Restart Ubuntu after installation or removal.\n'
        )
        for name in ['preinst', 'postinst', 'prerm', 'postrm']:
            copy(TEMPLATES / name, metadata / name, 0o755)
        md5 = []
        for file in sorted(stage.rglob('*')):
            if file.is_file() and not file.is_symlink() and metadata not in file.parents:
                md5.append(hashlib.md5(file.read_bytes()).hexdigest() + '  ' + str(file.relative_to(stage)))
        (metadata / 'md5sums').write_text('\n'.join(md5) + '\n')
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '-z3', '--build', str(stage), str(result)], check=True)
    result.with_suffix('.deb.sha256').write_text(digest(result) + '  ' + result.name + '\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--electron', type=Path, required=True)
    parser.add_argument('--companion', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('dist'))
    args = parser.parse_args()
    build(args.electron.resolve(), args.companion.resolve(), args.output.resolve())
