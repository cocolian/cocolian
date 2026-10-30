"""Persistent comment/revision lifecycle. No document text or provider credentials stored."""
import json
import re
import sqlite3
import time
import uuid
from collections import Counter

KEY = re.compile(r'[0-9a-f]{64}')

class ReviewConflict(Exception):
    pass


def _key(value):
    if not isinstance(value, str) or not KEY.fullmatch(value): raise ValueError('无效关联标识')
    return value


def update(data, file_id, payload, now=None):
    now = time.time() if now is None else now
    if not isinstance(payload,dict): raise ValueError('请求无效')
    op=payload.get('op');client=payload.get('client','')
    if op not in ('sync','begin','prepare','record','finish','heartbeat','manual','review-start','review-end'): raise ValueError('未知审阅操作')
    if not isinstance(client,str) or not 1<=len(client)<=64: raise ValueError('客户端标识无效')
    comments=payload.get('comments',[]);revisions=payload.get('revisions',[])
    if not isinstance(comments,list) or len(comments)>1000 or not isinstance(revisions,list) or len(revisions)>4000: raise ValueError('审阅数据过多')
    live={}
    for item in comments:
        if not isinstance(item,dict):raise ValueError('批注状态无效')
        key=_key(item.get('key'));ident=item.get('id');resolved=item.get('resolved')
        if not isinstance(ident,str) or not 1<=len(ident)<=64 or not isinstance(resolved,bool) or key in live: raise ValueError('批注状态无效')
        live[key]={'id':ident,'resolved':resolved,'thread':_key(item.get('thread',key))}
    active=Counter(_key(x) for x in revisions)
    decisions=payload.get('decisions',{})
    if not isinstance(decisions,dict) or len(decisions)>4000: raise ValueError('审阅结果无效')
    for key,value in decisions.items():
        _key(key)
        if value not in ('accepted','rejected','unknown'): raise ValueError('审阅结果无效')
    with sqlite3.connect(str(data/'.ai-review.sqlite3'),timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS review (file_id TEXT PRIMARY KEY, state TEXT NOT NULL)')
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT state FROM review WHERE file_id=?',(file_id,)).fetchone()
        state=json.loads(row[0]) if row else {'comments':{},'lease':None}
        records=state['comments'];lease=state['lease']
        if lease and lease['expires']<=now:
            for record in records.values():
                if record.get('job')==lease['token']:
                    record['working']=False
                    if record.get('prepared') and not record.get('links'): record['uncertain']=True
            state['lease']=lease=None
        for key,item in live.items():
            if key in records:
                records[key]['id']=item['id'];records[key]['resolved']=item['resolved'];records[key]['thread']=item['thread']
        review_lease=state.get('review_lease')
        if review_lease and review_lease['expires']<=now:state['review_lease']=review_lease=None
        if op=='review-start':
            if review_lease and review_lease['owner']!=client:raise ReviewConflict('其他用户正在审阅，请稍后重试')
            review_token=review_lease['token'] if review_lease else uuid.uuid4().hex
            state['review_lease']={'owner':client,'token':review_token,'expires':now+30}
        elif op=='review-end':
            if review_lease and review_lease['owner']==client and payload.get('review_token')==review_lease['token']:state['review_lease']=None
        elif op=='sync':
            history=payload.get('history',False)
            if not isinstance(history,bool): raise ValueError('历史状态无效')
            for record in records.values():
                for link in record.get('links',[]):
                    stamp=link['key']
                    if active[stamp]>1:
                        record['uncertain']=True
                    if stamp in active:
                        if history or link['outcome'] in ('accepted','rejected'):
                            link['outcome']='pending';record['hold_open']=False
                    elif stamp in decisions:
                        link['outcome']=decisions[stamp]
                    elif link['outcome']=='pending':
                        link['outcome']='unknown'
        elif op=='begin':
            if lease: raise ReviewConflict('已有 AI 修改任务正在处理此文档，请稍后再试')
            token=uuid.uuid4().hex;eligible=[]
            for key,item in live.items():
                record=records.get(key,{})
                pending=record.get('uncertain') or any(l['outcome'] in ('pending','unknown') for l in record.get('links',[]))
                if item['resolved'] or pending or (record.get('complete') and not record.get('hold_open') and record.get('links') and all(l['outcome']=='accepted' for l in record['links'])): continue
                eligible.append(key)
                records[key]={'id':item['id'],'thread':item['thread'],'resolved':False,'links':[],'complete':False,'working':True,'job':token,'prepared':False,'uncertain':False,'auto_resolved':False,'manual':False}
            state['lease']={'token':token,'owner':client,'expires':now+600}
        elif op in ('prepare','record','finish','heartbeat'):
            token=payload.get('token')
            if not lease or token!=lease['token'] or lease['owner']!=client: raise ReviewConflict('AI 任务已失效，已停止继续写入')
            lease['expires']=now+600
            keys=payload.get('keys',[])
            if not isinstance(keys,list) or len(keys)>100: raise ValueError('关联批注无效')
            keys=[_key(k) for k in keys]
            if any(k not in records or records[k].get('job')!=token for k in keys): raise ValueError('批注不属于本任务')
            if op=='prepare':
                for key in keys: records[key]['prepared']=True
            elif op=='record':
                linked=payload.get('linked',[])
                if not isinstance(linked,list) or len(linked)>100: raise ValueError('修订关联过多')
                linked=[_key(k) for k in linked]
                certain=payload.get('certain',False)
                if not isinstance(certain,bool): raise ValueError('关联状态无效')
                for key in keys:
                    record=records[key]
                    if not certain or not linked or any(active[k]!=1 for k in linked): record['uncertain']=True
                    for stamp in linked:
                        if stamp not in {x['key'] for x in record['links']}: record['links'].append({'key':stamp,'outcome':'pending'})
            elif op=='heartbeat':pass
            else:
                complete=payload.get('complete',[])
                if not isinstance(complete,list) or len(complete)>100: raise ValueError('完成状态无效')
                complete={_key(k) for k in complete}
                for key,record in records.items():
                    if record.get('job')==token:
                        record['working']=False;record['complete']=key in complete and bool(record['links']) and not record['uncertain']
                        if record['prepared'] and not record['links']:record['uncertain']=True
                state['lease']=None
        elif op=='manual':
            key=_key(payload.get('key'));resolved=payload.get('resolved')
            if key not in live or not isinstance(resolved,bool) or live[key]['resolved']!=resolved:raise ValueError('未确认原生批注状态')
            record=records.get(key)
            if record:
                record['manual']=resolved;record['auto_resolved']=False;record.pop('action',None)
                if not resolved and payload.get('history'):
                    record['hold_open']=True
                elif not resolved and not any(l['key'] in active for l in record.get('links',[])):
                    record.update(links=[],complete=False,uncertain=False,prepared=False,working=False)
        def accepted_record(record):
            links=record.get('links',[])
            return bool(links) and all(l['outcome']=='accepted' and l['key'] not in active for l in links) and record.get('complete') and not record.get('uncertain') and not record.get('working') and not record.get('hold_open')
        statuses={};actions=[]
        for key,record in records.items():
            if key not in live: continue
            item=live[key];links=record.get('links',[])
            pending=any(l['outcome'] in ('pending','unknown') or l['key'] in active for l in links)
            accepted=bool(links) and all(l['outcome']=='accepted' and l['key'] not in active for l in links)
            rejected=any(l['outcome']=='rejected' for l in links)
            thread=[(k,c) for k,c in live.items() if c['thread']==item['thread']]
            thread_ready=all(c['resolved'] or accepted_record(records.get(k,{})) for k,c in thread)
            thread_pending=any(any(l['outcome'] in ('pending','unknown') or l['key'] in active for l in records.get(k,{}).get('links',[])) for k,c in thread)
            ready_to_resolve=accepted_record(record) and thread_ready
            target=None
            if ready_to_resolve and not record.get('manual'):
                record['auto_resolved']=True
                if not item['resolved']:target=True
            elif record.get('auto_resolved') and (pending or thread_pending) and item['resolved'] and not record.get('manual'):
                target=False
            if item['resolved'] and target is not False:status='resolved'
            elif record.get('working'):status='generating'
            elif record.get('uncertain') or any(l['outcome']=='unknown' for l in links):status='needs_review'
            elif pending or (accepted_record(record) and not thread_ready):status='pending_review'
            elif rejected:status='ready'
            elif ready_to_resolve:status='accepted'
            else:status='ready'
            statuses[key]={'id':item['id'],'state':status,'skip':pending or (accepted_record(record) and not thread_ready) or record.get('uncertain',False) or item['resolved'] or record.get('working',False),'complete':record.get('complete',False)}
            action=record.get('action')
            if target is not None:
                if not action or action['expires']<=now or action['owner']==client:
                    record['action']={'owner':client,'expires':now+15,'resolved':target}
                    actions.append({'key':key,'id':item['id'],'resolved':target})
            else:record.pop('action',None)
        # Bound historical entries; never discard active review links.
        if len(records)>2000:
            for key in list(records):
                if key not in live and not records[key].get('working'): del records[key]
                if len(records)<=2000:break
        current_states={k:v['state'] for k,v in statuses.items()}
        changed_states={k:v for k,v in current_states.items() if state.get('states',{}).get(k)!=v}
        if changed_states or decisions or op in ('begin','prepare','record','finish','manual'):
            events=state.setdefault('events',[])
            events.append({'time':now,'operation':op,'client':client,'states':changed_states,'decisions':decisions})
            state['events']=events[-500:]
        state['states']=current_states
        db.execute('INSERT OR REPLACE INTO review VALUES (?,?)',(file_id,json.dumps(state,separators=(',',':'))))
        result={'statuses':statuses,'actions':actions}
        if op=='begin':result.update(token=token,eligible=eligible)
        if op=='review-start':result['review_token']=review_token
        return result
