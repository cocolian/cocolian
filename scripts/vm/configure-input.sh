#!/bin/bash
set -euo pipefail
cat > /home/codex/.config/autostart/dev-ibus.desktop <<'APP'
[Desktop Entry]
Type=Application
Name=Chinese Input
Exec=ibus-daemon -drx
X-GNOME-Autostart-enabled=true
APP
cat > /home/codex/.xsession <<'SESSION'
#!/bin/sh
unset DBUS_SESSION_BUS_ADDRESS SESSION_MANAGER
export XDG_SESSION_TYPE=x11
export GTK_IM_MODULE=ibus
export QT_IM_MODULE=ibus
export XMODIFIERS=@im=ibus
exec dbus-run-session -- startxfce4
SESSION
chmod 755 /home/codex/.xsession
chown codex:codex /home/codex/.xsession /home/codex/.config/autostart/dev-ibus.desktop
sudo -u codex dbus-run-session -- gsettings set org.freedesktop.ibus.general preload-engines "['xkb:us::eng', 'libpinyin']"
