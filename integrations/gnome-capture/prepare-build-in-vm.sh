#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run only as administrator inside the Ubuntu test VM'; exit 1; }
. /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 ]] || { echo 'Only Ubuntu 24.04 is supported'; exit 1; }
[[ $(hostname) == ghost-notes-ubuntu ]] || { echo 'This prototype build is restricted to the dedicated test VM'; exit 1; }
work=/home/ghostdev/ghost-notes-gnome
version=$(dpkg-query -W -f='${source:Version}' libmutter-14-0)
[[ $version == 46.2-* ]] || { echo "Unsupported Mutter source: $version"; exit 1; }
export DEBIAN_FRONTEND=noninteractive
python3 - <<'PY'
from pathlib import Path
import re
source=Path('/etc/apt/sources.list.d/ubuntu.sources').read_text()
Path('/etc/apt/sources.list.d/ghost-notes-build.sources').write_text(re.sub(r'^Types:.*$', 'Types: deb-src', source, flags=re.M))
PY
apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout=30
# Keep the stock rollback libraries and the source build on the same supported ABI.
version=$(apt-cache policy libmutter-14-0 | awk '/Candidate:/ {print $2}')
[[ $version == 46.2-* ]] || { echo "Unsupported Mutter candidate: $version"; exit 1; }
apt-get install -y --only-upgrade "libmutter-14-0=$version" "mutter-common=$version" "mutter-common-bin=$version" "gir1.2-mutter-14=$version"
DEB_BUILD_PROFILES='nocheck nodoc' apt-get build-dep -y --no-install-recommends "mutter=$version"
apt-get install -y --no-install-recommends meson ninja-build build-essential pkg-config gir1.2-gst-plugins-base-1.0 gstreamer1.0-tools
runuser -u ghostdev -- bash "$work/build-user.sh" "$version"
