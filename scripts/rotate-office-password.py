"""Read a new password from stdin, rotate the Kubernetes Secret, verify old/new login."""
import sys,subprocess,json,base64,urllib.request,urllib.parse,time
from pathlib import Path
ssh=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
new=sys.stdin.readline().rstrip('\r\n')
if not new:raise SystemExit('Password must not be empty')
old=base64.b64decode(subprocess.check_output(ssh+['kubectl -n office-lab get secret lab-auth -o jsonpath="{.data.key}"'])).decode().strip()
assert old!=new, 'Password is already set; no update needed'
patch={'data':{'key':base64.b64encode(new.encode()).decode()},'metadata':{'annotations':{'kubectl.kubernetes.io/last-applied-configuration':None}}}
subprocess.run(ssh+['kubectl -n office-lab patch secret lab-auth --type merge --patch-file=/dev/stdin'],input=json.dumps(patch).encode(),check=True)
subprocess.run(ssh+['kubectl -n office-lab rollout restart deployment/wopi && kubectl -n office-lab rollout status deployment/wopi --timeout=120s'],check=True)
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
def status(req):
 for attempt in range(30):
  try:
   with opener.open(req,timeout=30) as r:code=r.status
  except urllib.error.HTTPError as e:code=e.code
  if code not in (502,503,504):return code
  time.sleep(1)
 return code
def login(value):
 return status(urllib.request.Request('https://office.cocolian.cn/login',data=urllib.parse.urlencode({'key':value}).encode()))
old_status=login(old);new_status=login(new)
assert old_status==401 and new_status==303,(old_status,new_status)
# Existing session cookies must also fail the gateway's auth check.
def convert_auth(value):
 return status(urllib.request.Request('https://office.cocolian.cn/convert/health',headers={'Cookie':'office_session='+value}))
assert convert_auth(old)==401 and convert_auth(new)==200
result={'old_password_login_status':old_status,'new_password_login_status':new_status,'old_session_cookie_rejected':True,'new_session_converter_access':True}
root=Path(__file__).resolve().parents[1]
(root/'outputs/password-rotation-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
