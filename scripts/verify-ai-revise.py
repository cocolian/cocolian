"""Default document+comments workflow against disposable live documents."""
import base64, io, json, subprocess, sys, time, zipfile, tempfile
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
  sys.path.insert(0,str(root/'apps/office-portal'));import ai_review
  review_store=tempfile.TemporaryDirectory();review_path=Path(review_store.name)
  def review_api(route):
   payload=route.request.post_data_json
   try: route.fulfill(json=ai_review.update(review_path,payload['file'],payload))
   except ai_review.ReviewConflict as e:route.fulfill(status=409,json={'error':str(e)})
   except ValueError as e:route.fulfill(status=400,json={'error':str(e)})
  page.route('**/api/ai/review',review_api)
  for asset in ('ai-editor.js','ai-panel.js','ai-panel.css','ai-session.css'):
   page.route('**/'+asset,lambda route,request,asset=asset:route.fulfill(path=str(root/'apps/office-portal'/asset)))
 page.goto('https://office.cocolian.cn/edit?user=Alice&file='+file_id)
 frame=page.frame(name='editor');page.wait_for_timeout(10000)
 if frame.get_by_text('跳过',exact=True).count():frame.get_by_text('跳过',exact=True).click()
 assert page.locator('iframe[name=editor]').evaluate('(el)=>el.getBoundingClientRect().width')==1440
 expect(page.locator('#office-ai')).to_have_css('width','560px')
 expected_center=frame.evaluate("()=>{const a=app.activeDocument.activeLayout.getDocumentAnchorSection(),r=app.sectionContainer.getCanvasBoundingClientRect();return r.left+(a.myTopLeft[0]+a.size[0]/2)/app.dpiScale;}")
 panel_center=page.locator('#office-ai').evaluate('(el)=>{const r=el.getBoundingClientRect();return r.left+r.width/2;}')
 assert abs(panel_center-expected_center)<2,(panel_center,expected_center)
 assert page.locator('.ai-history').count()==0
 assert page.locator('#office-ai .ai-stages').count()==0
 expect(frame.locator('#tab-office-session')).to_be_visible()
 assert frame.locator('#navigation-options [role=tab]').count()==3
 frame.locator('#tab-navigator').click();page.wait_for_timeout(500)
 assert frame.locator('#office-session-panel').is_hidden()
 assert frame.locator('#tab-navigator').get_attribute('aria-selected')=='true'
 frame.locator('#tab-quick-find').click()
 expect(frame.locator('#navigator-search-input')).to_be_visible()
 page.wait_for_timeout(800)
 frame.locator('#navigator-search-input').press_sequentially('budget',delay=60)
 frame.locator('.navigation-search-wrapper').get_by_role('button',name='搜索',exact=True).click()
 page.wait_for_timeout(800)
 expect(frame.locator('#quickfind-dock-wrapper .ui-treeview-entry').first).to_be_visible()
 frame.locator('#tab-office-session').click();assert frame.locator('#office-session-panel').is_visible()
 frame.locator('#tab-navigator').focus();frame.locator('#tab-navigator').press('ArrowRight')
 assert frame.locator('#tab-quick-find').get_attribute('aria-selected')=='true'
 frame.locator('#tab-quick-find').press('ArrowRight')
 assert frame.locator('#tab-office-session').get_attribute('aria-selected')=='true'
 page.locator('.ai-instruction').fill('保留原有格式')
 page.locator('.ai-collapse').click();assert page.locator('.ai-shell').is_hidden()
 page.locator('.ai-mini').click();assert page.locator('.ai-instruction').input_value()=='保留原有格式'
 page.locator('.ai-instruction').fill('')
 page.set_viewport_size({'width':390,'height':700});page.wait_for_timeout(600)
 box=page.locator('#office-ai').bounding_box();assert box['x']>=0 and box['x']+box['width']<=390
 page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(600)
 page.screenshot(path=str(out/'floating-composer.png'))
 page.evaluate("window.testAI=new OfficeAIEditor(document.querySelector('iframe[name=editor]'))")
 for text,note in [('The project launch date is Monday.','把本段 Monday 改为 Tuesday，保留其他文字。'),('The budget is 100 yuan.','把本段预算数字 100 改为 200，保留其他文字。')]:
  page.evaluate('(text)=>window.testAI.locate(text)',text)
  frame.evaluate('(note)=>app.map.sendUnoCommand(\'.uno:InsertAnnotation\',{Text:{type:\'string\',value:note}})',note)
  page.wait_for_timeout(600)
 seen=set();calls=[]
 if '--real-model' not in sys.argv:
  def model(route):
   payload=route.request.post_data_json
   assert len(payload['comments'])==(1 if '--review-lifecycle' in sys.argv and len(calls)>0 else 2)
   assert all(c['block_ids'] for c in payload['comments'])
   assert len(payload['blocks'])>=1
   assert sum(len(b['text']) for b in payload['blocks'])<=12000
   assert payload['context'] and len(payload['context'])<=6000
   seen.update(b['id'] for b in payload['blocks']);calls.append(len(payload['blocks']))
   page.locator('.ai-collapse').click();assert page.locator('.ai-mini').is_visible()
   page.locator('.ai-mini').click()
   frame.locator('#tab-navigator').click();frame.locator('#tab-office-session').click()
   assert frame.locator('#office-session-panel .ai-status').last.inner_text()
   if '--changed-document' in sys.argv:
    frame.evaluate("app.map.sendUnoCommand('.uno:InsertAnnotation',{Text:{type:'string',value:'新增批注：需要重新生成'}})")
    page.wait_for_timeout(600)
   first=payload['comments'][0]['id'];second=payload['comments'][-1]['id']
   candidate_edits=([{'block_id':'b1','before':'The project launch date is Monday.','after':'The project launch date is Tuesday.','comment_ids':[first]}] if len(payload['comments'])==2 else [])+[{'block_id':'b2','before':'The budget is 100 yuan.','after':'The budget is 200 yuan.','comment_ids':[second]}]
   if '--history' in sys.argv and len(calls)>1:candidate_edits=[]
   if '--ambiguous-after' in sys.argv:
    candidate_edits[0].update(before='Monday',after='Tuesday')
    candidate_edits[1].update(before='100',after='Monday')
   route.fulfill(json={'comment_results':[{'id':c['id'],'status':'partial' if '--review-lifecycle' in sys.argv and len(calls)>1 else 'complete','reason':'仍需人工核对剩余要求' if '--review-lifecycle' in sys.argv and len(calls)>1 else ''} for c in payload['comments']],'summary':'按批注修改日期和预算','warnings':[],'edits':[e for e in candidate_edits if e['block_id'] in {b['id'] for b in payload['blocks']}]})
  page.route('**/api/ai/revise',model)
 page.locator('.ai-revise').click()
 expect(page.locator('.ai-send')).to_be_enabled(timeout=180000)
 result=frame.locator('#office-session-panel .ai-status').last.inner_text();print(result)
 if '--ambiguous-after' in sys.argv:
  assert '已确认写入 1 处' in result and '不唯一' in result
  print('PASS: a preceding edit cannot create an ambiguous target for the next write');browser.close();sys.exit(0)
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
 frame.locator('#office-session-panel .ai-details').last.locator('summary').click()
 assert frame.locator('#office-session-panel .ai-report').last.inner_text()
 assert page.locator('#office-ai .ai-status').count()==0
 page.screenshot(path=str(out/'comment-workflow.png'))
 if '--history' in sys.argv:
  first=frame.locator('#office-session-panel .ai-status').first.inner_text()
  page.locator('.ai-revise').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=180000)
  assert frame.locator('#office-session-panel .office-session-record').count()==2
  assert frame.locator('#office-session-panel .ai-status').first.inner_text()==first
  frame.locator('#tab-navigator').click();frame.locator('#tab-office-session').click()
  assert frame.locator('#office-session-panel .office-session-record').count()==2
  print('PASS: native outline/search/session tabs, keyboard navigation, and retained execution history')
 if '--cross-user' in sys.argv:
  bob_context=browser.new_context(viewport={'width':1440,'height':1000})
  assert bob_context.request.post('https://office.cocolian.cn/login',form={'key':key}).ok
  bob=bob_context.new_page()
  if '--local-assets' in sys.argv:
   for asset in ('ai-editor.js','ai-panel.js','ai-panel.css','ai-session.css'):
    bob.route('**/'+asset,lambda route,request,asset=asset:route.fulfill(path=str(root/'apps/office-portal'/asset)))
   bob.route('**/api/ai/review',review_api)
  bob.goto('https://office.cocolian.cn/edit?user=Bob&file='+file_id);bob.wait_for_timeout(10000)
  bf=bob.frame(name='editor')
  if bf.get_by_text('跳过',exact=True).count():bf.get_by_text('跳过',exact=True).click()
  bf.wait_for_function('window.app?.officeAIReview');bf.evaluate('()=>app.officeAIReview.ready')
  assert bf.evaluate("Object.values(app.officeAIReview.statuses).filter(x=>x.state==='pending_review').length")==2
  bf.evaluate("app.map.sendUnoCommand('.uno:AcceptAllTrackedChanges')");bf.evaluate('()=>app.officeAIReview.queue')
  assert not bf.evaluate('app.officeAIReview.error'),bf.evaluate('app.officeAIReview.error')
  assert bf.evaluate("app.officeAIReview.adapter.comments().every(c=>['true',true].includes(c.object.sectionProperties.data.resolved))")
  frame.evaluate('()=>app.officeAIReview.enqueue(()=>app.officeAIReview.sync())')
  assert frame.evaluate("Object.values(app.officeAIReview.statuses).every(x=>x.state==='resolved')")
  assert bf.evaluate("app.officeAIReview.adapter.comments().every(c=>c.object.sectionProperties.data.author==='Alice')")
  print('PASS: Bob accepts Alice AI revisions; both views synchronize resolved comments and preserve original authors')
  bob_context.close()
 if '--review-lifecycle' in sys.argv:
  page.reload();page.wait_for_timeout(10000);frame=page.frame(name='editor')
  frame.wait_for_function('window.app?.officeAIReview')
  frame.evaluate('()=>app.officeAIReview.ready')
  def states():return frame.evaluate('Object.values(app.officeAIReview.statuses).map(x=>x.state)')
  def unresolved():return frame.evaluate("app.officeAIReview.adapter.comments().filter(c=>!['true',true].includes(c.object.sectionProperties.data.resolved)).length")
  assert states().count('pending_review')==2,states()
  count=len(calls);page.locator('.ai-revise').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=30000)
  assert len(calls)==count and '等待审阅' in frame.locator('#office-session-panel .ai-status').last.inner_text()
  rows=frame.evaluate('()=>app.officeAIReview.raw()')
  project=[r for r in rows if 'proj' in r.get('description','')]
  assert len(project)==2,rows
  def review_one(row,accept=True):
   command='AcceptTrackedChange' if accept else 'RejectTrackedChange'
   frame.evaluate("(arg)=>app.map.sendUnoCommand('.uno:'+arg.command,{[arg.command]:{type:'unsigned short',value:arg.id}})",{'command':command,'id':row['index']})
   frame.evaluate('()=>app.officeAIReview.queue')
   assert not frame.evaluate('app.officeAIReview.error'),frame.evaluate('app.officeAIReview.error')
  review_one(project[0]);assert unresolved()==2
  assert states().count('pending_review')==2,states()
  review_one(project[1]);assert unresolved()==1
  assert states().count('resolved')==1,states()
  frame.evaluate("app.map.sendUnoCommand('.uno:RejectAllTrackedChanges')")
  frame.evaluate('()=>app.officeAIReview.queue')
  assert unresolved()==1 and states().count('ready')==1,states()
  ident=frame.evaluate("app.officeAIReview.adapter.comments().find(c=>!['true',true].includes(c.object.sectionProperties.data.resolved)).id")
  def toggle():
   frame.evaluate("(id)=>app.map.sendUnoCommand('.uno:ResolveComment',{Id:{type:'string',value:String(id)}})",ident)
   frame.evaluate('()=>app.officeAIReview.queue')
  toggle();assert unresolved()==0
  toggle();assert unresolved()==1 and states().count('ready')==1,states()
  page.locator('.ai-revise').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=180000)
  print('Partial:',frame.locator('#office-session-panel .ai-status').last.inner_text())
  assert len(calls)==count+1
  frame.evaluate("app.map.sendUnoCommand('.uno:AcceptAllTrackedChanges')")
  frame.evaluate('()=>app.officeAIReview.queue')
  assert unresolved()==1 and states().count('ready')==1,states()
  frame.evaluate("app.map.sendUnoCommand('.uno:Undo')")
  frame.evaluate('()=>app.officeAIReview.queue')
  assert states().count('pending_review')==1 and unresolved()==1,states()
  frame.evaluate("app.map.sendUnoCommand('.uno:AcceptAllTrackedChanges')")
  frame.evaluate('()=>app.officeAIReview.queue')
  assert states().count('ready')==1 and unresolved()==1,states()
  print('PASS: undo restores pending links without resolving comments')
  print('PASS: pending survives reload and skips repeat; partial acceptance stays pending; full acceptance resolves; reject and manual reopen restore ready; partial completion stays unresolved')
 print('PASS: automatic source+comments prompt, two revisions, original formatting, comments and untouched text retained')
 browser.close()
