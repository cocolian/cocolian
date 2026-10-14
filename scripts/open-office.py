#!/usr/bin/env python3
"""Open the HTTPS Office portal with the existing access key fetched over SSH."""
import base64,subprocess,urllib.parse,urllib.request,webbrowser,sys,http.cookiejar,json
command=['ssh','-J','aliserver','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2','kubectl -n office-lab get secret lab-auth -o jsonpath="{.data.key}"']
key=base64.b64decode(subprocess.check_output(command)).decode().strip()
if '--check' in sys.argv:
    jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(jar))
    with opener.open('https://office.cocolian.cn/?key='+urllib.parse.quote(key),timeout=15) as response:
        assert response.status==200 and '/convert/forms/libreoffice/convert' in response.read().decode()
    cookie=next(c for c in jar if c.name=='office_session')
    assert cookie.secure and cookie.has_nonstandard_attr('HttpOnly')
    print(json.dumps({'portal_login':'passed','secure_http_only_cookie':True}))
elif '--print-key' in sys.argv:
    print(key)
else:
    webbrowser.open('https://office.cocolian.cn/?key='+urllib.parse.quote(key))
    print('已打开 Office HTTPS 入口。登录后地址会自动清除密钥参数。')
