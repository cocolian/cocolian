import json,subprocess,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
meta=json.loads((root/'build/image.json').read_text())
ssh=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
pin='docker.io/cocolian/office-portal@'+meta['digest']
patch={'spec':{'template':{'metadata':{'annotations':{'office.cocolian.cn/source-sha256':meta['source_sha256']}},'spec':{'containers':[{'name':'wopi','image':pin,'command':['python','/app/server.py'],'volumeMounts':[{'mountPath':'/app','$patch':'delete'}]}]}}}}
# Source ConfigMap mount previously shadows /app; remove only that mount.
(root/'build/deployment-patch.json').write_text(json.dumps(patch,indent=2))
print(pin)
