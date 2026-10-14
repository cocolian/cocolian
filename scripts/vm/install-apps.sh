#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
mkdir -p /opt/dev-install
proxy=http://192.168.124.1:7770
curl --noproxy '*' -fsS http://192.168.124.1:8800/node-artifact-name.txt -o /opt/dev-install/node-artifact-name.txt
node_file=$(cat /opt/dev-install/node-artifact-name.txt)
[[ "$node_file" =~ ^node-v24\.[0-9]+\.[0-9]+-linux-x64.tar.xz$ ]]
curl --noproxy '*' -fsS "http://192.168.124.1:8800/$node_file" -o "/opt/dev-install/$node_file"
curl --noproxy '*' -fsS http://192.168.124.1:8800/node-SHASUMS256.txt -o /opt/dev-install/node-SHASUMS256.txt
cd /opt/dev-install
grep "  $node_file$" node-SHASUMS256.txt | sha256sum -c -
mkdir -p /opt/node24
tar -xJf "$node_file" -C /opt/node24 --strip-components=1
for command in node npm npx corepack; do [ ! -e "/opt/node24/bin/$command" ] || ln -sf "/opt/node24/bin/$command" "/usr/local/bin/$command"; done
# The official desktop package is expected, not an unofficial Linux wrapper.
[ "$(dpkg-deb -f chatgpt_amd64.deb Package)" = chatgpt ]
apt-get install -y --no-install-recommends /opt/dev-install/chatgpt_amd64.deb /opt/dev-install/google-chrome-stable_amd64.deb
install -m 755 /opt/dev-install/kubectl /usr/local/bin/kubectl
cat > /usr/local/bin/chatgpt-dev <<'APP'
#!/bin/sh
export HTTP_PROXY=http://192.168.124.1:7770 HTTPS_PROXY=http://192.168.124.1:7770
export http_proxy="$HTTP_PROXY" https_proxy="$HTTPS_PROXY"
export NO_PROXY=localhost,127.0.0.1,::1,192.168.124.1,192.168.124.10,192.168.137.75
export no_proxy="$NO_PROXY"
exec /usr/bin/chatgpt --disable-gpu --proxy-server="$HTTP_PROXY" --proxy-bypass-list='localhost;127.0.0.1;[::1];192.168.124.*' "$@"
APP
cat > /usr/local/bin/chrome-dev <<'APP'
#!/bin/sh
exec /usr/bin/google-chrome --disable-gpu --proxy-server=http://192.168.124.1:7770 --proxy-bypass-list='localhost;127.0.0.1;[::1];192.168.124.*' "$@"
APP
chmod 755 /usr/local/bin/chatgpt-dev /usr/local/bin/chrome-dev
mkdir -p /home/codex/.local/share/applications /home/codex/.config/autostart /home/codex/Desktop /home/codex/projects
python3 - <<'PY'
from pathlib import Path
import subprocess
for package,launcher in [('chatgpt','chatgpt-dev'),('google-chrome-stable','chrome-dev')]:
 paths=subprocess.check_output(['dpkg','-L',package],text=True).splitlines()
 desktop=next(Path(p) for p in paths if p.startswith('/usr/share/applications/') and p.endswith('.desktop'))
 text=desktop.read_text()
 text='\n'.join('Exec=/usr/local/bin/'+launcher+' %U' if line.startswith('Exec=') else line for line in text.splitlines())+'\n'
 (Path('/home/codex/.local/share/applications')/desktop.name).write_text(text)
 if package=='chatgpt':
  dest=Path('/home/codex/Desktop/ChatGPT.desktop');dest.write_text(text);dest.chmod(0o755)
  (Path('/home/codex/.config/autostart')/'chatgpt-dev.desktop').write_text('[Desktop Entry]\nType=Application\nName=ChatGPT Development\nExec=/usr/local/bin/chatgpt-dev\nX-GNOME-Autostart-enabled=true\n')
Path('/home/codex/.config/mimeapps.list').write_text('[Default Applications]\ntext/html=google-chrome.desktop\nx-scheme-handler/http=google-chrome.desktop\nx-scheme-handler/https=google-chrome.desktop\n')
PY
chown -R codex:codex /home/codex/.local /home/codex/.config /home/codex/Desktop /home/codex/projects
node --version
npm --version
kubectl version --client -o json
sudo -u codex docker version --format '{{.Server.Version}}'
dpkg-query -W chatgpt google-chrome-stable xrdp xfce4
