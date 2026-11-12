#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 && $(hostname) == ghost-notes-ubuntu ]] || { echo 'Restricted to administrator in the test VM'; exit 1; }
library=/usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0
marker=/var/lib/ghost-notes/mutter-capture.json
if [[ -f "$marker" ]]; then
  python3 - "$library" "$marker" <<'PY'
from pathlib import Path
import hashlib,json,sys
manifest=json.loads(Path(sys.argv[2]).read_text())
assert hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()==manifest['sha256'],'The library changed; refusing to discard another modification'
PY
  rm -- "$library"
  dpkg-divert --local --rename --remove "$library"
  rm -- "$marker"
fi
rm -f /home/ghostdev/.config/systemd/user/org.gnome.Shell@wayland.service.d/ghost-notes-capture.conf
runuser -u ghostdev -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user daemon-reload
printf 'Ubuntu Mutter library restored. Restart GDM to complete rollback.\n'
