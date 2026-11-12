#!/usr/bin/env bash
set -euo pipefail
version=$1
work="$HOME/ghost-notes-gnome"
mkdir -p "$work/source" "$work/stage"
cd "$work/source"
if ! compgen -G 'mutter-*/meson.build' >/dev/null; then
  apt-get source "mutter=$version"
fi
mapfile -t candidates < <(find "$work/source" -mindepth 2 -maxdepth 2 -name meson.build -print)
[[ ${#candidates[@]} == 1 ]] || { echo 'Expected exactly one Mutter source tree'; exit 1; }
source_root=${candidates[0]%/meson.build}
python3 "$work/apply-mutter-patch.py" "$source_root"
if [[ ! -f "$source_root/_ghostnotes/meson-private/coredata.dat" ]]; then
  meson setup "$source_root/_ghostnotes" "$source_root" \
    --prefix=/usr --libdir=lib/x86_64-linux-gnu \
    --buildtype=release -Dtests=false -Dinstalled_tests=false -Ddocs=false
fi
meson configure "$source_root/_ghostnotes" -Dprefix=/usr
ninja -C "$source_root/_ghostnotes" -j2
DESTDIR="$work/stage" meson install -C "$source_root/_ghostnotes" --no-rebuild
python3 - "$work" "$version" <<'PY'
from pathlib import Path
import hashlib,json,sys
work=Path(sys.argv[1]);prefix=work/'stage/usr'
files={str(p.relative_to(prefix)):hashlib.sha256(p.read_bytes()).hexdigest() for p in prefix.rglob('*.so*') if p.is_file() and not p.is_symlink()}
assert any('libmutter-14.so' in name for name in files)
(work/'build-manifest.json').write_text(json.dumps({'protocol':1,'mutterSourceVersion':sys.argv[2],'libraries':files,'status':'staged-not-enabled'},indent=2)+'\n')
print('Patched Mutter is staged. It has NOT replaced the active compositor.')
PY
