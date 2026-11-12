#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 && $(hostname) == ghost-notes-ubuntu ]] || { echo 'Restricted to administrator in the test VM'; exit 1; }
work=/home/ghostdev/ghost-notes-gnome
library=/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0
marker=/var/lib/ghost-notes/mutter-capture.json
python3 - "$work" <<'PY'
from pathlib import Path
import hashlib,json,sys,subprocess
work=Path(sys.argv[1]);manifest=json.loads((work/'build-manifest.json').read_text());name='lib/x86_64-linux-gnu/libmutter-14.so.0.0.0'
assert manifest['protocol']==1 and manifest['mutterSourceVersion'].startswith('46.2-')
installed=subprocess.check_output(['dpkg-query','-W','-f=${source:Version}','libmutter-14-0'],text=True).strip()
assert installed==manifest['mutterSourceVersion'],'Installed Mutter differs from the staged source'
assert hashlib.sha256((work/'stage/usr'/name).read_bytes()).hexdigest()==manifest['libraries'][name]
PY
if [[ -n $(dpkg-divert --list "$library") && ! -f "$marker" ]]; then
  echo 'Another integration owns this library diversion'; exit 1
fi
if [[ -z $(dpkg-divert --list "$library") ]]; then
  dpkg-divert --local --rename --add "$library"
fi
install -m 644 "$work/stage/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0" "$library"
install -d -m 755 /var/lib/ghost-notes
python3 - "$work" "$library" "$marker" <<'PY'
from pathlib import Path
import hashlib,json,sys,subprocess
manifest=json.loads((Path(sys.argv[1])/'build-manifest.json').read_text())
Path(sys.argv[3]).write_text(json.dumps({'protocol':1,'provider':'gnome-mutter','sourceVersion':manifest['mutterSourceVersion'],'library':sys.argv[2],'sha256':hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest(),'experimental':True},indent=2)+'\n')
PY
folder=/home/ghostdev/.config/systemd/user/org.gnome.Shell@wayland.service.d
install -d -m 755 -o ghostdev -g ghostdev "$folder"
cat > "$folder/ghost-notes-capture.conf" <<'UNIT'
[Service]
UnsetEnvironment=LD_LIBRARY_PATH GI_TYPELIB_PATH
Environment=GHOST_NOTES_CAPTURE_EXCLUSION=1
UNIT
chown ghostdev:ghostdev "$folder/ghost-notes-capture.conf"
runuser -u ghostdev -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user daemon-reload
# Select the actual Wayland session instead of accepting a silent X11 fallback.
busctl --system call org.freedesktop.Accounts /org/freedesktop/Accounts/User1000 org.freedesktop.Accounts.User SetSession s ubuntu-wayland
busctl --system call org.freedesktop.Accounts /org/freedesktop/Accounts/User1000 org.freedesktop.Accounts.User SetXSession s ubuntu-wayland
busctl --system call org.freedesktop.Accounts /org/freedesktop/Accounts/User1000 org.freedesktop.Accounts.User SetSessionType s wayland
printf 'VM-only Mutter core override installed; original retained by dpkg-divert. Restart GDM.\n'
