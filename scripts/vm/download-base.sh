#!/bin/bash
set -euo pipefail
cd /var/lib/dev-vm/downloads
origin=https://cloud-images.ubuntu.com/minimal/releases/noble/release
proxy=http://127.0.0.1:7770
curl --proxy "$proxy" -fsSL --retry 3 "$origin/SHA256SUMS" -o SHA256SUMS
curl --proxy "$proxy" -fL --retry 3 -C - "$origin/ubuntu-24.04-minimal-cloudimg-amd64.img" -o ubuntu-24.04-minimal-cloudimg-amd64.img
python3 - <<'PY'
from pathlib import Path
import hashlib
name='ubuntu-24.04-minimal-cloudimg-amd64.img'
expected=next(line.split()[0] for line in Path('SHA256SUMS').read_text().splitlines() if line.split()[-1].lstrip('*')==name)
actual=hashlib.file_digest(open(name,'rb'),'sha256').hexdigest()
assert actual==expected,(actual,expected)
print('Ubuntu image SHA256 verified:',actual)
PY
