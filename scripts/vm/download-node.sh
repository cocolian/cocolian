#!/bin/bash
set -euo pipefail
cd /var/lib/dev-vm/downloads
proxy=http://127.0.0.1:7770
curl --proxy "$proxy" -fsSL --max-time 60 https://nodejs.org/dist/index.json -o node-index.json
version=$(python3 -c 'import json; data=json.load(open("node-index.json")); print(next(x["version"] for x in data if x["version"].startswith("v24.") and x["lts"]))')
file="node-${version}-linux-x64.tar.xz"
curl --proxy "$proxy" -fsSL --retry 3 "https://nodejs.org/dist/$version/SHASUMS256.txt" -o node-SHASUMS256.txt
curl --proxy "$proxy" -fL --retry 3 "https://nodejs.org/dist/$version/$file" -o "$file"
grep "  $file$" node-SHASUMS256.txt | sha256sum -c -
printf '%s\n' "$file" > node-artifact-name.txt
