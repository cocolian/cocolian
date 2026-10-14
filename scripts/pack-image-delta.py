"""Produce an OCI delta for a server that has the exported base archive."""
from pathlib import Path
import tarfile
root=Path(__file__).resolve().parents[1]
with tarfile.open(root/'build/python-base.tar') as base:
 existing={m.name for m in base.getmembers() if m.name.startswith('blobs/')}
with tarfile.open(root/'build/office-portal.tar') as full,tarfile.open(root/'build/office-portal-delta.tar','w') as delta:
 for m in full.getmembers():
  if m.isfile() and m.name not in existing:delta.addfile(m,full.extractfile(m))
print('Delta bytes:',(root/'build/office-portal-delta.tar').stat().st_size)
