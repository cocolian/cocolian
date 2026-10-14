#!/bin/sh
set -eu
ssh -J aliserver -o BatchMode=yes -o HostKeyAlias=rdp.cocolian.cn -o StrictHostKeyChecking=yes shamphone@192.168.99.2 'kubectl -n office-lab rollout undo deployment/wopi && kubectl -n office-lab rollout status deployment/wopi --timeout=120s'
