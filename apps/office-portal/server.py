import re, uuid, mimetypes, shutil
import ai_proxy
import file_open
import render_profile
import os, json, hashlib, threading, time, urllib.parse, urllib.request, html, zipfile, io, hmac
from http.cookies import SimpleCookie, CookieError
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

EDITOR = json.loads(Path(__file__).with_name('editor.json').read_text())
if EDITOR['language'] not in ('zh-CN', 'zh-TW', 'en-US') or EDITOR['ui_mode'] not in ('compact', 'tabbed'):
    raise ValueError('Unsupported editor configuration')
DATA = Path(os.environ.get('OFFICE_DATA_DIR', '/data')); DATA.mkdir(parents=True, exist_ok=True)
KEY = os.environ['LAB_KEY'].strip()
TOKENS = {hashlib.sha256((KEY+u).encode()).hexdigest(): u for u in ('Alice','Bob')}
LOCK = threading.RLock()
locks = {}
FILE = DATA/'collaboration.docx'
if not FILE.exists():
    with zipfile.ZipFile(FILE,'w') as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Office Lab Collaboration Test</w:t></w:r></w:p><w:p><w:r><w:t>中文文档转换验证：协同办公。</w:t></w:r></w:p><w:sectPr/></w:body></w:document>')

class Handler(BaseHTTPRequestHandler):
    def authenticated(self, query=None):
        values=[]
        auth=self.headers.get('Authorization','')
        if auth.startswith('Bearer '): values.append(auth[7:].strip())
        try:
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            if 'office_session' in cookies: values.append(cookies['office_session'].value)
        except CookieError: pass
        if query is not None: values.extend(query.get('key',[]))
        return any(hmac.compare_digest(value.encode(),KEY.encode()) for value in values)
    def cookie_headers(self):
        secure='; Secure' if self.headers.get('Host','').split(':')[0]=='office.cocolian.cn' or self.headers.get('X-Forwarded-Proto')=='https' else ''
        return {'Set-Cookie':'office_session='+KEY+'; Path=/; HttpOnly; SameSite=Lax; Max-Age=14400'+secure,'Location':'/workspace'}
    def login_page(self, error=''):
        return '''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Office 文档工作台</title><style>*{box-sizing:border-box}body{font:15px system-ui!important;background:#f4f6fb;color:#19243b;max-width:1000px!important;margin:48px auto!important;padding:32px!important}h1{font-size:32px;letter-spacing:-1px;margin-bottom:8px}h2{font-size:20px;margin-top:32px}p{color:#637089;line-height:1.7}a{color:#3659d9;text-decoration:none}a[href^="/edit"]{display:inline-block;background:#3659d9;color:white;padding:12px 22px;border-radius:10px;margin:6px 8px 6px 0;box-shadow:0 4px 12px #3659d922}form{background:white;padding:24px;border:1px solid #e1e6f0;border-radius:16px;box-shadow:0 8px 28px #19243b08}input{font:inherit;max-width:100%;border:1px solid #ccd4e3;border-radius:8px;padding:12px!important}button{font:inherit;background:#3659d9;color:white;border:0;border-radius:8px;padding:12px 18px!important;cursor:pointer;margin:8px}a:hover,button:hover{filter:brightness(.94)}body:before{content:"COCOLIAN / OFFICE";font-size:12px;letter-spacing:2px;color:#74819b}input[type=file]{display:block;width:100%;background:#f8faff;border:1px dashed #aab9da;padding:24px!important;margin-bottom:16px}footer{margin-top:40px;font-size:12px;color:#8792a6;border-top:1px solid #dfe5f0;padding-top:20px}@media(max-width:600px){body{margin:12px auto!important;padding:20px!important}h1{font-size:26px}a[href^="/edit"]{display:block;text-align:center}button{margin-left:0}}</style></head><body style="font:16px system-ui;max-width:720px;margin:60px auto;padding:24px"><h1>文档工作台</h1><p>请输入访问密钥，使用在线编辑和文档转换。</p><p>'''+html.escape(error)+'''</p><form action="/login" method="post"><input type="password" name="key" required autocomplete="current-password" aria-label="访问密钥" style="width:320px;padding:10px"><button type="submit" style="padding:10px">登录</button></form><footer>Office Lab · Collabora Online / LibreOffice</footer></body></html>'''
    def log_message(self, fmt, *args):
        # Never log bearer tokens or the lab entry key.
        print(json.dumps({'time':time.time(),'method':self.command,'path':urllib.parse.urlsplit(self.path).path,'message':fmt.split('%')[0]}), flush=True)
    def reply(self, code, data=b'', kind='application/json', headers=None):
        if isinstance(data,dict): data=json.dumps(data).encode()
        if isinstance(data,str): data=data.encode()
        self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers()
        if self.command!='HEAD': self.wfile.write(data)
    def reply_file(self, path, attachment=False):
        with path.open('rb') as stream:
            self.send_response(200)
            self.send_header('Content-Type',mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.send_header('Content-Length',str(os.fstat(stream.fileno()).st_size))
            self.send_header('Cache-Control','no-store')
            if attachment: self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+urllib.parse.quote(path.name))
            self.end_headers()
            if self.command!='HEAD': shutil.copyfileobj(stream,self.wfile,1024*1024)
    def do_HEAD(self):
        self.do_GET()
    def do_GET(self):
        p=urllib.parse.urlsplit(self.path); q=urllib.parse.parse_qs(p.query)
        if p.path=='/health': return self.reply(200,{'status':'ok'})
        if p.path in ('/project-homepage.css', '/community-qrcode.jpg'):
            return self.reply_file(Path(__file__).with_name(p.path[1:]))
        if p.path=='/login':
            return self.reply(200,self.login_page(),'text/html; charset=utf-8')
        if p.path=='/' and not (self.authenticated(q) and q.get('key')):
            return self.reply(200,Path(__file__).with_name('project-homepage.html').read_bytes(),'text/html; charset=utf-8',headers={'Content-Security-Policy':"default-src 'none'; img-src 'self' https:; style-src 'self'; base-uri 'none'; form-action 'self'"})
        if p.path=='/auth':
            return self.reply(204 if self.authenticated() else 401,b'',headers={'WWW-Authenticate':'Bearer realm="office-lab"'})
        match=re.fullmatch(r'/wopi/files/([a-z0-9]+)(/contents)?', p.path)
        if match:
            try: document=file_open.resolve(DATA,match[1])
            except FileNotFoundError: return self.reply(404)
            user=TOKENS.get(q.get('access_token',[''])[0])
            if not user: return self.reply(401)
            if p.path.endswith('/contents'): return self.reply_file(document)
            with LOCK:
                return self.reply(200,{'BaseFileName':document.name,'OwnerId':'lab','Size':document.stat().st_size,'UserId':user,'UserFriendlyName':user,'Version':str(document.stat().st_mtime_ns),'UserCanWrite':True,'SupportsUpdate':True,'SupportsLocks':True,'SupportsGetLock':True,'UserCanNotWriteRelative':True,'PostMessageOrigin':os.environ.get('PUBLIC_ORIGIN','https://office.cocolian.cn'),'LastModifiedTime':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(document.stat().st_mtime))})
        if p.path=='/' and self.authenticated(q) and q.get('key'):
            return self.reply(303,b'',headers=self.cookie_headers())
        if not self.authenticated(q):
            if p.path=='/': return self.reply(200,self.login_page(),'text/html; charset=utf-8')
            return self.reply(303,b'',headers={'Location':'/login'})
        if p.path in ('/file-open.js','/file-open.css','/file-open.svg','/ai-panel.js','/ai-panel.css','/ai-session.css','/ai-editor.js'):
            asset=Path(__file__).with_name(p.path[1:])
            return self.reply(200,asset.read_bytes(),mimetypes.guess_type(asset.name)[0] or 'application/octet-stream')
        if p.path=='/api/files':
            with LOCK: return self.reply(200,{'files':file_open.catalogue(DATA)})
        if p.path=='/download':
            try: document=file_open.resolve(DATA,q.get('file',['1'])[0])
            except FileNotFoundError: return self.reply(404)
            return self.reply_file(document,attachment=True)
        if p.path=='/workspace':
            links=' '.join('<a target="_blank" rel="noopener" href="/edit?user='+u+'">'+u+' 在线编辑</a>' for u in ('Alice','Bob'))
            return self.reply(200,'<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Office 文档工作台</title><style>*{box-sizing:border-box}body{font:15px system-ui!important;background:#f4f6fb;color:#19243b;max-width:1000px!important;margin:48px auto!important;padding:32px!important}h1{font-size:32px;letter-spacing:-1px;margin-bottom:8px}h2{font-size:20px;margin-top:32px}p{color:#637089;line-height:1.7}a{color:#3659d9;text-decoration:none}a[href^="/edit"]{display:inline-block;background:#3659d9;color:white;padding:12px 22px;border-radius:10px;margin:6px 8px 6px 0;box-shadow:0 4px 12px #3659d922}form{background:white;padding:24px;border:1px solid #e1e6f0;border-radius:16px;box-shadow:0 8px 28px #19243b08}input{font:inherit;max-width:100%;border:1px solid #ccd4e3;border-radius:8px;padding:12px!important}button{font:inherit;background:#3659d9;color:white;border:0;border-radius:8px;padding:12px 18px!important;cursor:pointer;margin:8px}a:hover,button:hover{filter:brightness(.94)}body:before{content:"COCOLIAN / OFFICE";font-size:12px;letter-spacing:2px;color:#74819b}input[type=file]{display:block;width:100%;background:#f8faff;border:1px dashed #aab9da;padding:24px!important;margin-bottom:16px}footer{margin-top:40px;font-size:12px;color:#8792a6;border-top:1px solid #dfe5f0;padding-top:20px}@media(max-width:600px){body{margin:12px auto!important;padding:20px!important}h1{font-size:26px}a[href^="/edit"]{display:block;text-align:center}button{margin-left:0}}</style></head><body style="font:16px system-ui;max-width:720px;margin:60px auto;padding:24px"><h1>文档工作台</h1><p>在线协同与格式转换，一站完成。</p><h2>在线编辑</h2><p>'+links+'</p><p>选择一个测试身份进入编辑器。Alice 与 Bob 共同编辑同一份文档，修改自动保存。</p><p><a href="/download">下载保存后的 DOCX</a></p><h2>DOCX 转 PDF</h2><p>上传 Word 文档，转换完成后下载 PDF。单个请求最大 200 MB。</p><form action="/convert/forms/libreoffice/convert" method="post" enctype="multipart/form-data" target="_blank"><input type="file" name="files" accept=".docx" required><button type="submit">转换并下载 PDF</button></form><footer>Office Lab · Collabora Online / LibreOffice</footer></body></html>','text/html; charset=utf-8')
        if p.path=='/edit':
            user=q.get('user',['Alice'])[0]
            if user not in ('Alice','Bob'): return self.reply(400)
            file_id=q.get('file',['1'])[0]
            try: document=file_open.resolve(DATA,file_id)
            except FileNotFoundError: return self.reply(404,{'error':'文件不存在'})
            token=next(t for t,u in TOKENS.items() if u==user)
            import xml.etree.ElementTree as ET
            discovery=ET.fromstring(urllib.request.urlopen(render_profile.discovery_url(file_id),timeout=10).read())
            action=next((a for a in discovery.iter('action') if a.get('ext')==document.suffix[1:].lower() and a.get('name')=='edit'),None)
            if action is None: return self.reply(400,{'error':'编辑器暂不支持此格式'})
            url=urllib.parse.urlsplit(action.get('urlsrc'))
            src=url.path+'?WOPISrc='+urllib.parse.quote('http://wopi:8080/wopi/files/'+file_id,safe='')+'&lang='+urllib.parse.quote(EDITOR['language'],safe='')
            page='<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;overscroll-behavior:none}body{position:fixed;inset:0}#f{display:none}iframe[name=editor]{position:fixed;inset:0;display:block;border:0;width:100%;height:100%}</style><link rel="stylesheet" href="/file-open.css"><title>'+html.escape(document.name)+' · '+user+' Office Lab</title></head><body><form id="f" action="'+html.escape(src)+'" method="post" target="editor"><input type="hidden" name="access_token" value="'+token+'"><input type="hidden" name="access_token_ttl" value="0"><input type="hidden" name="ui_defaults" value="UIMode='+html.escape(EDITOR['ui_mode'])+';SavedUIState='+str(EDITOR['use_saved_ui_state']).lower()+';"></form><iframe title="Collabora '+user+'" name="editor" allow="clipboard-read; clipboard-write"></iframe><script>document.getElementById("f").submit()</script><script src="/file-open.js"></script><link rel="stylesheet" href="/ai-panel.css"><script src="/ai-editor.js"></script><script src="/ai-panel.js"></script></body></html>'
            return self.reply(200,page,'text/html')
        return self.reply(404)
    def do_POST(self):
        p=urllib.parse.urlsplit(self.path); q=urllib.parse.parse_qs(p.query)
        if p.path=='/login':
            length=int(self.headers.get('Content-Length','0'))
            if length>4096:return self.reply(413)
            values=urllib.parse.parse_qs(self.rfile.read(length).decode(errors='replace'))
            if hmac.compare_digest(values.get('key',[''])[0].encode(),KEY.encode()):return self.reply(303,b'',headers=self.cookie_headers())
            return self.reply(401,self.login_page('访问密钥无效，请重试。'),'text/html; charset=utf-8')
        if p.path in ('/api/ai/edit','/api/ai/chat','/api/ai/revise'):
            if not self.authenticated(): return self.reply(401,{'error':'请先登录'})
            if self.headers.get('Sec-Fetch-Site')=='cross-site': return self.reply(403)
            origin=self.headers.get('Origin')
            if origin and urllib.parse.urlsplit(origin).netloc!=self.headers.get('Host'): return self.reply(403)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.reply(415)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length <= (262144 if p.path=='/api/ai/revise' else 100000): return self.reply(413)
                self.connection.settimeout(70)
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict): raise ValueError('请求必须为对象')
                file_id=payload.get('file','1')
                if not isinstance(file_id,str): raise ValueError('文件标识无效')
                file_open.resolve(DATA,file_id)
                result=ai_proxy.revise(payload) if p.path=='/api/ai/revise' else ai_proxy.suggest(payload, chat=p.path=='/api/ai/chat')
            except FileNotFoundError: return self.reply(404)
            except (ValueError,TypeError): return self.reply(400,{'error':'请求内容无效'})
            except ai_proxy.AIError as error: return self.reply(503,{'error':str(error)})
            return self.reply(200,result)
        if p.path=='/api/files':
            if not self.authenticated(): return self.reply(401,{'error':'请先登录'})
            if self.headers.get('Sec-Fetch-Site')=='cross-site': return self.reply(403)
            origin=self.headers.get('Origin')
            if origin and urllib.parse.urlsplit(origin).netloc!=self.headers.get('Host'): return self.reply(403)
            try: length=int(self.headers.get('Content-Length','0'))
            except ValueError: return self.reply(400)
            if length<=0 or length>file_open.MAX_UPLOAD: return self.reply(413,{'error':'文件最大 1 GB（1024 MB）'})
            if self.headers.get('Content-Type','')!='application/octet-stream': return self.reply(415)
            self.connection.settimeout(600)
            try: result=file_open.upload_stream(DATA,q.get('name',[''])[0],self.rfile,length)
            except ValueError as error: return self.reply(400,{'error':str(error)})
            except OSError: return self.reply(507,{'error':'上传未完成，请重试或检查可用空间'})
            return self.reply(201,result)
        match=re.fullmatch(r'/wopi/files/([a-z0-9]+)(/contents)?',p.path)
        if not match: return self.reply(404)
        file_id=match[1]
        try: document=file_open.resolve(DATA,file_id)
        except FileNotFoundError: return self.reply(404)
        if not TOKENS.get(q.get('access_token',[''])[0]): return self.reply(401)
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: return self.reply(400)
        if length<0 or length>file_open.MAX_UPLOAD: return self.reply(413)
        if p.path.endswith('/contents'):
            temp=document.parent/('.save-'+uuid.uuid4().hex)
            self.connection.settimeout(600)
            try:
                file_open.receive_exact(self.rfile,temp,length)
                with LOCK:
                    old,expiry=locks.get(file_id,('',0));old=old if expiry>time.time() else ''
                    if old and old!=self.headers.get('X-WOPI-Lock',''):
                        return self.reply(409,b'',headers={'X-WOPI-Lock':old})
                    temp.replace(document)
                    return self.reply(200,b'',headers={'X-WOPI-ItemVersion':str(document.stat().st_mtime_ns)})
            except ValueError: return self.reply(400)
            except OSError: return self.reply(507)
            finally: temp.unlink(missing_ok=True)
        if length>4096: return self.reply(413)
        self.rfile.read(length)
        op=self.headers.get('X-WOPI-Override',''); new=self.headers.get('X-WOPI-Lock','')
        with LOCK:
            old, expiry=locks.get(file_id,('',0)); old=old if expiry>time.time() else ''
            def conflict(): return self.reply(409,b'',headers={'X-WOPI-Lock':old})
            if op=='GET_LOCK': return self.reply(200,b'',headers={'X-WOPI-Lock':old})
            if op in ('LOCK','REFRESH_LOCK'):
                expected=self.headers.get('X-WOPI-OldLock',new)
                if old and old!=expected: return conflict()
                if op=='REFRESH_LOCK' and not old: return conflict()
                locks[file_id]=(new,time.time()+1800); return self.reply(200)
            if op=='UNLOCK':
                if old!=new: return conflict()
                locks.pop(file_id,None); return self.reply(200)
            return self.reply(501)

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
