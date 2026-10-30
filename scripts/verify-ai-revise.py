"""Default document+comments workflow against disposable live documents."""
import base64, io, json, subprocess, sys, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
root=Path(__file__).resolve().parents[1]
out=root/'build/ai-validation';out.mkdir(parents=True,exist_ok=True)
key=base64.b64decode(subprocess.check_output(['ssh','-J','aliserver','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2','kubectl -n office-lab get secret lab-auth -o jsonpath="{.data.key}"'])).decode().strip()
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 context=browser.new_context(viewport={'width':1440,'height':1000})
 assert context.request.post('https://office.cocolian.cn/login',form={'key':key}).ok
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w') as z:
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
  z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
  z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>OpenWen document title.</w:t></w:r></w:p><w:p><w:r><w:t>The project launch date is Monday.</w:t></w:r></w:p><w:p><w:r><w:t>The budget is 100 yuan.</w:t></w:r></w:p><w:p><w:r><w:t>Unchanged final paragraph.</w:t></w:r></w:p>'+(''.join('<w:p><w:r><w:t>Background paragraph '+str(i)+': '+('Unchanged background text. '*20)+'</w:t></w:r></w:p>' for i in range(60)) if '--long-document' in sys.argv else '')+'<w:sectPr/></w:body></w:document>')
 upload=context.request.post('https://office.cocolian.cn/api/files?name=AI-comment-workflow-'+str(int(time.time()))+'.docx',data=buf.getvalue(),headers={'Content-Type':'application/octet-stream'})
 assert upload.status==201
 file_id=upload.json()['id'];page=context.new_page()
 if '--local-assets' in sys.argv:
  for asset in ('ai-editor.js','ai-panel.js','ai-panel.css'):
   page.route('**/'+asset,lambda route,request,asset=asset:route.fulfill(path=str(root/'apps/office-portal'/asset)))
 page.goto('https://office.cocolian.cn/edit?user=Alice&file='+file_id)
 frame=page.frame(name='editor');page.wait_for_timeout(10000)
 if frame.get_by_text('跳过',exact=True).count():frame.get_by_text('跳过',exact=True).click()
 page.evaluate("window.testAI=new OfficeAIEditor(document.querySelector('iframe[name=editor]'))")
 for text,note in [('The project launch date is Monday.','把本段 Monday 改为 Tuesday，保留其他文字。'),('The budget is 100 yuan.','把本段预算数字 100 改为 200，保留其他文字。')]:
  page.evaluate('(text)=>window.testAI.locate(text)',text)
  frame.evaluate('(note)=>app.map.sendUnoCommand(\'.uno:InsertAnnotation\',{Text:{type:\'string\',value:note}})',note)
  page.wait_for_timeout(600)
 seen=set();calls=[]
 if '--real-model' not in sys.argv:
  def model(route):
   payload=route.request.post_data_json
   assert len(payload['comments'])==2
   assert all(c['block_ids'] for c in payload['comments'])
   assert len(payload['blocks'])>=1
   assert sum(len(b['text']) for b in payload['blocks'])<=12000
   assert payload['context'] and len(payload['context'])<=6000
   seen.update(b['id'] for b in payload['blocks']);calls.append(len(payload['blocks']))
   if '--changed-document' in sys.argv:
    frame.evaluate("app.map.sendUnoCommand('.uno:InsertAnnotation',{Text:{type:'string',value:'新增批注：需要重新生成'}})")
    page.wait_for_timeout(600)
   candidate_edits=[{'block_id':'b1','before':'The project launch date is Monday.','after':'The project launch date is Tuesday.','comment_ids':[payload['comments'][0]['id']]},{'block_id':'b2','before':'The budget is 100 yuan.','after':'The budget is 200 yuan.','comment_ids':[payload['comments'][1]['id']]}]
   route.fulfill(json={'summary':'按两条批注修改日期和预算','warnings':[],'edits':[e for e in candidate_edits if e['block_id'] in {b['id'] for b in payload['blocks']}]})
  page.route('**/api/ai/revise',model)
 assert page.locator('.ai-mode').input_value()=='document'
 page.locator('.ai-revise').click()
 expect(page.locator('.ai-send')).to_be_enabled(timeout=180000)
 result=page.locator('.ai-assistant .ai-message-text').last.inner_text();print(result)
 if '--changed-document' in sys.argv:
  assert '文档或批注已变化' in result and '已确认写入 0 处' in result
  print('PASS: changed document/comments block automatic writes');browser.close();sys.exit(0)
 assert '2 处修订' in result
 if '--long-document' in sys.argv:
  assert len(calls)>1 and len(seen)==64
  print('PASS: every long-document paragraph processed across',len(calls),'bounded prompts')
 page.wait_for_timeout(3000)
 response=context.request.get('https://office.cocolian.cn/download?file='+file_id)
 with zipfile.ZipFile(io.BytesIO(response.body())) as z:
  xml=z.read('word/document.xml').decode()
  assert 'word/comments.xml' in z.namelist()
 (out/'comment-workflow.xml').write_text(xml)
 import xml.etree.ElementTree as ET
 tree=ET.fromstring(xml);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 inserted=''.join(e.text or '' for ins in tree.findall('.//w:ins',ns) for e in ins.findall('.//w:t',ns))
 assert 'Tuesday' in inserted and '200' in inserted
 assert len(tree.findall('.//w:del',ns))>=2
 assert tree.find('.//w:p/w:r/w:rPr/w:b',ns) is not None
 assert 'Unchanged final paragraph.' in xml
 page.screenshot(path=str(out/'comment-workflow.png'))
 print('PASS: automatic source+comments prompt, two revisions, original formatting, comments and untouched text retained')
 browser.close()
