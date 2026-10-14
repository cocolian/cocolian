"""Resume a TLS download using validated HTTP ranges; proxy stays process-local."""
import urllib.request,concurrent.futures,pathlib,sys,time,json
url,destination=sys.argv[1:3]
workers=int(sys.argv[3]) if len(sys.argv)>3 else 16
path=pathlib.Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
proxy=urllib.request.ProxyHandler({'http':'http://127.0.0.1:7770','https':'http://127.0.0.1:7770'})
opener=urllib.request.build_opener(proxy)
with opener.open(urllib.request.Request(url,method='HEAD'),timeout=90) as r:
 size=int(r.headers['Content-Length']);etag=r.headers.get('ETag')
partdir=path.with_name(path.name+'.parts');partdir.mkdir(exist_ok=True)
chunk=4*1024*1024
jobs=[(i,start,min(start+chunk,size)-1) for i,start in enumerate(range(0,size,chunk))]
def part(job):
 i,start,end=job;target=partdir/str(i)
 if target.exists() and target.stat().st_size==end-start+1:return target.stat().st_size
 for attempt in range(6):
  try:
   headers={'Range':f'bytes={start}-{end}'}
   if etag:headers['If-Range']=etag
   with opener.open(urllib.request.Request(url,headers=headers),timeout=180) as r:
    assert r.status==206 and r.headers.get('Content-Range')==f'bytes {start}-{end}/{size}',(r.status,r.headers.get('Content-Range'))
    content=r.read();assert len(content)==end-start+1
   temp=target.with_suffix('.tmp');temp.write_bytes(content);temp.replace(target);return len(content)
  except Exception:
   if attempt==5:raise
   time.sleep(min(2**attempt,16))
completed=0
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
 for count,future in enumerate(concurrent.futures.as_completed([pool.submit(part,j) for j in jobs]),1):
  completed+=future.result()
  if count%8==0 or count==len(jobs):print(json.dumps({'download':path.name,'completed_MiB':round(completed/1048576,1),'total_MiB':round(size/1048576,1)}),flush=True)
temp=path.with_suffix(path.suffix+'.complete')
with temp.open('wb') as out:
 for i,_,_ in jobs:
  with (partdir/str(i)).open('rb') as data:
   while buf:=data.read(1024*1024):out.write(buf)
assert temp.stat().st_size==size;temp.replace(path)
print('COMPLETE',path.name,size,flush=True)
