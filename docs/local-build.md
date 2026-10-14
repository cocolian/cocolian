# 本地构建与发布

本轮从 apps/office-portal/server.py 打包门户/WOPI 服务。Python 标准库服务无需额外编译步骤。scripts/build-oci.py 将本地源码作为新 OCI 层加入从测试服务器导出的、现用 Python 3.12 amd64 基础镜像，生成 build/office-portal.tar 与 build/image.json。不需要启动本地 Docker，也不会把本地 macOS 架构误用于服务器。

1. 基础镜像导出到 build/python-base.tar。
2. `python3 scripts/build-oci.py`
3. `python3 scripts/generate-deployment-patch.py`
4. 上传 OCI tar 与补丁；k3s ctr 导入，设置 CRI managed 标签及摘要别名。
5. `kubectl -n office-lab patch deployment wopi --type strategic --patch-file /tmp/deployment-patch.json`
6. 等待 rollout 并验证公开 HTTPS。

Dockerfile 提供另一条常规容器构建路径，本轮未使用 Docker 构建。基础 Python 镜像由既有摘要固定；Dockerfile 的 FROM 同样固定了基础镜像摘要。

持久备份目录：/var/lib/office-lab/backups/local-build-20261014/，内含 office-wopi-before.json 和 office-source-before.json。回滚可应用部署前的 Deployment 备份，恢复 Python 镜像及 /app ConfigMap 挂载；文档 PVC 和访问 Secret 不做替换。

Collabora、LibreOffice/Gotenberg 仍使用部署前的已验证引擎镜像。upstream-lock.json 记录获取的官方源码提交。上游 main 不等于线上引擎版本，不能直接以其前端替换旧引擎浏览器资源。

回滚脚本：`scripts/rollback-portal.sh`，回退到上一个 Deployment 版本；后续再次发布后需根据持久备份选择指定版本。本轮入口样式变更只影响自有门户，Collabora 原生编辑器界面未重新设计。

已发布清单：deploy/k8s/wopi.local-build.json。回放时使用已导入的本地镜像摘要，imagePullPolicy 为 Never；在新节点部署前必须先导入镜像包。
