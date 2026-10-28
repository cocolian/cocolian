# 开发与发布约定

## CSV
所有字段（含表头、数字和空值）使用双引号；用标准序列化工具，例如 Python csv.QUOTE_ALL。双引号转义为两个双引号。导出后用标准解析器回读并核对记录。

## 项目
- apps/office-portal 是门户和 WOPI Host；editor.json 控制语言与默认紧凑工具栏（ui_mode=compact）。
- 所有修改先落在本地源码或配置，再编译打包、推送镜像仓库并更新 k3s；不直接修改 Pod 文件。
- upstream 保存官方源码；Collabora main 与线上 CODE 25.04 不同，不能直接替换其浏览器资源。
- deploy、scripts、docs 分别保存部署、构建验证和操作说明。
- 不把密码、访问 token、kubeconfig 或 SSH 私钥提交到 Git。

## 服务器与权限
- 开发环境及管理地址由仓库外的私有配置提供。
- k3s 部署默认仅操作 office-lab。其他 Namespace 先只读检查；写入生产环境需要用户明确授权。
- 先检查 Pod、日志、事件、配额和资源，再决定修改。
- 保留原镜像摘要、Deployment 配置和文档卷。发布验证失败时回滚，不删除 PVC 作为排错手段。
- Collabora、转换服务和门户使用 配置的镜像仓库 的不可变镜像摘要及 IfNotPresent；新镜像先推送仓库并确认节点拉取，再更新 Deployment。保留的 gateway 镜像仍为 Never。
- 不修改宿主机 DNS、默认路由或代理；开发机自己的工具代理可按 docs 配置。

## 验证
- 验证登录、编辑器启动、WOPI 保存和 DOCX 转 PDF；必要时使用 Playwright。
- 对照发布前后其他 Namespace 的 Pod UID、镜像、就绪与重启次数，区分已验证结果和未验收项。

## 开发机构建
- 项目位于 ${WORKSPACE}/cocolian。Python 验证环境为 .venv，Chrome 使用系统安装的 google-chrome。
- OFFICE_IMAGE_NAME=docker.io/cocolian/office-portal:<tag> python3 scripts/build-oci.py 在本机生成 OCI 包；scripts/import-office-image.sh 导入镜像后返回可用于 Deployment 的摘要。
- scripts/vm 为安装引导与运维脚本；除明确说明外，不要在开发 VM 中重跑宿主机或新建虚拟机脚本。
- 上游源码快照已迁移，省略 .git 对象和 node_shrinkpack npm 缓存；原始提交参考 docs/upstream-lock.json，完整引擎源码编译另行准备。
