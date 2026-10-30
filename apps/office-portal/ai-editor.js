/* Same-origin adapter for the pinned OpenWen Collabora build. Fail closed. */
window.OfficeAIEditor = class {
 constructor(frame) { this.frame=frame;this.epoch=0; }
 connect() {
  const w=this.frame.contentWindow,a=w.app,m=a?.map,d=m?._docLayer;
  if(!d||d._docType!=='text'||!a.activeDocument?.activeLayout)throw Error('等待 Writer 文档加载');
  if(this.layer===d)return;
  this.app=a;this.map=m;this.layer=d;this.epoch++;
  const original=d._onTextSelectionMsg;
  if(typeof original!=='function')throw Error('此编辑器版本不支持选区绑定');
  d._onTextSelectionMsg=(msg)=>{if(this.selection!==msg){this.selection=msg;this.epoch++;}return original.call(d,msg);};
 }
 comments() {
  this.connect();const list=this.app.sectionContainer.getSectionWithName(this.app.CSections.CommentList.name);
  return (list?.sectionProperties.commentList||[]).filter(c=>!c.sectionProperties.data.trackchange).map(c=>({id:c.sectionProperties.data.id,text:c.sectionProperties.contentText?.textContent||'',object:c,list}));
 }
 selectComment(id) {
  const c=this.comments().find(c=>String(c.id)===id);if(!c)throw Error('批注已删除，请刷新');
  c.list.select(c.object,true);return c.text;
 }
 async selectionContent(selectAll=false) {
  this.connect();this.app.idleHandler?.notifyActive();
  if(this.map.wopi?.DisableCopy)throw Error('此文档不允许读取内容，不能发送给 AI');
  return new Promise((resolve,reject)=>{
   const controller=new AbortController();let downloading=false;
   const cleanup=()=>{clearTimeout(timer);this.map.off('textselectioncontent',done);this.map.off('complexselection',complex);};
   const finish=value=>{cleanup();resolve(value);};
   const done=e=>finish({html:e.html||'',plainText:e.plainText||''});
   const complex=async()=>{
    if(downloading)return;downloading=true;
    try{
     await new Promise((resolve,reject)=>{const onCopy=e=>{if(e.commandName!=='.uno:Copy')return;clearTimeout(copyTimer);this.map.off('commandresult',onCopy);if(e.success===false)reject(Error('长文档复制失败'));else resolve();};const copyTimer=setTimeout(()=>{this.map.off('commandresult',onCopy);reject(Error('长文档复制超时'));},6000);this.map.on('commandresult',onCopy);this.app.socket.sendMessage('uno .uno:Copy');});
     const clip=this.map._clip;const url=new URL(clip.getMetaURL()+'&MimeType=text/html',this.frame.contentWindow.location.href);
     if(url.origin!==location.origin)throw Error('文档读取地址不受支持');
     const response=await fetch(url,{signal:controller.signal});if(!response.ok)throw Error('长文档读取失败');
     if(Number(response.headers.get('Content-Length'))>10485760)throw Error('文档内容过大');
     const reader=response.body.getReader();const chunks=[];let size=0;
     try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>10485760)throw Error('文档内容过大');chunks.push(value);}}catch(e){await reader.cancel();throw e;}
     const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
     const raw=new TextDecoder().decode(bytes);const value=clip.parseClipboard(raw);
     if(!value.html)throw Error('未能读取长文档原文');finish({html:value.html,plainText:value.plain||''});
    }catch(e){cleanup();reject(e);}
   };
   const timer=setTimeout(()=>{cleanup();controller.abort();reject(Error('读取文档超时，请重试'));},20000);
   this.map.on('textselectioncontent',done);this.map.on('complexselection',complex);
   if(selectAll){this.map.focus();this.map.sendUnoCommand('.uno:GoToStartOfDoc');this.map.sendUnoCommand('.uno:SelectAll');}
   this.app.socket.sendMessage('gettextselection mimetype=text/html,text/plain;charset=utf-8');
  });
 }
 async capture() {
  this.connect();this.app.idleHandler?.notifyActive();
  if(!this.selection||!this.selection.replace('textselection:','').trim())throw Error('请先在文档中选择要修改的文字');
  const epoch=this.epoch,selection=this.selection;
  const content=await this.selectionContent();const doc=new DOMParser().parseFromString(content.html,'text/html');const text=content.plainText||doc.body.textContent||'';
  if(epoch!==this.epoch||!text.trim())throw Error('选区已变化，请重新选择');
  return {epoch,selection,text,layer:this.layer};
 }
 async readDocument() {
  this.connect();this.app.idleHandler?.notifyActive();
  const layer=this.layer;
  const {html}=await this.selectionContent(true);
  if(layer!==this.layer)throw Error('文档已切换，请重试');
  const doc=new DOMParser().parseFromString(html,'text/html');
  const nodes=[...doc.body.querySelectorAll('p,h1,h2,h3,h4,h5,h6')];
  if(!nodes.length)throw Error('无法读取文档段落，请先确认文档已加载');
  const blocks=[],anchors=new Map();
  for(const node of nodes){
   const text=(node.textContent||'').replace(/\x00/g,'');if(!text.trim())continue;
   const id='b'+blocks.length;blocks.push({id,text});
   const walker=doc.createTreeWalker(node,128);let note;
   while((note=walker.nextNode())){const key=note.textContent.trim();if(key){const list=anchors.get(key)||[];list.push(id);anchors.set(key,list);}}
  }
  if(!blocks.length||blocks.length>2000||blocks.reduce((n,b)=>n+b.text.length,0)>200000)throw Error('文档过大，请拆分为不超过20万字的文档后处理');
  if(blocks.some(b=>b.text.length>12000))throw Error('存在超过12000字的单段，请先拆分该段落');
  const comments=this.comments().filter(c=>!['true',true].includes(c.object.sectionProperties.data.resolved)).map(c=>({id:String(c.id),text:c.text,block_ids:anchors.get(c.text.trim())||[]}));
  return {blocks,comments,layer,fingerprint:JSON.stringify({blocks,comments})};
 }
 async locate(text) {
  this.connect();this.app.idleHandler?.notifyActive();
  await new Promise((resolve,reject)=>{
   const done=e=>{if(e.originalPhrase!==text)return;clearTimeout(timer);this.map.off('search',done);if(e.count!==1)reject(Error('原文位置不唯一或已变化，已停止修改'));else resolve();};
   const timer=setTimeout(()=>{this.map.off('search',done);reject(Error('定位原文超时，已停止修改'));},6000);
   this.map.on('search',done);
   this.map.sendUnoCommand('.uno:ExecuteSearch',{
    'SearchItem.SearchString':{type:'string',value:text},'SearchItem.Backward':{type:'boolean',value:false},
    'SearchItem.SearchStartPointX':{type:'long',value:0},'SearchItem.SearchStartPointY':{type:'long',value:0},
    'SearchItem.Command':{type:'long',value:0},'SearchItem.SearchFlags':{type:'long',value:0},'SearchItem.TransliterateFlags':{type:'long',value:0}
   });
  });
  const target=await this.capture();
  if(target.text!==text)throw Error('定位文字与原文不一致，已停止修改');
  return target;
 }
 async applyDocumentPlan(snapshot,edits,onProgress,signal,hooks) {
  let expected=snapshot.fingerprint,applied=0;
  const all=snapshot.blocks.map(b=>b.text).join('\n');const ranges=[];
  for(const edit of edits){
   const block=snapshot.blocks.find(b=>b.id===edit.block_id);
   if(!block||!edit.before||block.text.split(edit.before).length!==2||all.split(edit.before).length!==2)throw Error('修改片段不能唯一定位，请补充批注中的原文范围');
   const offset=all.indexOf(edit.before),end=offset+edit.before.length;
   if(ranges.some(r=>offset<r.end&&end>r.offset))throw Error('修改范围相互重叠，未写入文档');
   ranges.push({offset,end,edit});
  }
  ranges.sort((a,b)=>b.offset-a.offset);
  try{
   for(const {edit} of ranges){
    if(signal?.aborted)throw Error('已停止修改');
    const current=await this.readDocument();
    if(current.layer!==snapshot.layer||current.fingerprint!==expected)throw Error('文档或批注已变化，请重新生成修改');
    if(current.blocks.map(b=>b.text).join('\n').split(edit.before).length!==2)throw Error('原文位置不唯一或已变化，已停止修改');
    const target=await this.locate(edit.before);
    if(signal?.aborted)throw Error('已停止修改');
    if(hooks)await hooks.prepare(edit);
    await this.apply(target,edit.after);
    // A subsequent copy round-trip is ordered after the paste on the same socket.
    const after=await this.readDocument();
    if(after.fingerprint===expected)throw Error('未确认本次修改已写入，已停止后续修改');
    applied++;expected=after.fingerprint;
    if(hooks)await hooks.record(edit);
    onProgress(applied,ranges.length);
   }
   this.map.save(false,false);
   return applied;
  }catch(e){if(applied)this.map.save(false,false);throw Error(`已确认写入 ${applied} 处修订；${e.message}。已停止后续修改，请核对文档中的修订。`);}
 }
 async apply(target,text) {
  this.connect();
  if(this.map.isReadOnlyMode?.())throw Error('文档为只读');
  const current=await this.capture();
  if(current.epoch!==target.epoch||current.selection!==target.selection||current.text!==target.text||current.layer!==target.layer)throw Error('原选区或内容已变化，请重新选择并生成建议');
  const state=()=>this.map.stateChangeHandler.getItemValue('.uno:TrackChanges');
  if(state()!==true&&state()!=='true'){
   this.map.sendUnoCommand('.uno:TrackChangesInAllViews');
   await new Promise((resolve,reject)=>{const start=Date.now();const timer=setInterval(()=>{if(state()===true||state()==='true'){clearInterval(timer);resolve();}else if(Date.now()-start>4000){clearInterval(timer);reject(Error('无法确认修订已开启，未修改文档'));}},50);});
  }
  if(this.epoch!==target.epoch)throw Error('选区已变化，未修改文档');
  this.app.idleHandler?.notifyActive();
  this.app.socket.sendMessage(new this.frame.contentWindow.Blob(['paste mimetype=text/plain;charset=utf-8\n',text]));
  this.map.focus();
 }
};

/* Native review commands are serialized with a before/after core-table round trip. */
window.OfficeAIReview = class {
 constructor(adapter,notify){this.adapter=adapter;this.notify=notify;this.client=crypto.randomUUID();this.statuses={};this.queue=Promise.resolve();this.rawQueue=Promise.resolve();this.ready=null;}
 async hash(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(value))))].map(x=>x.toString(16).padStart(2,'0')).join('');}
 connect(){
  this.adapter.connect();const a=this.adapter;if(this.layer===a.layer)return;
  this.layer=a.layer;const layer=this.layer;this.requests=[];this.rawQueue=Promise.resolve();a.app.officeAIReview=this;const socket=a.app.socket;if(!socket.officeAIReviewTransport)socket.officeAIReviewTransport=socket.sendMessage.bind(socket);this.send=socket.officeAIReviewTransport;
  const values=this.layer._onCommandValuesMsg;
  this.layer._onCommandValuesMsg=msg=>{if(this.layer!==layer)return values.call(layer,msg);try{const data=JSON.parse(msg.slice(msg.indexOf('{')));if(Array.isArray(data.redlines)){this.rows=data.redlines.map(r=>({...r}));const request=this.requests?.shift();if(request?.active)request.done(this.rows);}}catch{}return values.call(layer,msg);};
  socket.sendMessage=msg=>{
   let kind=null;
   if(typeof msg==='string'){
    const command=msg.match(/^uno \.uno:(\w+)/)?.[1];
    if(['AcceptTrackedChange','AcceptTrackedChangeToNext','AcceptAllTrackedChanges'].includes(command))kind='accepted';
    if(['RejectTrackedChange','RejectTrackedChangeToNext','RejectAllTrackedChanges'].includes(command))kind='rejected';
    if(['Undo','Redo'].includes(command))kind='history';
    if(['ResolveComment','ResolveCommentThread'].includes(command))kind='manual';
    if(msg.startsWith('dialogevent ')&&[...this.adapter.frame.contentDocument.querySelectorAll('[id^=writerchanges],[id^=RedlineViewPage]')].some(node=>node.checkVisibility())){try{const action=JSON.parse(msg.slice(msg.indexOf('{')));if(['click','activate'].includes(action.cmd)&&/^(accept|acceptall|reject|rejectall)$/i.test(action.id))kind=/^accept/i.test(action.id)?'accepted':'rejected';}catch{}}
   }
   if(!kind){if(msg==='commandvalues command=.uno:AcceptTrackedChanges')(this.requests||(this.requests=[])).push(null);return this.send(msg);}
   this.enqueue(async()=>{
    if(this.layer!==layer)throw Error('编辑器已重新加载，请重新审阅');
    await this.lock();
    try{
    const before=await this.snapshot();if(this.layer!==layer)throw Error('编辑器已重新加载，请重新审阅');this.send(msg);let after;
    const start=Date.now();let last='',stable=0;
    do{
     after=await this.snapshot();if(this.layer!==layer)throw Error('编辑器已重新加载，请重新审阅');const ids=new Set(after.rows.map(r=>r.index));
     const changed=kind==='manual'?after.comments.some(c=>before.comments.some(old=>old.key===c.key&&old.resolved!==c.resolved)):before.rows.some(r=>!ids.has(r.index))||(kind==='history'&&JSON.stringify(before)!==JSON.stringify(after));
     const current=JSON.stringify([after.rows.map(r=>[r.index,r.key]),after.comments.map(c=>[c.key,c.resolved])]);
     stable=current===last?stable+1:0;last=current;
     if((changed&&stable>=2)||Date.now()-start>3500)break;
     await new Promise(resolve=>setTimeout(resolve,90));
    }while(true);

    if(kind==='manual'){
     for(const c of after.comments){const old=before.comments.find(x=>x.key===c.key);if(old&&old.resolved!==c.resolved)await this.post('manual',{key:c.key,resolved:c.resolved},after);}
    }else{
     if(kind==='history')for(const c of after.comments){const old=before.comments.find(x=>x.key===c.key);if(old&&old.resolved!==c.resolved)await this.post('manual',{key:c.key,resolved:c.resolved,history:true},after);}
     const remaining=new Set(after.revisions),decisions={};
     for(const r of before.revisions)if(!remaining.has(r))decisions[r]=kind==='history'?'unknown':kind;
     await this.sync({decisions,history:kind==='history'},after);
    }
    a.map.save(false,false);
    }finally{await this.unlock();}
   });
  };
  this.ready=this.enqueue(()=>this.sync());
  if(!this.timer)this.timer=setInterval(()=>{if(!this.working&&!document.hidden)this.enqueue(()=>this.sync());},5000);
 }
 enqueue(fn){const task=this.queue.catch(()=>{}).then(fn);this.queue=task.catch(e=>{this.error=e.message;this.notify?.(this.statuses,this.error);});return task;}
 raw(){
  const layer=this.layer;
  const task=this.rawQueue.catch(()=>{}).then(()=>new Promise((resolve,reject)=>{
   if(this.layer!==layer){reject(Error('编辑器已重新加载'));return;}
   let timer;const request={active:true,done:rows=>{request.active=false;clearTimeout(timer);resolve(rows);}};
   (this.requests||(this.requests=[])).push(request);
   timer=setTimeout(()=>{request.active=false;reject(Error('读取原生修订超时，未继续自动处理批注'));},6000);
   this.adapter.app.idleHandler?.notifyActive();this.send('commandvalues command=.uno:AcceptTrackedChanges');
  }));this.rawQueue=task;return task;
 }
 async snapshot(){
  const layer=this.layer;const rows=await this.raw();if(this.layer!==layer)throw Error('编辑器已重新加载');const revisions=await Promise.all(rows.map(async r=>({...r,key:await this.hash([r.author,r.type,r.dateTime?.slice(0,19),r.description,r.comment||''])})));
  const comments=await Promise.all(this.adapter.comments().map(async c=>{const d=c.object.sectionProperties.data;const date=d.dateTimeUtc||d.dateTime;return {id:String(c.id),key:await this.hash([d.author||'',date?.slice(0,19)||'',c.text]),resolved:['true',true].includes(d.resolved),text:c.text};}));
  const originals=this.adapter.comments();
  for(const c of comments){let native=originals.find(x=>String(x.id)===c.id),seen=new Set();while(native&&!seen.has(String(native.id))){seen.add(String(native.id));const d=native.object.sectionProperties.data,parent=String(d.parentId||d.parent||'0');if(parent==='0')break;const next=originals.find(x=>String(x.id)===parent);if(!next)break;native=next;}c.thread=comments.find(x=>x.id===String(native?.id))?.key||c.key;}
  if(new Set(comments.map(c=>c.key)).size!==comments.length)throw Error('存在无法唯一区分的同名批注，请先分别补充说明');
  this.live=comments;return {comments,revisions:revisions.map(r=>r.key),rows:revisions};
 }
 async post(op,data={},snapshot){
  snapshot=snapshot||await this.snapshot();
  const response=await fetch('/api/ai/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,file:new URL(location.href).searchParams.get('file')||'1',client:this.client,comments:snapshot.comments.map(({key,id,resolved,thread})=>({key,id,resolved,thread})),revisions:snapshot.revisions,...data})});
  const result=await response.json();if(!response.ok)throw Error(result.error||'批注状态保存失败，已停止自动修改');
  this.statuses=result.statuses;this.error='';this.notify?.(this.statuses,'',this.live);return result;
 }
 async lock(){
  if(this.reviewToken)return;
  const start=Date.now();
  while(true){try{const result=await this.post('review-start');this.reviewToken=result.review_token;return;}catch(e){if(Date.now()-start>4000)throw e;await new Promise(resolve=>setTimeout(resolve,150));}}
 }
 async unlock(){if(!this.reviewToken)return;const token=this.reviewToken;this.reviewToken=null;await this.post('review-end',{review_token:token});}
 async sync(data={},snapshot){
  const layer=this.layer;
  let result=await this.post('sync',data,snapshot);
  const ownLock=!this.reviewToken&&result.actions.length>0;
  if(ownLock){await this.lock();result=await this.post('sync');}
  try{
  let changed=false;
  for(const action of result.actions){
   if(this.layer!==layer)throw Error('编辑器已重新加载，未继续自动解决批注');
   const native=this.adapter.comments().find(c=>String(c.id)===action.id);if(!native)continue;
   const resolved=['true',true].includes(native.object.sectionProperties.data.resolved);
   if(resolved===action.resolved)continue;
   if(!native.object.canModerate())continue;
   this.send('uno .uno:ResolveComment '+JSON.stringify({Id:{type:'string',value:action.id}}));
   await this.raw();
   await new Promise((resolve,reject)=>{const start=Date.now();const timer=setInterval(()=>{const current=this.adapter.comments().find(c=>String(c.id)===action.id);if(current&&['true',true].includes(current.object.sectionProperties.data.resolved)===action.resolved){clearInterval(timer);resolve();}else if(Date.now()-start>4000){clearInterval(timer);reject(Error('未确认批注状态更新，请在文档中核对'));}},30);});
   changed=true;
  }
  if(changed){this.adapter.map.save(false,false);return this.post('sync');}
  return result;
  }finally{if(ownLock)await this.unlock();}
 }
 async begin(comments){
  this.connect();this.working=true;
  try{await this.queue;await this.sync();const state=await this.post('begin');this.token=state.token;this.commentKeys=new Map((this.live||[]).map(c=>[c.id,c.key]));
   const eligible=new Set(state.eligible);return comments.filter(c=>eligible.has(this.commentKeys.get(c.id)));
  }catch(e){this.working=false;throw e;}
 }
 async heartbeat(){if(this.token)await this.post('heartbeat',{token:this.token});}
 async prepare(edit){
  this.before=await this.snapshot();const keys=(edit.comment_ids||[]).map(id=>this.commentKeys.get(id)).filter(Boolean);
  await this.post('prepare',{token:this.token,keys},this.before);
 }
 async record(edit){
  const after=await this.snapshot(),old=new Map(this.before.rows.map(r=>[r.index,r.key]));
  const added=after.rows.filter(r=>!old.has(r.index));const modified=after.rows.some(r=>old.has(r.index)&&old.get(r.index)!==r.key);
  const linked=added.map(r=>r.key);const unique=new Set(after.revisions).size===after.revisions.length;
  await this.post('record',{token:this.token,keys:(edit.comment_ids||[]).map(id=>this.commentKeys.get(id)).filter(Boolean),linked,certain:!!linked.length&&!modified&&unique},after);
 }
 async finish(complete=[]){
  if(!this.token)return;
  try{await this.post('finish',{token:this.token,complete:complete.map(id=>this.commentKeys.get(id)).filter(Boolean)});await this.sync();}finally{this.token=null;this.working=false;}
 }
};
