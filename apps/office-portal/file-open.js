(() => {
 'use strict';
 const editor=document.querySelector('iframe[name=editor]');
 const dialog=document.createElement('dialog');dialog.id='file-picker';
 dialog.setAttribute('aria-labelledby','file-picker-title');
 dialog.innerHTML=`<header><h2 id="file-picker-title">打开文件</h2><button id="close-picker" aria-label="关闭打开文件窗口">✕</button></header><nav role="tablist" aria-label="文件来源"><button role="tab" id="knowledge-tab" aria-controls="knowledge-panel" aria-selected="true">知识库</button><button role="tab" id="upload-tab" aria-controls="upload-panel" aria-selected="false">本地上传</button></nav><section id="knowledge-panel" role="tabpanel" aria-labelledby="knowledge-tab"><input id="knowledge-search" type="search" placeholder="搜索文件名称" aria-label="搜索知识库"><div id="knowledge-files" aria-live="polite"></div></section><section id="upload-panel" role="tabpanel" aria-labelledby="upload-tab" hidden><p>上传后保存至服务器知识库，并在新标签页打开。支持 Word、Excel、PowerPoint 及 OpenDocument 格式，单个文件最大 1 GB（1024 MB）。</p><form id="upload-document"><input id="local-document" type="file" accept=".docx,.doc,.odt,.rtf,.txt,.xlsx,.xls,.ods,.pptx,.ppt,.odp" required aria-label="选择本地文档"><button type="submit">上传并打开</button><progress id="upload-progress" hidden aria-label="正在上传"></progress></form></section><p id="file-error" role="alert"></p><footer>在新标签页打开文件，当前文档继续保留。同名上传不会覆盖已有文件。</footer>`;
 document.body.append(dialog);
 const find=id=>dialog.querySelector('#'+id);
 let files=[];
 const user=new URL(location.href).searchParams.get('user')||'Alice';
 const url=id=>'/edit?user='+encodeURIComponent(user)+'&file='+encodeURIComponent(id);
 const error=message=>{find('file-error').textContent=message;};
 function render(){
  const list=find('knowledge-files');list.replaceChildren();
  const filtered=files.filter(f=>f.name.toLocaleLowerCase().includes(find('knowledge-search').value.toLocaleLowerCase()));
  if(!filtered.length){list.textContent='暂无匹配的文件，可从“本地上传”添加。';return;}
  for(const file of filtered){
   const row=document.createElement('div');row.className='file-row';
   const text=document.createElement('div');text.className='file-name';text.textContent=file.name;
   const meta=document.createElement('small');meta.textContent=Math.max(1,Math.round(file.size/1024))+' KB · '+new Date(file.modified*1000).toLocaleString('zh-CN');text.append(meta);
   const open=document.createElement('button');open.textContent='打开';open.setAttribute('aria-label','打开 '+file.name);open.onclick=()=>window.open(url(file.id),'_blank','noopener');row.append(text,open);list.append(row);
  }
 }
 async function refresh(){
  find('knowledge-files').textContent='正在加载…';
  try{const response=await fetch('/api/files');if(!response.ok)throw new Error('知识库加载失败，请刷新或重新登录');files=(await response.json()).files;render();}catch(e){error(e.message);}
 }
 function tab(upload){find('knowledge-panel').hidden=upload;find('upload-panel').hidden=!upload;find('knowledge-tab').setAttribute('aria-selected',String(!upload));find('upload-tab').setAttribute('aria-selected',String(upload));error('');}
 function show(){if(!dialog.open)dialog.showModal();tab(false);refresh();}
 find('close-picker').onclick=()=>dialog.close();find('knowledge-tab').onclick=()=>tab(false);find('upload-tab').onclick=()=>tab(true);find('knowledge-search').oninput=render;
 dialog.querySelector('nav').onkeydown=e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();const upload=find('knowledge-tab').getAttribute('aria-selected')==='true';tab(upload);find(upload?'upload-tab':'knowledge-tab').focus();}};
 find('upload-document').onsubmit=async e=>{
  e.preventDefault();error('');const file=find('local-document').files[0];if(!file)return;
  if(!file.size||file.size>1024*1024*1024){error('请选择非空文件，最大 1 GB（1024 MB）');return;}
  const target=window.open('about:blank','_blank');if(target)target.opener=null;
  const button=e.target.querySelector('button');button.disabled=true;find('upload-progress').hidden=false;
  try{
   const response=await fetch('/api/files?name='+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
   const result=await response.json();if(!response.ok)throw new Error(result.error||'上传失败，请稍后重试');
   if(target){target.location.href=url(result.id);dialog.close();}else{tab(false);error('文件已上传，请从知识库点击“打开”（浏览器阻止了新窗口）。');await refresh();}
  }catch(e){if(target)target.close();error(e.message);}finally{button.disabled=false;find('upload-progress').hidden=true;}
 };
 function send(MessageId,Values={}){editor.contentWindow.postMessage(JSON.stringify({MessageId,Values}),new URL(editor.src||document.getElementById('f').action,location.href).origin);}
 editor.addEventListener('load',()=>send('Host_PostmessageReady'));
 window.addEventListener('message',event=>{
  const origin=new URL(document.getElementById('f').action,location.href).origin;
  if(event.source!==editor.contentWindow||event.origin!==origin)return;
  let message;try{message=typeof event.data==='string'?JSON.parse(event.data):event.data;}catch{return;}
  if(message.MessageId==='App_LoadingStatus'&&message.Values?.Status==='Document_Loaded')send('Insert_Button',{id:'office-open-file',hint:'打开文件',imgurl:location.origin+'/file-open.svg',insertBefore:'save'});
  if(message.MessageId==='Clicked_Button'&&message.Values?.Id==='office-open-file')show();
 });
})();
