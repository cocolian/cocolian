#!/bin/bash
set -euo pipefail
cd /var/lib/dev-vm/downloads
python3 - <<'PY'
from pathlib import Path
import hashlib
name='ubuntu-24.04-minimal-cloudimg-amd64.img'
expected=next(line.split()[0] for line in Path('SHA256SUMS').read_text().splitlines() if line.split()[-1].lstrip('*')==name)
actual=hashlib.file_digest(open(name,'rb'),'sha256').hexdigest()
assert actual==expected,(actual,expected)
print('Verified Ubuntu image:',actual)
PY
if virsh dominfo codex-dev >/dev/null 2>&1; then echo 'codex-dev already exists; refusing to overwrite'; exit 1; fi
mkdir -p /var/lib/libvirt/images /var/lib/libvirt/qemu/nvram
cp --reflink=auto ubuntu-24.04-minimal-cloudimg-amd64.img /var/lib/libvirt/images/codex-dev.qcow2
qemu-img resize /var/lib/libvirt/images/codex-dev.qcow2 200G
cloud-localds --network-config=/var/lib/dev-vm/seed/network-config /var/lib/libvirt/images/codex-dev-seed.iso /var/lib/dev-vm/seed/user-data /var/lib/dev-vm/seed/meta-data
chmod 600 /var/lib/dev-vm/seed/user-data /var/lib/libvirt/images/codex-dev-seed.iso
virsh net-define /var/lib/dev-vm/config/codex-dev-mgmt.xml
virsh net-start codex-dev-mgmt
virsh net-autostart codex-dev-mgmt
virsh define /var/lib/dev-vm/config/codex-dev.xml
virsh autostart codex-dev
virsh start codex-dev
virsh dominfo codex-dev
