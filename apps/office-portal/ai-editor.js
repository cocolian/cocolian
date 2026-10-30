/* Same-origin adapter for the pinned OpenWen Collabora build. Fail closed. */
window.OfficeAIEditor = class {
 constructor(frame) { this.frame=frame;this.epoch=0;this.padding=408; }
 connect() {
  const w=this.frame.contentWindow,a=w.app,m=a?.map,d=m?._docLayer;
  if(!d||d._docType!=='text'||!a.activeDocument?.activeLayout)throw Error('等待 Writer 文档加载');
  if(this.layer===d)return;
  this.app=a;this.map=m;this.layer=d;this.epoch++;
  const original=d._onTextSelectionMsg;
  if(typeof original!=='function')throw Error('此编辑器版本不支持选区绑定');
  d._onTextSelectionMsg=(msg)=>{this.selection=msg;this.epoch++;return original.call(d,msg);};
  this.layout();
 }
 layout() {
  const a=this.app,l=a?.activeDocument?.activeLayout;if(!l||l.type!=='ViewLayoutWriter')return;
  if(l.officeAIPaddingAdapter)return;
  l.officeAIPaddingAdapter=true;
  // Extend the actual layout extent used by both wheel limits and scrollbar.
  const original=l.refreshScrollProperties;
  l.refreshScrollProperties=()=>{
   const size=l._viewSize;
   if(size){
    const previous=l.officeAILastSize;
    const base=previous&&size.pY===previous.padded?previous.base:size.pY;
    const anchor=l.getDocumentAnchorSection();
    const padded=Math.max(base,anchor.size[1])+this.padding*a.dpiScale;
    const next=size.clone();next.pY=padded;l._viewSize=next;
    l.officeAILastSize={base,padded};
   }
   return original.call(l);
  };
  l.refreshScrollProperties();a.sectionContainer.requestReDraw();
 }
 reserve(height) {this.padding=height+48;if(this.app){this.layout();this.app.activeDocument.activeLayout.refreshScrollProperties();this.app.sectionContainer.requestReDraw();}}
 comments() {
  this.connect();const list=this.app.sectionContainer.getSectionWithName(this.app.CSections.CommentList.name);
  return (list?.sectionProperties.commentList||[]).filter(c=>!c.sectionProperties.data.trackchange).map(c=>({id:c.sectionProperties.data.id,text:c.sectionProperties.contentText?.textContent||'',object:c,list}));
 }
 selectComment(id) {
  const c=this.comments().find(c=>String(c.id)===id);if(!c)throw Error('批注已删除，请刷新');
  c.list.select(c.object,true);return c.text;
 }
 async capture() {
  this.connect();this.app.idleHandler?.notifyActive();
  if(!this.selection||!this.selection.replace('textselection:','').trim())throw Error('请先在文档中选择要修改的文字');
  const epoch=this.epoch,selection=this.selection;
  const text=await new Promise((resolve,reject)=>{
   const done=e=>{clearTimeout(timer);this.map.off('textselectioncontent',done);const doc=new DOMParser().parseFromString(e.html||'','text/html');resolve(e.plainText||doc.body.textContent||'');};
   const timer=setTimeout(()=>{this.map.off('textselectioncontent',done);reject(Error('读取选区超时，请重新选择'));},4000);
   this.map.on('textselectioncontent',done);this.app.socket.sendMessage('gettextselection mimetype=text/html,text/plain;charset=utf-8');
  });
  if(epoch!==this.epoch||!text.trim())throw Error('选区已变化，请重新选择');
  return {epoch,selection,text,layer:this.layer};
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
