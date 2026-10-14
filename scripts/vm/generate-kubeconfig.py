from pathlib import Path
import subprocess,json,base64,yaml
root=Path(__file__).resolve().parents[2]
ssh=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
secret=json.loads(subprocess.check_output(ssh+['kubectl -n office-lab get secret codex-dev-api-token -o json']))
data=secret['data'];token=base64.b64decode(data['token']).decode()
config={'apiVersion':'v1','kind':'Config','clusters':[{'name':'cocoserver','cluster':{'server':'https://192.168.124.1:6443','tls-server-name':'kubernetes','certificate-authority-data':data['ca.crt']}}],'users':[{'name':'codex-developer','user':{'token':token}}],'contexts':[{'name':'office-lab','context':{'cluster':'cocoserver','user':'codex-developer','namespace':'office-lab'}}],'current-context':'office-lab'}
p=root/'work/dev-vm/kubeconfig';p.write_text(yaml.safe_dump(config,sort_keys=False));p.chmod(0o600)
print('Generated scoped kubeconfig; token not printed')
