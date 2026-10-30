(() => {
 'use strict';
 const frame=document.querySelector('iframe[name=editor]');if(!frame)return;
 const adapter=new OfficeAIEditor(frame);
 // Keep execution history inside Collabora's existing left navigation.
 class SessionLog {
  constructor(){this.records=[];this.selected='tab-office-session';this.explicit=false;this.root=document.createElement('section');this.root.id='office-session-panel';this.root.className='office-session-panel';this.root.setAttribute('role','tabpanel');this.root.setAttribute('aria-labelledby','tab-office-session');this.root.setAttribute('tabindex','0');this.root.innerHTML='<section class="office-review-summary" hidden aria-label="批注审阅状态"></section><div class="office-session-empty">在文档中添加批注，发送修改要求后，可在这里查看执行进度和结果。</div>';}
  install(){
   adapter.connect();const nav=adapter.map.navigator,doc=frame.contentDocument;
   const tabs=doc.getElementById('navigation-options');
   if(!nav||!tabs||!doc.getElementById('tab-navigator')||!doc.getElementById('tab-quick-find'))return false;
   if(this.tabs===tabs&&doc.getElementById('tab-office-session'))return true;
   this.nav=nav;this.tabs=tabs;nav.navigationPanel.classList.add('office-session-navigation');
   if(!doc.getElementById('office-session-style')){const link=doc.createElement('link');link.id='office-session-style';link.rel='stylesheet';link.href=new URL('/ai-session.css',location.href).href;doc.head.append(link);}
   for(const [id,label] of [['tab-navigator','大纲'],['tab-quick-find','搜索']]){const tab=doc.getElementById(id);tab.setAttribute('aria-label',label);tab.title=label;const span=doc.createElement('span');span.className='office-nav-label';span.textContent=label;tab.append(span);}
   const tab=doc.createElement('button');tab.id='tab-office-session';tab.className='tab';tab.type='button';tab.setAttribute('role','tab');tab.setAttribute('aria-controls',this.root.id);tab.setAttribute('aria-label','会话');tab.title='会话';tab.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 4h16v12H9l-5 4V4M8 8h8M8 12h5"/></svg><span class="office-nav-label">会话</span>';tabs.append(tab);nav.navigationPanel.append(this.root);
   if(this.wrappedNav!==nav){
    this.wrappedNav=nav;const original=nav.switchNavigationTab;
    nav.switchNavigationTab=(id)=>{
     // Native outline refreshes must not take the user away from session history.
     if(id==='tab-navigator'&&this.selected==='tab-office-session'&&!this.explicit&&!nav.focusQuickFind){this.activate();return;}
     original.call(nav,id);this.selected=id;this.root.hidden=id!=='tab-office-session';
     if(id==='tab-office-session')this.activate();
    };
   }
   tabs.addEventListener('click',()=>{this.explicit=true;setTimeout(()=>{this.explicit=false;},0);},true);
   tab.onclick=()=>nav.switchNavigationTab(tab.id);
   tabs.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)||!e.target.closest('[role=tab]'))return;
    e.preventDefault();e.stopImmediatePropagation();const all=[...tabs.querySelectorAll('[role=tab]')];let index=all.indexOf(e.target.closest('[role=tab]'));
    index=e.key==='Home'?0:e.key==='End'?all.length-1:(index+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;
    this.explicit=true;try{nav.switchNavigationTab(all[index].id);}finally{this.explicit=false;}all[index].focus();
   },true);
   this.show();return true;
  }
  activate(){
   if(!this.nav)return;this.selected='tab-office-session';
   for(const tab of this.tabs.querySelectorAll('[role=tab]')){const selected=tab.id===this.selected;tab.classList.toggle('selected',selected);tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;}
   for(const pane of [this.nav.navigatorDockWrapper,this.nav.quickFindWrapper,this.nav.presentationControlsWrapper])if(pane)pane.style.display='none';
   this.root.hidden=false;
  }
  show(){
   if(!this.nav){try{if(!this.install())return false;}catch{return false;}}
   this.nav.showNavigationPanel(false);this.activate();this.root.scrollTop=this.root.scrollHeight;schedulePosition();return true;
  }
  start(instruction){
   try{this.install();}catch{/* Attach pending history when the document finishes loading. */}
   this.root.querySelector('.office-session-empty')?.remove();
   const record=document.createElement('article');record.className='office-session-record';record.innerHTML='<h3></h3><div class="office-session-request"></div><ol class="ai-stages" aria-label="修改进度"><li data-stage="read">读取批注</li><li data-stage="generate">生成修改</li><li data-stage="apply">写入修订</li></ol><p class="ai-status" role="status" aria-live="polite"></p><details class="ai-details" hidden><summary>修改详情</summary><div class="ai-report"></div></details>';
   record.querySelector('h3').textContent='批注修改 · '+new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});record.querySelector('.office-session-request').textContent=instruction||'按全部未解决批注修改原文';
   this.root.append(record);this.records.push(record);if(this.records.length>20)this.records.shift().remove();this.show();return record;
  }
  update(record,name,text){
   const follow=this.root.scrollHeight-this.root.scrollTop-this.root.clientHeight<48;
   record.dataset.state=name;record.querySelector('.ai-status').textContent=text;
   const order=['read','generate','apply'],index=order.indexOf(name);
   for(const item of record.querySelectorAll('[data-stage]')){const n=order.indexOf(item.dataset.stage);item.classList.toggle('active',n===index);item.classList.toggle('done',name==='complete'||(index>=0&&n<index));if(n===index)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current');}
   if(follow)this.root.scrollTop=this.root.scrollHeight;
  }
  review(statuses,error,comments=[]){
   const box=this.root.querySelector('.office-review-summary');box.replaceChildren();box.hidden=!error&&!Object.keys(statuses).length;
   const labels={pending_review:'待审阅',needs_review:'待核对',ready:'待修改',resolved:'已解决',accepted:'已接受，正在解决批注',generating:'处理中'};
   const title=document.createElement('strong');title.textContent=error||'批注审阅';box.append(title);
   for(const c of comments){const state=statuses[c.key];if(!state)continue;const row=document.createElement('p');row.textContent=(labels[state.state]||'待核对')+' · '+c.text.slice(0,45);box.append(row);}
  }
  report(record,text){record.querySelector('.ai-report').textContent=text;record.querySelector('.ai-details').hidden=!text;}
 }
 const sessions=new SessionLog();const review=new OfficeAIReview(adapter,(...args)=>sessions.review(...args));let currentTask=null;
 const panel=document.createElement('section');panel.id='office-ai';panel.setAttribute('aria-label','AI 批注修改');
 panel.innerHTML=`<button type="button" class="ai-mini" hidden aria-label="展开修改框" aria-expanded="false">✦ 批注修改</button><div class="ai-shell"><header><div><span class="ai-spark" aria-hidden="true">✦</span><strong>按批注修改</strong></div><div><button type="button" class="ai-sessions" title="查看会话记录">会话</button><button type="button" class="ai-collapse" aria-label="收起修改框" aria-expanded="true" title="收起">⌄</button></div></header><form class="ai-composer"><label class="ai-input-label" for="ai-input">补充修改要求，可留空</label><textarea id="ai-input" class="ai-instruction" maxlength="2000" rows="1" placeholder="补充修改要求，可留空"></textarea><div class="ai-actions"><small>自动读取原文和全部未解决批注</small><button type="button" class="ai-cancel" hidden>停止</button><button type="submit" class="ai-send ai-revise">按批注修改 <span aria-hidden="true">↑</span></button></div></form></div>`;
 document.body.append(panel);
 const find=s=>panel.querySelector(s),input=find('.ai-instruction'),send=find('.ai-send'),cancel=find('.ai-cancel'),mini=find('.ai-mini');
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
  panel.dataset.state=name;sessions.update(currentTask,name,text);
  mini.textContent=['read','generate','apply'].includes(name)?'✦ 批注修改 · 进行中':'✦ 批注修改';
 }
 function report(text){sessions.report(currentTask,text);}
 find('.ai-sessions').onclick=()=>sessions.show();
 function fitInput(){input.style.height='auto';input.style.height=Math.min(120,Math.max(36,input.scrollHeight))+'px';}
 input.oninput=fitInput;
 cancel.onclick=()=>controller?.abort();
 find('form').onsubmit=async e=>{
  e.preventDefault();if(controller)return;
  const instruction=input.value.trim();controller=new AbortController();const signal=controller.signal;
  currentTask=sessions.start(instruction);send.disabled=true;input.disabled=true;cancel.hidden=false;
  stage('read','正在读取原文和批注…');
  try{
   review.connect();await review.queue;await review.sync();
   const snapshot=await adapter.readDocument();
   const comments=await review.begin(snapshot.comments);
   // Return typing focus to the optional instruction instead of the selected document.
   (collapsed?mini:find('.ai-collapse')).focus();
   if(snapshot.comments.length&&!comments.length)throw Error('现有批注正在等待审阅，请先接受或拒绝文档修订；待核对项可人工解决后重新打开。');
   if(!comments.length&&!instruction)throw Error('没有未解决批注，请补充修改要求后再试。');
   if(signal.aborted)throw new DOMException('已停止','AbortError');
   const chunks=[];let chunk=[],length=0;
   for(const block of snapshot.blocks){if(chunk.length&&(length+block.text.length>12000||chunk.length>=200)){chunks.push(chunk);chunk=[];length=0;}chunk.push(block);length+=block.text.length;}if(chunk.length)chunks.push(chunk);
   const perBlock=Math.max(0,Math.floor(5500/snapshot.blocks.length)-12);
   const synopsis=snapshot.blocks.map(b=>b.id+': '+b.text.slice(0,perBlock)+(b.text.length>perBlock?'…':'')).join('\n').slice(0,6000);
   const edits=[],warnings=[],summaries=[],completion=new Map();
   for(let i=0;i<chunks.length;i++){
    await review.heartbeat();
    stage('generate',`已读取 ${comments.length} 条待修改批注，正在生成修改${chunks.length>1?`（${i+1}/${chunks.length}）`:''}…`);
    const response=await fetch('/api/ai/revise',{method:'POST',signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({file:new URL(location.href).searchParams.get('file')||'1',instruction,blocks:chunks[i],comments,context:synopsis})});
    const data=await response.json();if(!response.ok)throw Error(data.error||'生成修改失败');
    for(const item of data.comment_results||[]){const states=completion.get(item.id)||[];states.push(item.status);completion.set(item.id,states);if(item.status!=='complete'&&item.reason)warnings.push(item.reason);}
    edits.push(...data.edits);warnings.push(...data.warnings);if(data.summary)summaries.push(data.summary);
   }
   if(signal.aborted)throw new DOMException('已停止','AbortError');
   let applied=0;
   if(edits.length){
    stage('apply',`正在写入 ${edits.length} 处修订…`);
    const wasInert=frame.inert;frame.inert=true;
    try{applied=await adapter.applyDocumentPlan(snapshot,edits,(n,total)=>stage('apply',`正在写入修订 ${n}/${total}…`),signal,review);}finally{frame.inert=wasInert;}
   }
   await review.finish(comments.filter(c=>completion.get(c.id)?.length&&completion.get(c.id).every(x=>x==='complete')).map(c=>c.id));
   adapter.app?.searchService?.resetSelection();
   const addressed=new Set(edits.flatMap(edit=>edit.comment_ids));
   const unchecked=comments.filter(comment=>!addressed.has(comment.id));
   stage('complete',applied?`已生成 ${applied} 处修订${unchecked.length?`，${unchecked.length} 条批注需核对`:''}。请在文档中接受或拒绝。`:'未生成修改，请检查批注或补充要求。');
   report([...new Set(summaries)].join('\n')+(warnings.length?'\n需核对：\n'+[...new Set(warnings)].join('\n'):'')+(unchecked.length?'\n未处理的批注：\n'+unchecked.map(c=>c.text).join('\n'):''));
  }catch(e){stage(signal.aborted?'stopped':'error',e.name==='AbortError'?'已停止，请核对文档中已写入的修订。':e.message);}finally{if(review.token){try{await review.finish([]);}catch(e){stage('error',e.message);}}controller=null;send.disabled=false;input.disabled=false;cancel.hidden=true;schedulePosition();}
 };
 input.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();find('form').requestSubmit();}};
 const connect=()=>{try{adapter.connect();if(!sessions.install())return false;review.connect();const canvas=adapter.app?.sectionContainer?.canvas;if(canvas&&canvas!==observedCanvas){canvasObserver.disconnect();canvasObserver.observe(canvas);observedCanvas=canvas;}schedulePosition();return true;}catch{return false;}};
 frame.addEventListener('load',()=>{controller?.abort();connect();});
 const timer=setInterval(()=>{if(connect())clearInterval(timer);},500);
 window.addEventListener('resize',schedulePosition);new ResizeObserver(schedulePosition).observe(panel);position();
})();
