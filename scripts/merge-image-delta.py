"""Reassemble an OCI archive from the unchanged base plus a local-source delta."""
import sys,tarfile,io
blobs={}
for path in sys.argv[1:3]:
 with tarfile.open(path) as t:
  for m in t.getmembers():
   if m.isfile() and (m.name.startswith('blobs/') or m.name in ('oci-layout','index.json')):blobs[m.name]=t.extractfile(m).read()
with tarfile.open(sys.argv[3],'w') as t:
 for name,data in blobs.items():
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;t.addfile(info,io.BytesIO(data))
