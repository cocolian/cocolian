"""Real HTTPS editor validation using disposable documents and a mocked model response."""
import subprocess,base64,json,io,zipfile,time,urllib.parse,sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
root=Path(__file__).resolve().parents[1]
(root/'build/ai-validation').mkdir(parents=True,exist_ok=True)
key=base64.b64decode(subprocess.check_output(['ssh','-J','aliserver','-o','HostKeyAlias=rdp.cocolian.cn','-o','StrictHostKeyChecking=yes','shamphone@192.168.99.2','kubectl -n office-lab get secret lab-auth -o jsonpath="{.data.key}"'])).decode().strip()
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 context=browser.new_context(viewport={'width':1440,'height':1000})
 context.request.post('https://office.cocolian.cn/login',form={'key':key})
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w') as z:
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
  z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
  z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>OpenWen AI original sentence.</w:t></w:r></w:p><w:sectPr/></w:body></w:document>')
 response=context.request.post('https://office.cocolian.cn/api/files?name=AI-validation-'+str(int(time.time()))+'.docx',data=buf.getvalue(),headers={'Content-Type':'application/octet-stream'})
 assert response.status==201,response.status
 file_id=response.json()['id']
 page=context.new_page()
 if '--local-assets' in sys.argv:
  for asset in ('ai-editor.js','ai-panel.js','ai-panel.css'):
   page.route('**/'+asset,lambda route,request,asset=asset:route.fulfill(path=str(root/'apps/office-portal'/asset)))
 page.goto('https://office.cocolian.cn/edit?user=Alice&file='+file_id)
 page.wait_for_timeout(10000)
 frame=page.frame(name='editor')
 print(frame.evaluate('''()=>({url:location.pathname,app:!!window.app,map:!!window.app?.map,doc:window.app?.map?._docLayer?._docType,layout:window.app?.activeDocument?.activeLayout?.type,selection:typeof window.app?.map?._docLayer?._onTextSelectionMsg})'''))
 page.locator('#office-ai').wait_for()
 page.wait_for_timeout(1500)
 assert page.locator('#office-ai').evaluate('(el)=>el.getBoundingClientRect().width')==200
 assert page.locator('iframe[name=editor]').evaluate('(el)=>el.getBoundingClientRect().right')==1240
 page.screenshot(path=str(root/'build/ai-validation/sidebar.png'))
 handle=page.locator('.ai-resizer');handle.focus();page.keyboard.press('ArrowLeft')
 assert page.locator('#office-ai').evaluate('(el)=>el.getBoundingClientRect().width')==220
 page.locator('.ai-close').click()
 assert page.locator('iframe[name=editor]').evaluate('(el)=>el.getBoundingClientRect().width')==1440
 page.locator('.ai-reopen').click()
 if '--real-model' not in sys.argv:
  page.route('**/api/ai/chat',lambda route:route.fulfill(json={'suggestion':'可以帮你完善文档。'}))
 page.locator('.ai-instruction').fill('你能帮我做什么？')
 page.locator('.ai-send').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=70000)
 assert page.locator('.ai-assistant').count()==1
 assert page.locator('.ai-instruction').input_value()==''
 if frame.get_by_text('跳过',exact=True).count():frame.get_by_text('跳过',exact=True).click()
 frame.evaluate("app.map.focus();app.map.sendUnoCommand('.uno:SelectAll')")
 page.wait_for_timeout(1000)
 page.locator('.ai-capture').click();page.wait_for_timeout(1000)
 assert 'OpenWen AI original sentence.' in page.locator('.ai-context span').inner_text()
 if '--real-model' not in sys.argv:
  page.route('**/api/ai/edit',lambda route:route.fulfill(json={'suggestion':'OpenWen AI revised sentence.'}))
 frame.evaluate("app.map.sendUnoCommand('.uno:InsertAnnotation',{Text:{type:'string',value:'Improve wording'}})")
 page.wait_for_timeout(1000)
 page.locator('.ai-comments').click()
 assert page.locator('.ai-comment option').count()>1
 page.locator('.ai-comment').select_option(index=1)
 assert page.locator('.ai-instruction').input_value()=='Improve wording'
 frame.evaluate("app.map.focus();app.map.sendUnoCommand('.uno:SelectAll')")
 page.wait_for_timeout(700)
 page.locator('.ai-capture').click();page.wait_for_timeout(700)
 page.locator('.ai-instruction').fill('将原文替换为这句英文，仅返回这一句，不添加其他内容：OpenWen AI revised sentence.')
 page.locator('.ai-send').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=70000);page.locator('.ai-accept').last.wait_for(state='visible',timeout=1000)
 assert '<think>' not in page.locator('.ai-assistant .ai-message-text').last.inner_text()
 frame.evaluate("app.map.focus()")
 page.keyboard.press("ArrowRight")
 page.wait_for_timeout(500)
 page.locator('.ai-accept').last.click();page.wait_for_timeout(700)
 print('stale',page.locator('#office-ai [role=status]').inner_text());assert '选择' in page.locator('#office-ai [role=status]').inner_text() or '选区' in page.locator('#office-ai [role=status]').inner_text()
 frame.evaluate("app.map.sendUnoCommand('.uno:SelectAll')")
 page.wait_for_timeout(700)
 page.locator('.ai-capture').click();page.wait_for_timeout(700)
 page.locator('.ai-instruction').fill('将原文替换为这句英文，仅返回这一句，不添加其他内容：OpenWen AI revised sentence.')
 page.locator('.ai-send').click();expect(page.locator('.ai-send')).to_be_enabled(timeout=70000);page.locator('.ai-accept').last.wait_for(state='visible',timeout=1000)
 assert '<think>' not in page.locator('.ai-assistant .ai-message-text').last.inner_text()
 page.locator('.ai-close').click()
 page.locator('.ai-reopen').click()
 page.locator('.ai-accept').last.click();page.wait_for_timeout(2000)
 print('apply',page.locator('#office-ai [role=status]').inner_text())
 print('track',frame.evaluate("app.map.stateChangeHandler.getItemValue('.uno:TrackChanges')"))
 frame.evaluate("app.map.save(false,false)")
 page.wait_for_timeout(3000)
 response=context.request.get('https://office.cocolian.cn/download?file='+file_id)
 with zipfile.ZipFile(io.BytesIO(response.body())) as z: xml=z.read('word/document.xml').decode()
 (root/'build/ai-validation/saved.xml').write_text(xml);print('revision', '<w:ins' in xml,'<w:del' in xml,'revised sentence' in xml)
 assert '<w:ins' in xml and '<w:del' in xml and 'revised sentence' in xml
 page.screenshot(path=str(root/'build/ai-validation/revision.png'))
 browser.close()
