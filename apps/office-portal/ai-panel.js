(() => {
 'use strict';
 const frame=document.querySelector('iframe[name=editor]');if(!frame)return;
 const adapter=new OfficeAIEditor(frame);
 const panel=document.createElement('section');panel.id='office-ai';panel.setAttribute('aria-label','AI 批注修改');
 panel.innerHTML=`<button type="button" class="ai-mini" hidden aria-label="展开修改框" aria-expanded="false">✦ 批注修改</button><div class="ai-shell"><header><div><span class="ai-spark" aria-hidden="true">✦</span><strong>按批注修改</strong></div><button type="button" class="ai-collapse" aria-label="收起修改框" aria-expanded="true" title="收起">⌄</button></header><form class="ai-composer"><label class="ai-input-label" for="ai-input">补充修改要求，可留空</label><textarea id="ai-input" class="ai-instruction" maxlength="2000" rows="1" placeholder="补充修改要求，可留空"></textarea><div class="ai-actions"><small>自动读取原文和全部未解决批注</small><button type="button" class="ai-cancel" hidden>停止</button><button type="submit" class="ai-send ai-revise">按批注修改 <span aria-hidden="true">↑</span></button></div></form><div class="ai-task" hidden><ol class="ai-stages" aria-label="修改进度"><li data-stage="read">读取批注</li><li data-stage="generate">生成修改</li><li data-stage="apply">写入修订</li></ol><p class="ai-status" role="status" aria-live="polite"></p><details class="ai-details" hidden><summary>修改详情</summary><div class="ai-report"></div></details></div></div>`;
 document.body.append(panel);
 const find=s=>panel.querySelector(s),input=find('.ai-instruction'),send=find('.ai-send'),cancel=find('.ai-cancel'),mini=find('.ai-mini'),status=find('[role=status]');
 let controller=null,collapsed=false,positionRequest=0,observedCanvas=null;
 const canvasObserver=new ResizeObserver(()=>schedulePosition());
 function position(){
  positionRequest=0;
  const frameRect=frame.getBoundingClientRect();let area={left:frameRect.left,right:frameRect.right,bottom:frameRect.bottom};
  try{
   const app=adapter.app,container=app?.sectionContainer,anchor=app?.activeDocument?.activeLayout.getDocumentAnchorSection();
   if(container&&anchor){const rect=container.getCanvasBoundingClientRect(),scale=app.dpiScale||1;area={left:frameRect.left+rect.left+anchor.myTopLeft[0]/scale,right:frameRect.left+rect.left+(anchor.myTopLeft[0]+anchor.size[0])/scale,bottom:frameRect.top+rect.top+(anchor.myTopLeft[1]+anchor.size[1])/scale};}
  }catch{/* Use the editor frame until its document canvas is ready. */}
  const available=Math.max(0,Math.min(innerWidth,area.right)-Math.max(0,area.left));
  const width=Math.min(560,Math.max(0,innerWidth-24),Math.max(160,available-32));
  const center=Math.max(width/2+12,Math.min(innerWidth-width/2-12,(area.left+area.right)/2));
  panel.style.left=center+'px';panel.style.width=width+'px';panel.style.bottom=Math.max(42,innerHeight-area.bottom+16)+'px';
 }
 function schedulePosition(){if(!positionRequest)positionRequest=requestAnimationFrame(position);}
 function fold(value){collapsed=value;panel.classList.toggle('is-collapsed',value);mini.hidden=!value;find('.ai-shell').hidden=value;find('.ai-collapse').setAttribute('aria-expanded',String(!value));if(!value)input.focus();schedulePosition();}
 find('.ai-collapse').onclick=()=>fold(true);mini.onclick=()=>fold(false);
 function stage(name,text){
  find('.ai-task').hidden=false;panel.dataset.state=name;status.textContent=text;
  const order=['read','generate','apply'],index=order.indexOf(name);
  for(const item of panel.querySelectorAll('[data-stage]')){const n=order.indexOf(item.dataset.stage);item.classList.toggle('active',n===index);item.classList.toggle('done',name==='complete'||(index>=0&&n<index));if(n===index)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current');}
  mini.textContent='✦ '+text;
 }
 function report(text){find('.ai-report').textContent=text;find('.ai-details').hidden=!text;}
 function fitInput(){input.style.height='auto';input.style.height=Math.min(120,Math.max(36,input.scrollHeight))+'px';}
 input.oninput=fitInput;
 cancel.onclick=()=>controller?.abort();
 find('form').onsubmit=async e=>{
  e.preventDefault();if(controller)return;
  const instruction=input.value.trim();controller=new AbortController();const signal=controller.signal;
  send.disabled=true;input.disabled=true;cancel.hidden=false;find('.ai-details').open=false;report('');
  stage('read','正在读取原文和批注…');
  try{
   const snapshot=await adapter.readDocument();
   // Return typing focus to the optional instruction instead of the selected document.
   (collapsed?mini:find('.ai-collapse')).focus();
   if(!snapshot.comments.length&&!instruction)throw Error('没有未解决批注，请补充修改要求后再试。');
   if(signal.aborted)throw new DOMException('已停止','AbortError');
   const chunks=[];let chunk=[],length=0;
   for(const block of snapshot.blocks){if(chunk.length&&(length+block.text.length>12000||chunk.length>=200)){chunks.push(chunk);chunk=[];length=0;}chunk.push(block);length+=block.text.length;}if(chunk.length)chunks.push(chunk);
   const perBlock=Math.max(0,Math.floor(5500/snapshot.blocks.length)-12);
   const synopsis=snapshot.blocks.map(b=>b.id+': '+b.text.slice(0,perBlock)+(b.text.length>perBlock?'…':'')).join('\n').slice(0,6000);
   const edits=[],warnings=[],summaries=[];
   for(let i=0;i<chunks.length;i++){
    stage('generate',`已读取 ${snapshot.comments.length} 条批注，正在生成修改${chunks.length>1?`（${i+1}/${chunks.length}）`:''}…`);
    const response=await fetch('/api/ai/revise',{method:'POST',signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({file:new URL(location.href).searchParams.get('file')||'1',instruction,blocks:chunks[i],comments:snapshot.comments,context:synopsis})});
    const data=await response.json();if(!response.ok)throw Error(data.error||'生成修改失败');
    edits.push(...data.edits);warnings.push(...data.warnings);if(data.summary)summaries.push(data.summary);
   }
   if(signal.aborted)throw new DOMException('已停止','AbortError');
   let applied=0;
   if(edits.length){
    stage('apply',`正在写入 ${edits.length} 处修订…`);
    const wasInert=frame.inert;frame.inert=true;
    try{applied=await adapter.applyDocumentPlan(snapshot,edits,(n,total)=>stage('apply',`正在写入修订 ${n}/${total}…`),signal);}finally{frame.inert=wasInert;}
   }
   adapter.app?.searchService?.resetSelection();
   const addressed=new Set(edits.flatMap(edit=>edit.comment_ids));
   const unchecked=snapshot.comments.filter(comment=>!addressed.has(comment.id));
   stage('complete',applied?`已生成 ${applied} 处修订${unchecked.length?`，${unchecked.length} 条批注需核对`:''}。请在文档中接受或拒绝。`:'未生成修改，请检查批注或补充要求。');
   report([...new Set(summaries)].join('\n')+(warnings.length?'\n需核对：\n'+[...new Set(warnings)].join('\n'):'')+(unchecked.length?'\n未处理的批注：\n'+unchecked.map(c=>c.text).join('\n'):''));
  }catch(e){stage(signal.aborted?'stopped':'error',e.name==='AbortError'?'已停止，请核对文档中已写入的修订。':e.message);}finally{controller=null;send.disabled=false;input.disabled=false;cancel.hidden=true;schedulePosition();}
 };
 input.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();find('form').requestSubmit();}};
 const connect=()=>{try{adapter.connect();const canvas=adapter.app?.sectionContainer?.canvas;if(canvas&&canvas!==observedCanvas){canvasObserver.disconnect();canvasObserver.observe(canvas);observedCanvas=canvas;}schedulePosition();return true;}catch{return false;}};
 frame.addEventListener('load',()=>{controller?.abort();connect();});
 const timer=setInterval(()=>{if(connect())clearInterval(timer);},500);
 window.addEventListener('resize',schedulePosition);new ResizeObserver(schedulePosition).observe(panel);position();
})();
