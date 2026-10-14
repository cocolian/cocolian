from pathlib import Path
import yaml
root=Path(__file__).resolve().parents[2];work=root/'work/dev-vm'
user={'name':'codex','gecos':'Codex Developer','groups':['adm','sudo'],'shell':'/bin/bash','sudo':'ALL=(ALL) NOPASSWD:ALL','lock_passwd':False,'hashed_passwd':(work/'password.hash').read_text().strip(),'ssh_authorized_keys':[(work/'provision-key.pub').read_text().strip()]}
config={'hostname':'codex-dev','manage_etc_hosts':True,'disable_root':True,'ssh_pwauth':False,'users':[user],'package_update':False,'package_upgrade':False,'timezone':'Asia/Shanghai','write_files':[{'path':'/etc/profile.d/dev-build.sh','permissions':'0644','content':'export CMAKE_BUILD_PARALLEL_LEVEL=2\nexport MAKEFLAGS=-j2\n'},{'path':'/etc/sysctl.d/90-dev-ipv6.conf','permissions':'0644','content':'net.ipv6.conf.all.use_tempaddr=0\nnet.ipv6.conf.default.use_tempaddr=0\n'}]}
network={'version':2,'renderer':'networkd','ethernets':{'lan0':{'match':{'macaddress':'52:54:00:42:15:01'},'set-name':'lan0','dhcp4':True,'dhcp6':False,'accept-ra':True,'ipv6-privacy':False,'optional':True,'nameservers':{'addresses':['223.5.5.5','119.29.29.29']}},'mgmt0':{'match':{'macaddress':'52:54:00:42:15:02'},'set-name':'mgmt0','addresses':['192.168.124.10/24'],'dhcp4':False,'dhcp6':False,'accept-ra':False,'optional':True}}}
(work/'user-data').write_text('#cloud-config\n'+yaml.safe_dump(config,sort_keys=False));(work/'user-data').chmod(0o600)
(work/'network-config').write_text(yaml.safe_dump(network,sort_keys=False))
(work/'meta-data').write_text('instance-id: codex-dev-20261014\nlocal-hostname: codex-dev\n')
print('Generated cloud-init user and network configuration')
