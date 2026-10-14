#!/bin/bash
set -euo pipefail
state=$(virsh domstate codex-dev)
[ "$state" = 'shut off' ] || { echo "Refusing disk attach: VM state=$state"; exit 1; }
modprobe nbd max_part=16
[ ! -e /sys/block/nbd0/pid ] || { echo 'nbd0 already used'; exit 1; }
qemu-nbd --read-only --connect=/dev/nbd0 /var/lib/libvirt/images/codex-dev.qcow2
cleanup(){ umount /mnt/codex-dev-inspect 2>/dev/null || true; qemu-nbd --disconnect /dev/nbd0; }
trap cleanup EXIT
udevadm settle
mkdir -p /mnt/codex-dev-inspect
mount -o ro,noload /dev/nbd0p1 /mnt/codex-dev-inspect
root=/mnt/codex-dev-inspect
ls "$root/etc/netplan"
grep -E 'cloud-init|ds-identify|DataSource|ERROR|WARNING|NoCloud|disabled|seed' "$root/var/log/cloud-init.log" | tail -25 || true
cat "$root/run/cloud-init/ds-identify.log" 2>/dev/null || true
ls "$root/var/lib/cloud/data" 2>/dev/null || true
cat "$root/var/lib/cloud/data/status.json" 2>/dev/null || true
ls "$root/etc/cloud/cloud.cfg.d"
grep -R -E 'datasource_list|NoCloud|disable|ds-identify' "$root/etc/cloud/cloud.cfg.d" "$root/etc/cloud/ds-identify.cfg" 2>/dev/null || true
