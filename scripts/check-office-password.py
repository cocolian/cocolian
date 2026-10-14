"""Check a retired password from stdin against the current Secret, without printing either."""
import sys,subprocess,base64,urllib.request,urllib.parse,urllib.error,time,json
from pathlib import Path
old=sys.stdin.readline().strip()
ssh=['ssh','-J','aliserver','-o','BatchMode=yes','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2']
new=base64.b64decode(subprocess.check_output(ssh+['kubectl -n office-lab get secret lab-auth -o jsonpath="{.data.key}"'])).decode().strip()
assert old and old!=new
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
def login(value):return status(urllib.request.Request('https://office.cocolian.cn/login',data=urllib.parse.urlencode({'key':value}).encode()))
def converter(value,kind):return status(urllib.request.Request('https://office.cocolian.cn/convert/health',headers={kind:('Bearer '+value) if kind=='Authorization' else 'office_session='+value}))
result={'old_password_login_status':login(old),'new_password_login_status':login(new),'old_session_status':converter(old,'Cookie'),'new_session_status':converter(new,'Cookie'),'old_bearer_status':converter(old,'Authorization'),'new_bearer_status':converter(new,'Authorization')}
assert result=={'old_password_login_status':401,'new_password_login_status':303,'old_session_status':401,'new_session_status':200,'old_bearer_status':401,'new_bearer_status':200},result
(Path(__file__).resolve().parents[1]/'outputs/password-rotation-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
