#!/usr/bin/python3
"""Forced SSH command: import a validated local-source Office OCI image only."""
import sys,os,tempfile,tarfile,json,hashlib,re,subprocess,pathlib
if os.geteuid()!=0:raise SystemExit('Root execution required')
base=pathlib.Path('/var/lib/dev-vm/imports');base.mkdir(mode=0o700,exist_ok=True)
fd,name=tempfile.mkstemp(prefix='office-',suffix='.tar',dir=base)
try:
 size=0
 with os.fdopen(fd,'wb') as out:
  while block:=sys.stdin.buffer.read(1024*1024):
   size+=len(block)
   if size>2*1024**3:raise ValueError('Image exceeds 2 GiB limit')
   out.write(block)
 with tarfile.open(name) as archive:
  entries={}
  for member in archive.getmembers():
   if not member.isfile() or member.name in entries:raise ValueError('Unsupported archive member')
   if member.name not in ('oci-layout','index.json') and not re.fullmatch(r'blobs/sha256/[a-f0-9]{64}',member.name):raise ValueError('Unsupported OCI path')
   entries[member.name]=member
   if member.name.startswith('blobs/'):
    digest=hashlib.sha256()
    with archive.extractfile(member) as source:
     while chunk:=source.read(1024*1024):digest.update(chunk)
    if digest.hexdigest()!=member.name.rsplit('/',1)[1]:raise ValueError('Blob digest mismatch')
  def read_json(path):
   if entries[path].size>2*1024*1024:raise ValueError('JSON object too large')
   return json.load(archive.extractfile(entries[path]))
  index=read_json('index.json');assert len(index['manifests'])==1
  descriptor=index['manifests'][0];digest=descriptor['digest']
  if descriptor.get('mediaType')!='application/vnd.oci.image.manifest.v1+json':raise ValueError('Expected a single OCI image manifest')
  assert re.fullmatch(r'sha256:[a-f0-9]{64}',digest)
  image=descriptor.get('annotations',{}).get('io.containerd.image.name','')
  if not re.fullmatch(r'docker\.io/cocolian/office-portal:[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',image):raise ValueError('Image repository is not allowed')
  manifest=read_json('blobs/sha256/'+digest.split(':')[1])
  if manifest.get('mediaType')!='application/vnd.oci.image.manifest.v1+json' or 'manifests' in manifest:raise ValueError('Nested image indexes are not allowed')
  config=read_json('blobs/sha256/'+manifest['config']['digest'].split(':')[1])
  if config.get('architecture')!='amd64' or config.get('os')!='linux':raise ValueError('Expected Linux amd64')
  if config.get('config',{}).get('User')!='1000:1000':raise ValueError('Expected unprivileged Office application user')
 def ctr(*args):
  result=subprocess.run(['/usr/local/bin/k3s','ctr','-n','k8s.io',*args],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr[-1000:])
 ctr('images','import','--platform','linux/amd64',name)
 ctr('images','label',image,'io.cri-containerd.image=managed')
 pin='docker.io/cocolian/office-portal@'+digest
 # A repeated import of the same digest is harmless.
 result=subprocess.run(['/usr/local/bin/k3s','ctr','-n','k8s.io','images','tag',image,pin],capture_output=True,text=True)
 if result.returncode and 'already exists' not in result.stderr:raise RuntimeError(result.stderr[-1000:])
 print(json.dumps({'image':image,'digest':digest,'deployment_image':pin,'bytes':size}))
finally:
 pathlib.Path(name).unlink(missing_ok=True)
