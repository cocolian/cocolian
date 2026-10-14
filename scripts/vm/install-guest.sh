#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
proxy=http://192.168.124.1:7770
export http_proxy="$proxy" https_proxy="$proxy" HTTP_PROXY="$proxy" HTTPS_PROXY="$proxy"
export no_proxy=localhost,127.0.0.1,::1,192.168.124.1,192.168.124.10,192.168.137.75
export NO_PROXY="$no_proxy"
mkdir -p /opt/dev-install
cat > /etc/apt/apt.conf.d/80-dev-proxy <<APT
Acquire::http::Proxy "$proxy";
Acquire::https::Proxy "$proxy";
Acquire::https::Proxy::mirrors.aliyun.com "DIRECT";
Acquire::Languages "none";
Acquire::ForceIPv4 "true";
APT
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/apt/sources.list.d/ubuntu.sources')
s=p.read_text().replace('http://archive.ubuntu.com/ubuntu','https://mirrors.aliyun.com/ubuntu').replace('http://security.ubuntu.com/ubuntu','https://mirrors.aliyun.com/ubuntu')
p.write_text(s)
PY
apt-get update
apt-get install -y --no-install-recommends xfce4 xorgxrdp xrdp dbus-x11 xserver-xorg-core xfonts-base fonts-dejavu-core fonts-wqy-zenhei locales gnome-keyring libpam-gnome-keyring qemu-guest-agent openssh-server ca-certificates curl git python3 python3-pip python3-venv build-essential pkg-config jq unzip ripgrep docker.io docker-buildx ufw mousepad xfce4-terminal
locale-gen zh_CN.UTF-8 en_US.UTF-8
update-locale LANG=zh_CN.UTF-8
cat > /home/codex/.xsession <<'SESSION'
#!/bin/sh
unset DBUS_SESSION_BUS_ADDRESS SESSION_MANAGER
export XDG_SESSION_TYPE=x11
exec dbus-run-session -- startxfce4
SESSION
chmod 755 /home/codex/.xsession
chown codex:codex /home/codex/.xsession
usermod -aG docker codex
usermod -aG ssl-cert xrdp
cat >> /etc/environment <<ENV
HTTP_PROXY="$proxy"
HTTPS_PROXY="$proxy"
http_proxy="$proxy"
https_proxy="$proxy"
NO_PROXY="$no_proxy"
no_proxy="$no_proxy"
ENV
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/proxy.conf <<ENV
[Service]
Environment="HTTP_PROXY=$proxy" "HTTPS_PROXY=$proxy" "NO_PROXY=$no_proxy"
ENV
openssl req -x509 -nodes -newkey rsa:3072 -days 365 -subj /CN=codex-dev -keyout /etc/xrdp/key.pem -out /etc/xrdp/cert.pem >/dev/null 2>&1
chown root:xrdp /etc/xrdp/key.pem /etc/xrdp/cert.pem
chmod 640 /etc/xrdp/key.pem
chmod 644 /etc/xrdp/cert.pem
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/xrdp/xrdp.ini');s=p.read_text().replace('security_layer=negotiate','security_layer=tls');p.write_text(s)
p=Path('/etc/xrdp/sesman.ini');s=p.read_text().replace('KillDisconnected=true','KillDisconnected=false');p.write_text(s)
p=Path('/etc/pam.d/xrdp-sesman');s=p.read_text()
if 'pam_gnome_keyring.so' not in s:s+='\nauth optional pam_gnome_keyring.so\nsession optional pam_gnome_keyring.so auto_start\n'
p.write_text(s)
PY
systemctl daemon-reload
systemctl enable --now qemu-guest-agent docker xrdp
systemctl restart docker xrdp
ufw default deny incoming
ufw default allow outgoing
ufw allow in on mgmt0 from 192.168.124.1 to any port 22 proto tcp
ufw allow 3389/tcp
ufw --force enable
printf '\nDesktop and development base installed\n'
ss -lntp | grep -E ':3389|:22'
