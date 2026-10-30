(() => {
 'use strict';
 const frame=document.querySelector('iframe[name=editor]');if(!frame)return;
 const adapter=new OfficeAIEditor(frame);
 const panel=document.createElement('section');panel.id='office-ai';panel.setAttribute('aria-label','AI 文档助手');
 panel.innerHTML=`<header><strong>AI 文档助手</strong><button type="button" aria-label="收缩 AI 窗口" aria-expanded="true">收缩</button></header><div class="ai-body"><p role="status">选择文档原文，或选择批注作为修改要求。</p><button class="ai-capture">关联当前选区</button><button class="ai-comments">读取批注</button><select class="ai-comment" aria-label="选择批注"><option value="">选择批注作为修改要求</option></select><label>关联原文<textarea class="ai-source" readonly></textarea></label><label>修改要求<textarea class="ai-instruction" maxlength="2000"></textarea></label><button class="ai-send">生成修改建议</button><button class="ai-cancel" hidden>取消</button><pre class="ai-result" tabindex="0"></pre><button class="ai-accept" hidden>接受建议并生成修订</button><button class="ai-reject" hidden>拒绝建议</button></div>`;
 document.body.append(panel);
 const find=s=>panel.querySelector(s),status=find('[role=status]'),result=find('.ai-result'),send=find('.ai-send'),reject=find('.ai-reject'),accept=find('.ai-accept'),cancel=find('.ai-cancel');
 let target=null,suggestion='',controller=null;
 function clear(){suggestion='';result.textContent='';accept.hidden=reject.hidden=true;}
 function error(e){status.textContent=e.message;}
 find('header button').onclick=e=>{const collapsed=panel.classList.toggle('collapsed');e.target.textContent=collapsed?'展开':'收缩';e.target.setAttribute('aria-expanded',String(!collapsed));e.target.setAttribute('aria-label',collapsed?'展开 AI 窗口':'收缩 AI 窗口');adapter.reserve(panel.getBoundingClientRect().height);};
 async function capture(){clear();target=await adapter.capture();find('.ai-source').value=target.text;status.textContent='已关联选区。移动或改变选区后需要重新关联。';}
 find('.ai-capture').onclick=()=>capture().catch(error);
 find('.ai-comments').onclick=()=>{try{const select=find('.ai-comment');select.replaceChildren(new Option('选择批注作为修改要求',''));for(const c of adapter.comments())select.add(new Option(c.text.slice(0,100),String(c.id)));status.textContent='选取批注后，请在文档中选中对应原文并关联选区。';}catch(e){error(e);}};
 find('.ai-comment').onchange=e=>{if(!e.target.value)return;try{find('.ai-instruction').value=adapter.selectComment(e.target.value);clear();target=null;find('.ai-source').value='';status.textContent='已定位批注。请选择对应原文，再点击“关联当前选区”。';}catch(e){error(e);}};
 reject.onclick=()=>{clear();status.textContent='已拒绝建议，文档未修改。';};
 cancel.onclick=()=>controller?.abort();
 send.onclick=async()=>{
  const instruction=find('.ai-instruction').value;
  if(!target||!instruction.trim()){status.textContent='请关联原文并填写修改要求。';return;}
  const requestTarget=target;clear();send.disabled=true;cancel.hidden=false;controller=new AbortController();status.textContent='正在生成建议…';
  try{
   const response=await fetch('/api/ai/edit',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({file:new URL(location.href).searchParams.get('file')||'1',text:requestTarget.text,instruction})});
   const data=await response.json();if(!response.ok)throw Error(data.error||'请求失败');
   if(requestTarget!==target)throw Error('关联选区已变化，请重新生成建议');
   suggestion=data.suggestion;result.textContent=suggestion;accept.hidden=reject.hidden=false;status.textContent='请核对建议。接受后生成文档修订，可在原生审阅功能中继续接受或拒绝修订。';
  }catch(e){status.textContent=e.name==='AbortError'?'已取消，文档未修改。':e.message;}finally{send.disabled=false;cancel.hidden=true;controller=null;}
 };
 accept.onclick=async()=>{accept.disabled=true;try{await adapter.apply(target,suggestion);clear();target=null;find('.ai-source').value='';status.textContent='已提交带修订的修改，请在文档中核对并保存。';}catch(e){error(e);}finally{accept.disabled=false;}};
 find('.ai-instruction').oninput=()=>{if(suggestion)clear();};
 // Parent controls stay outside the document; collapsing retains context and tasks.
 const connect=()=>{try{adapter.connect();adapter.reserve(panel.getBoundingClientRect().height);return true;}catch{return false;}};
 frame.addEventListener('load',()=>{target=null;clear();connect();});
 const timer=setInterval(()=>{if(connect())clearInterval(timer);},500);
 window.addEventListener('resize',()=>{if(adapter.app)adapter.reserve(panel.getBoundingClientRect().height);});
})();
