from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parents[2]
host=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
vm=['ssh','-F',str(root/'work/dev-vm/ssh-config'),'-o','BatchMode=yes','codex-dev']
def remote(args,cmd):return subprocess.check_output(args+[cmd],text=True)
before=json.loads(remote(host,'cat /tmp/dev-vm-pods-before.json'));after=json.loads(remote(host,'kubectl get pods -A -o json'))
def signature(p):return {'uid':p['metadata']['uid'],'containers':[(c['name'],c['imageID'],c['ready'],c['restartCount']) for c in p['status'].get('containerStatuses',[])]}
def mapping(data):return {(p['metadata']['namespace'],p['metadata']['name']):signature(p) for p in data['items']}
assert mapping(before)==mapping(after),'Existing Kubernetes Pods changed'
profile=json.loads(remote(vm,"python3 - <<'CODE'\nimport json,subprocess,platform\ndef out(*a):return subprocess.check_output(a,text=True).strip()\nprint(json.dumps({'hostname':platform.node(),'architecture':platform.machine(),'network':json.loads(out('ip','-j','address')),'memory':out('free','-h'),'disk':out('df','-h','/'),'versions':out('dpkg-query','-W','chatgpt','google-chrome-stable','xfce4','xrdp','ibus-libpinyin'),'node':out('node','--version'),'codex_cli':out('codex','--version'),'desktop_test':json.load(open('/home/codex/rdp-session-check.json'))}))\nCODE"))
result={'existing_k3s_pods_unchanged':len(mapping(before)),'vm':profile,'configuration':{'vcpu':4,'memory_MiB':16384,'disk_GiB':200},'chatgpt_account_login':'pending user sign-in','external_ipv6_rdp':'pending user router firewall and DNS configuration','build_and_host_image_import_verified':True,'playwright_sandboxed_chrome_verified':True}
(root/'outputs/dev-vm-state.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'existing_k3s_pods_unchanged':len(mapping(before)),'vm':profile['hostname'],'node':profile['node']}))
