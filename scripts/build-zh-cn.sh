#!/usr/bin/env bash
# Run in the cocolian-office workspace on codex-dev after fetching the pinned translations.
set -euo pipefail
root=${COCOLIAN_OFFICE_ROOT:-/home/codex/projects/cocolian-office}
source_root="$root/src/online.mirror"
build="$root/build/source-19b4efae7fb8"
translations="$source_root/engine/translations"
expected=17fb3698d5e86169d44076f7a992c572f8f780f1
test "$(git -C "$translations" rev-parse HEAD)" = "$expected"
test -s "$translations/source/zh-CN/officecfg/registry/data/org/openoffice/Office/UI.po"
mkdir -p "$build/source/engine/translations"
python3 -c 'import shutil,sys;shutil.copytree(sys.argv[1],sys.argv[2],dirs_exist_ok=True,ignore=shutil.ignore_patterns(".git"))' "$translations" "$build/source/engine/translations"
python3 - "$build" "$expected" "$source_root" "$translations" <<'PY'
import sys,json,hashlib,subprocess
from pathlib import Path
import shutil
build=Path(sys.argv[1]);
for relative in subprocess.check_output(['git','-C',sys.argv[3],'diff','19b4efae7fb8e9eda4a6d88baa959c838d3eb8c3','--name-only','--','browser','wsd']).decode().splitlines():
 src=Path(sys.argv[3])/relative;dest=build/'source'/relative
 if not src.is_file():raise SystemExit('Unsupported removed source: '+relative)
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
browser_diff=subprocess.check_output(['git','-C',sys.argv[3],'diff','19b4efae7fb8e9eda4a6d88baa959c838d3eb8c3','--binary','--','browser']);translation_diff=subprocess.check_output(['git','-C',sys.argv[4],'diff',sys.argv[2],'--binary']);seed=('zh-CN:19b4efae7fb8e9eda4a6d88baa959c838d3eb8c3:'+sys.argv[2]).encode()+browser_diff+translation_diff;revision=hashlib.sha256(seed).hexdigest()[:10]
(build/'source/dist_git_hash').write_text(revision+'\n')
record={'repository':'https://gerrit.collaboraoffice.com/translations','branch':'distro/collabora/co-26.04','commit':sys.argv[2],'languages':['en-US','zh-CN'],'ui_revision':revision,'browser_patch_sha256':hashlib.sha256(browser_diff).hexdigest(),'translation_patch_sha256':hashlib.sha256(translation_diff).hexdigest()}
record['server_patch_sha256']=hashlib.sha256(subprocess.check_output(['git','-C',sys.argv[3],'diff','19b4efae7fb8e9eda4a6d88baa959c838d3eb8c3','--binary','--','wsd'])).hexdigest()
(build/'zh-cn-build-lock.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
PY
docker run -d -e BUILD_ENGINE="${BUILD_ENGINE:-1}" --name "${ZH_BUILD_NAME:-cocolian-zh-cn-build}" --cpus=3 --memory=10g \
 -v "$build:/workspace" cocolian-office-builder:debian13 bash -lc '
set -euo pipefail
export CCACHE_DIR=/workspace/cache/ccache CCACHE_MAXSIZE=8G
if test "$BUILD_ENGINE" = 1; then
cd /workspace/engine
../source/engine/autogen.sh --with-distro=CPLinux-LOKit --disable-epm --without-package-format --disable-symbols --without-java --disable-python --without-myspell-dicts --without-fonts --disable-noto-font --with-lang="en-US zh-CN" --with-parallelism=3
make -j3 build
else
test -s /workspace/engine/instdir/program/resource/zh_CN/LC_MESSAGES/svx.mo
fi
cd /workspace/source
./config.status --recheck
./config.status
make -j3
DESTDIR=/workspace/stage make install
cp -a /workspace/engine/instdir/. /workspace/stage/opt/collaboraoffice/
echo ZH_CN_BUILD_COMPLETE
'
