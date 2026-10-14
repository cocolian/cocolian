#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
backup=/var/lib/dev-vm/backups
mkdir -p "$backup" /var/lib/dev-vm/downloads
if [ -e /usr/sbin/policy-rc.d ]; then cp -a /usr/sbin/policy-rc.d "$backup/policy-rc.d"; had_policy=1; else had_policy=0; fi
restore_policy(){ if [ "$had_policy" = 1 ]; then cp -a "$backup/policy-rc.d" /usr/sbin/policy-rc.d; else rm -f /usr/sbin/policy-rc.d; fi; }
trap restore_policy EXIT
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
apt-get -o Acquire::http::Proxy=http://127.0.0.1:7770 -o Acquire::https::Proxy=http://127.0.0.1:7770 install -y --no-install-recommends libvirt-daemon-system libvirt-clients cloud-image-utils
# Keep the libvirt default NAT network from starting on this existing k3s node.
if [ -L /etc/libvirt/qemu/networks/autostart/default.xml ]; then
 cp -a /etc/libvirt/qemu/networks/autostart/default.xml "$backup/default-network-autostart.xml"
 rm /etc/libvirt/qemu/networks/autostart/default.xml
fi
restore_policy
trap - EXIT
systemctl enable --now libvirtd
virsh list --all
virsh net-list --all
