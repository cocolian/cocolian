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
 async applyDocumentPlan(snapshot,edits,onProgress,signal) {
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
    const target=await this.locate(edit.before);
    if(signal?.aborted)throw Error('已停止修改');
    await this.apply(target,edit.after);
    // A subsequent copy round-trip is ordered after the paste on the same socket.
    const after=await this.readDocument();
    if(after.fingerprint===expected)throw Error('未确认本次修改已写入，已停止后续修改');
    applied++;expected=after.fingerprint;onProgress(applied,ranges.length);
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
