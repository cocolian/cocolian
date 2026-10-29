"""Package local Python source as an OCI image using an exported Python base."""
import tarfile,io,json,hashlib,gzip,pathlib,os
root=pathlib.Path(__file__).resolve().parents[1]
base=root/'build/python-base.tar'
blobs={}
with tarfile.open(base) as t:
 for m in t.getmembers():
  if m.isfile(): blobs[m.name]=t.extractfile(m).read()
def read(d): return json.loads(blobs['blobs/sha256/'+d['digest'].split(':')[1]])
index=json.loads(blobs['index.json'])
def manifest(d):
 o=read(d)
 if 'manifests' in o:
  for child in o['manifests']:
   plat=child.get('platform',{})
   if plat.get('architecture')=='amd64' and plat.get('os')=='linux':return manifest(child)
  return manifest(o['manifests'][0])
 return o
m=manifest(index['manifests'][0]); config=read(m['config'])
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as t:
 for filename in ('server.py','editor.json','file_open.py','file-open.js','file-open.css','file-open.svg','render_profile.py','project-homepage.html','project-homepage.css','community-qrcode.jpg'):
  data=(root/'apps/office-portal'/filename).read_bytes()
  info=tarfile.TarInfo('app/'+filename);info.size=len(data);info.mode=0o644;info.uid=1000;info.gid=1000;info.mtime=0
  t.addfile(info,io.BytesIO(data))
raw=buf.getvalue();layer=gzip.compress(raw,mtime=0)
def put(data,kind):
 digest=hashlib.sha256(data).hexdigest();blobs['blobs/sha256/'+digest]=data
 return {'mediaType':kind,'digest':'sha256:'+digest,'size':len(data)}
m['layers'].append(put(layer,'application/vnd.oci.image.layer.v1.tar+gzip'))
config['rootfs']['diff_ids'].append('sha256:'+hashlib.sha256(raw).hexdigest())
config['config'].update({'User':'1000:1000','WorkingDir':'/app','Entrypoint':None,'Cmd':['python','/app/server.py']})
config.setdefault('history',[]).append({'created_by':'COPY local office-portal source /app/server.py'})
m['config']=put(json.dumps(config,separators=(',',':')).encode(),'application/vnd.oci.image.config.v1+json')
m['mediaType']='application/vnd.oci.image.manifest.v1+json'
d=put(json.dumps(m,separators=(',',':')).encode(),m['mediaType'])
name=os.environ.get('OFFICE_IMAGE_NAME','docker.io/cocolian/office-portal:toolbar-20261014')
d['annotations']={'io.containerd.image.name':name,'org.opencontainers.image.ref.name':name.rsplit(':',1)[-1]}
blobs['index.json']=json.dumps({'schemaVersion':2,'manifests':[d]}).encode();blobs['oci-layout']=b'{"imageLayoutVersion":"1.0.0"}'
with tarfile.open(root/'build/office-portal.tar','w') as t:
 for path,data in blobs.items():
  if path not in ('index.json','oci-layout') and not path.startswith('blobs/'):continue
  info=tarfile.TarInfo(path);info.size=len(data);info.mtime=0;t.addfile(info,io.BytesIO(data))
(root/'build/image.json').write_text(json.dumps({'image':name,'digest':d['digest'],'source_sha256':hashlib.sha256(b''.join((root/'apps/office-portal'/f).read_bytes() for f in ('server.py','editor.json','file_open.py','file-open.js','file-open.css','file-open.svg','render_profile.py','project-homepage.html','project-homepage.css','community-qrcode.jpg'))).hexdigest()},indent=2))
print((root/'build/image.json').read_text())
