"""Isolated end-to-end test. Uses disposable documents and a random lab key."""
import os, json, secrets, subprocess, time, shutil, hashlib, urllib.parse, urllib.request, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path('/home/codex/projects/cocolian-office');out=root/'artifacts/file-open-20261017';out.mkdir(exist_ok=True)
source=Path('/home/codex/projects/cocolian/apps/office-portal');key=secrets.token_urlsafe(32);result={}
for filename in ('file_open.py','file-open.js','file-open.css','file-open.svg'):
 shutil.copy2(source/filename,out/filename)
s=(source/'server.py').read_text().replace("Path('/data')","Path(os.environ['SOURCE_TEST_DATA'])").replace('http://collabora:9980','http://127.0.0.1:19980').replace("src=url.path+","src=urllib.parse.urlunsplit((url.scheme,url.netloc,url.path,'',''))+").replace('http://wopi:8080','http://127.0.0.1:18080').replace("('0.0.0.0',8000)","('127.0.0.1',18080)")
(out/'host.py').write_text(s);data=out/('data-'+secrets.token_hex(4));data.mkdir();fixture=root/'tests/fixtures/source-build-smoke.docx';shutil.copy2(fixture,data/'collaboration.docx');original=(data/'collaboration.docx').read_bytes();(out/'editor.json').write_text(json.dumps({'language':'zh-CN','ui_mode':'tabbed','use_saved_ui_state':False}))
env=dict(os.environ,LAB_KEY=key,SOURCE_TEST_DATA=str(data),PUBLIC_ORIGIN='http://127.0.0.1:18080',NO_PROXY='127.0.0.1,localhost',no_proxy='127.0.0.1,localhost');log=(out/'host.log').open('w');host=subprocess.Popen(['python3',str(out/'host.py')],env=env,stdout=log,stderr=log)
try:
 time.sleep(.5)
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True,chromium_sandbox=True);context=browser.new_context(viewport={'width':1440,'height':1000});api=context.request;base='http://127.0.0.1:18080'
  assert api.post(base+'/api/files?name=test.docx',data=original,headers={'Content-Type':'application/octet-stream'}).status==401
  assert api.post(base+'/login',form={'key':key}).ok
  def upload(name):return api.post(base+'/api/files?name='+urllib.parse.quote(name),data=original,headers={'Content-Type':'application/octet-stream'})
  first=upload('知识库测试.docx');assert first.status==201,first.text();first=first.json();second=upload('知识库测试.docx').json();assert first['id']!=second['id']
  assert upload('../bad.docx').status==400;assert upload('bad.html').status==400
  assert api.post(base+'/api/files?name=x.docx',data=original,headers={'Content-Type':'application/octet-stream','Origin':'https://invalid.example'}).status==403
  token=hashlib.sha256((key+'Alice').encode()).hexdigest()
  wopi=lambda id:base+'/wopi/files/'+id+'?access_token='+token
  assert api.get(wopi(first['id'])).json()['BaseFileName']=='知识库测试.docx'
  assert api.post(wopi(first['id']),headers={'X-WOPI-Override':'LOCK','X-WOPI-Lock':'one'}).ok
  assert api.post(wopi(second['id']),headers={'X-WOPI-Override':'LOCK','X-WOPI-Lock':'two'}).ok
  assert api.post(base+'/wopi/files/'+first['id']+'/contents?access_token='+token,data=original,headers={'X-WOPI-Lock':'wrong'}).status==409
  for item,lock in [(first,'one'),(second,'two')]:assert api.post(wopi(item['id']),headers={'X-WOPI-Override':'UNLOCK','X-WOPI-Lock':lock}).ok
  result['api_and_lock_isolation']=True
  page=context.new_page();page.goto(base+'/edit?user=Alice');frame=page.frame_locator('iframe[name=editor]');frame.locator('#document-canvas').wait_for(state='visible',timeout=90000)
  try:frame.get_by_role('button',name='跳过',exact=True).click(timeout=1500)
  except Exception:pass
  button=frame.locator('#office-open-file');button.wait_for(timeout=20000);save=frame.locator('.notebookbar-shortcuts-bar button[id^=save][id$="-button"]');assert button.bounding_box()['x']<save.bounding_box()['x']
  button.click();page.locator('#file-picker').wait_for(state='visible');page.screenshot(path=str(out/'picker.png'))
  page.locator('#knowledge-search').fill('知识库测试')
  with page.expect_popup() as opened:page.get_by_role('button',name='打开 知识库测试.docx',exact=True).first.click()
  child=opened.value;child.wait_for_url('**/edit?user=Alice&file=*');childframe=child.frame_locator('iframe[name=editor]');childframe.locator('#document-canvas').wait_for(state='visible',timeout=90000)
  try:childframe.get_by_role('button',name='跳过',exact=True).click(timeout=1500)
  except Exception:pass
  childframe.locator('#document-canvas').click(position={'x':300,'y':200});child.keyboard.press('Control+End');marker='KNOWLEDGE_SAVE_'+secrets.token_hex(5);child.keyboard.press('Enter');child.keyboard.insert_text(marker);child.keyboard.press('Control+s')
  file_id=urllib.parse.parse_qs(urllib.parse.urlsplit(child.url).query)['file'][0];saved=next((data/'knowledge-base'/file_id).iterdir())
  for _ in range(60):
   with zipfile.ZipFile(saved) as archive:
    if marker in archive.read('word/document.xml').decode():break
   time.sleep(1)
  else:raise AssertionError('Uploaded file WOPI save failed')
  assert (data/'collaboration.docx').read_bytes()==original
  other=second if file_id==first['id'] else first;assert next((data/'knowledge-base'/other['id']).iterdir()).read_bytes()==original
  result['knowledge_open_edit_save_without_overwrite']=True;child.close()
  page.locator('#upload-tab').click();page.locator('#local-document').set_input_files({'name':'本地上传.docx','mimeType':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','buffer':original})
  with page.expect_popup() as uploaded:page.get_by_role('button',name='上传并打开',exact=True).click()
  uploaded=uploaded.value;uploaded.wait_for_url('**/edit?user=Alice&file=*');uploaded.frame_locator('iframe[name=editor]').locator('#document-canvas').wait_for(state='visible',timeout=90000)
  result['local_upload_opens_editor']=True;result['button_before_save']=True
  result['persistent_catalogue']=len(api.get(base+'/api/files').json()['files'])==4
  assert result['persistent_catalogue']
  browser.close()
  host.terminate();host.wait(timeout=10)
  host=subprocess.Popen(['python3',str(out/'host.py')],env=env,stdout=log,stderr=log);time.sleep(.5)
  with urllib.request.urlopen(urllib.request.Request(base+'/api/files',headers={'Authorization':'Bearer '+key})) as response:
   assert len(json.load(response)['files'])==4
  result['restart_persistence']=True
finally:
 host.terminate();host.wait(timeout=10);log.close();(out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
