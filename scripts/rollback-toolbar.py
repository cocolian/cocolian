"""Restore the pre-toolbar deployment revision; keep the rotated Secret."""
import json,subprocess
ssh=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
previous=json.loads(subprocess.check_output(ssh+['sudo cat /var/lib/office-lab/backups/toolbar-20261014/wopi-before.json']))
revision=previous['metadata']['annotations']['deployment.kubernetes.io/revision']
assert revision.isdigit()
subprocess.run(ssh+['kubectl -n office-lab rollout undo deployment/wopi --to-revision='+revision+' && kubectl -n office-lab rollout status deployment/wopi --timeout=120s'],check=True)
