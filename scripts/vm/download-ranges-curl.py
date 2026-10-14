"""Validated resumable parallel download using curl's TLS/HTTP implementation."""
import subprocess,concurrent.futures,pathlib,sys,time,json,re
url,destination=sys.argv[1:3];workers=int(sys.argv[3]) if len(sys.argv)>3 else 16
path=pathlib.Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
common=['curl','--proxy','http://127.0.0.1:7770','--max-time','240','--silent','--show-error','--location']
headers=subprocess.check_output(common+['--head',url],text=True)
size=int(re.findall(r'(?im)^content-length:\s*(\d+)',headers)[-1])
etags=re.findall(r'(?im)^etag:\s*([^\r\n]+)',headers);etag=etags[-1] if etags else None
partdir=path.with_name(path.name+'.parts');partdir.mkdir(exist_ok=True);chunk=4*1024*1024
jobs=[(i,start,min(start+chunk,size)-1) for i,start in enumerate(range(0,size,chunk))]
def part(job):
 i,start,end=job;target=partdir/str(i)
 if target.exists() and target.stat().st_size==end-start+1:return target.stat().st_size
 for attempt in range(6):
  try:
   temp=target.with_suffix('.tmp');h=target.with_suffix('.headers')
   args=common+['--range',f'{start}-{end}','--dump-header',str(h),'--output',str(temp),'--write-out','%{http_code}']
   if etag:args+=['--header','If-Range: '+etag]
   response=subprocess.check_output(args+[url],text=True)
   content_ranges=re.findall(r'(?im)^content-range:\s*([^\r\n]+)',h.read_text())
   assert response=='206' and content_ranges[-1]==f'bytes {start}-{end}/{size}',(response,content_ranges)
   assert temp.stat().st_size==end-start+1;temp.replace(target);h.unlink();return end-start+1
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
assert temp.stat().st_size==size;temp.replace(path);print('COMPLETE',path.name,size,flush=True)
