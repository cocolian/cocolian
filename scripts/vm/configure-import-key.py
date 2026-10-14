from pathlib import Path
import subprocess,re
root=Path(__file__).resolve().parents[2]
config=str(root/'work/dev-vm/ssh-config')
vm=['ssh','-F',config,'-o','BatchMode=yes','codex-dev']
host=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
public=subprocess.check_output(vm+['cat ~/.ssh/office-image-key.pub'],text=True).strip()
assert re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/=]+ codex-dev-office-image',public)
entry='from="192.168.124.10",restrict,command="sudo -n /usr/local/sbin/codex-dev-import-image" '+public
remote="python3 -c 'import sys,pathlib; p=pathlib.Path.home()/\".ssh/authorized_keys\"; p.parent.mkdir(mode=0o700,exist_ok=True); s=p.read_text() if p.exists() else \"\"; line=sys.stdin.read().strip(); p.write_text(s+(\"\" if not s or s.endswith(\"\\n\") else \"\\n\")+line+\"\\n\") if line not in s else None; p.chmod(0o600)'"
subprocess.run(host+[remote],input=entry+'\n',text=True,check=True)
key=subprocess.check_output(host+['cat /etc/ssh/ssh_host_ed25519_key.pub'],text=True).strip().split()
known='192.168.124.1 '+key[0]+' '+key[1]+'\n'
remote="cat >> ~/.ssh/known_hosts; chmod 600 ~/.ssh/known_hosts"
subprocess.run(vm+[remote],input=known,text=True,check=True)
ssh_config='Host office-image-host\n    HostName 192.168.124.1\n    User shamphone\n    IdentityFile ~/.ssh/office-image-key\n    IdentitiesOnly yes\n    StrictHostKeyChecking yes\n'
subprocess.run(vm+['cat >> ~/.ssh/config; chmod 600 ~/.ssh/config'],input=ssh_config,text=True,check=True)
print('Configured restricted Office image import key and trusted host key')
