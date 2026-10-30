(() => {
 'use strict';
 const frame=document.querySelector('iframe[name=editor]');if(!frame)return;
 const adapter=new OfficeAIEditor(frame);
 const panel=document.createElement('aside');panel.id='office-ai';panel.setAttribute('aria-label','AI 对话');
 panel.innerHTML=`<div class="ai-resizer" role="separator" tabindex="0" aria-label="调整 AI 栏宽度" aria-orientation="vertical" aria-valuemin="200" aria-valuemax="600" aria-valuenow="200"></div><header><strong>AI 助手</strong><button class="ai-close" aria-label="关闭 AI 栏" title="关闭">×</button></header><div class="ai-history" role="log" aria-label="聊天记录" aria-live="polite"><div class="ai-welcome"><span>✦</span><h2>一起完善文档</h2><p>提问，或选中文字后告诉我如何修改。</p></div></div><form class="ai-composer"><div class="ai-context" hidden><span></span><button type="button" aria-label="移除关联选区">×</button></div><div class="ai-tools"><button type="button" class="ai-capture">关联选区</button><button type="button" class="ai-comments">批注</button></div><select class="ai-comment" aria-label="选择批注" hidden></select><label class="ai-input-label" for="ai-input">发送消息</label><textarea id="ai-input" class="ai-instruction" maxlength="2000" rows="3" placeholder="向 AI 提问…"></textarea><div class="ai-send-row"><small>MiniMax M3</small><button type="button" class="ai-cancel" hidden>停止</button><button type="submit" class="ai-send" aria-label="发送消息">↑</button></div><p role="status"></p></form>`;
 const reopen=document.createElement('button');reopen.className='ai-reopen';reopen.textContent='✦ AI';reopen.setAttribute('aria-label','打开 AI 栏');reopen.hidden=true;
 document.body.append(panel,reopen);document.body.classList.add('office-ai-open');
 const find=s=>panel.querySelector(s),history=find('.ai-history'),input=find('.ai-instruction'),status=find('[role=status]'),send=find('.ai-send'),cancel=find('.ai-cancel'),handle=find('.ai-resizer');
 let target=null,controller=null,width=200;const conversation=[];const pending=new Set();
 function resize(value){width=Math.max(200,Math.min(600,Math.floor(innerWidth*.6),value));document.documentElement.style.setProperty('--office-ai-width',width+'px');handle.setAttribute('aria-valuenow',String(width));}
 function open(value){panel.hidden=!value;reopen.hidden=value;document.body.classList.toggle('office-ai-open',value);if(value)input.focus();}
 find('.ai-close').onclick=()=>open(false);reopen.onclick=()=>open(true);
 let dragging=false;
 handle.onpointerdown=e=>{dragging=true;handle.setPointerCapture(e.pointerId);document.body.classList.add('office-ai-resizing');e.preventDefault();};
 handle.onpointermove=e=>{if(dragging)resize(innerWidth-e.clientX);};
 const finish=()=>{dragging=false;document.body.classList.remove('office-ai-resizing');};handle.onpointerup=finish;handle.onlostpointercapture=finish;
 handle.onkeydown=e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();resize(width+(e.key==='ArrowLeft'?20:-20));}if(e.key==='Home')resize(200);};
 window.addEventListener('resize',()=>resize(width));resize(width);
 function message(role,text){find('.ai-welcome')?.remove();const row=document.createElement('article');row.className='ai-message ai-'+role;const label=document.createElement('strong');label.textContent=role==='user'?'你':'AI';const content=document.createElement('div');content.className='ai-message-text';content.textContent=text;row.append(label,content);history.append(row);history.scrollTop=history.scrollHeight;return row;}
 function context(){const box=find('.ai-context');box.hidden=!target;box.querySelector('span').textContent=target?'已关联：'+target.text.slice(0,60):'';input.placeholder=target?'希望如何修改这段文字？':'向 AI 提问…';}
 function invalidate(){for(const entry of pending){entry.buttons.remove();}pending.clear();}
 function error(e){status.textContent=e.message;}
 find('.ai-context button').onclick=()=>{target=null;context();};
 find('.ai-capture').onclick=async()=>{try{target=await adapter.capture();context();status.textContent='已关联选区';input.focus();}catch(e){error(e);}};
 find('.ai-comments').onclick=()=>{try{const select=find('.ai-comment');select.replaceChildren(new Option('选择批注',''));for(const c of adapter.comments())select.add(new Option(c.text.slice(0,100),String(c.id)));select.hidden=false;status.textContent=select.options.length===1?'暂无批注':'';}catch(e){error(e);}};
 find('.ai-comment').onchange=e=>{if(!e.target.value)return;try{input.value=adapter.selectComment(e.target.value);target=null;context();status.textContent='已定位批注，请选中对应原文并关联选区';}catch(e){error(e);}};
 cancel.onclick=()=>controller?.abort();
 find('form').onsubmit=async e=>{
  e.preventDefault();const instruction=input.value.trim();if(!instruction||controller)return;
  const requestTarget=target;const previous=conversation.slice(-10);message('user',instruction);input.value='';
  const row=message('assistant','正在思考…');const content=row.querySelector('.ai-message-text');
  send.disabled=true;cancel.hidden=false;controller=new AbortController();status.textContent='';
  try{
   const response=await fetch(requestTarget?'/api/ai/edit':'/api/ai/chat',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({file:new URL(location.href).searchParams.get('file')||'1',text:requestTarget?.text,instruction,history:previous})});
   const data=await response.json();if(!response.ok)throw Error(data.error||'请求失败');
   content.textContent=data.suggestion;conversation.push({role:'user',content:instruction},{role:'assistant',content:data.suggestion});if(conversation.length>10)conversation.splice(0,conversation.length-10);
   if(requestTarget){
    const buttons=document.createElement('div');buttons.className='ai-review';const accept=document.createElement('button'),reject=document.createElement('button');accept.type=reject.type='button';accept.textContent='接受修改';reject.textContent='拒绝';accept.className='ai-accept';reject.className='ai-reject';buttons.append(accept,reject);row.append(buttons);const entry={buttons};pending.add(entry);
    reject.onclick=()=>{buttons.textContent='已拒绝';pending.delete(entry);};
    accept.onclick=async()=>{accept.disabled=true;try{await adapter.apply(requestTarget,data.suggestion);buttons.textContent='已生成修订';pending.delete(entry);if(target===requestTarget){target=null;context();}status.textContent='请在文档中核对修订';}catch(e){error(e);}finally{accept.disabled=false;}};
   }
  }catch(e){content.textContent=e.name==='AbortError'?'已停止生成':e.message;if(!input.value)input.value=instruction;}finally{send.disabled=false;cancel.hidden=true;controller=null;history.scrollTop=history.scrollHeight;}
 };
 input.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();find('form').requestSubmit();}};
 const connect=()=>{try{adapter.connect();return true;}catch{return false;}};
 frame.addEventListener('load',()=>{target=null;context();invalidate();connect();});const timer=setInterval(()=>{if(connect())clearInterval(timer);},500);
})();
