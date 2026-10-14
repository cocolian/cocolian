# 开发与发布约定

## CSV
所有字段（含表头、数字和空值）使用双引号；用标准序列化工具，例如 Python csv.QUOTE_ALL。双引号转义为两个双引号。导出后用标准解析器回读并核对记录。

## 项目
- apps/office-portal 是门户和 WOPI Host；editor.json 控制语言与紧凑工具栏。
- upstream 保存官方源码；Collabora main 与线上 CODE 25.04 不同，不能直接替换其浏览器资源。
- deploy、scripts、docs 分别保存部署、构建验证和操作说明。
- 不把密码、访问 token、kubeconfig 或 SSH 私钥提交到 Git。

## 服务器与权限
- 开发 VM 为 build-host，管理地址 PRIVATE_NETWORK_ADDRESS；宿主机管理地址 PRIVATE_NETWORK_ADDRESS。
- k3s 部署默认仅操作 office-lab。其他 Namespace 先只读检查；写入生产环境需要用户明确授权。
- 先检查 Pod、日志、事件、配额和资源，再决定修改。
- 保留原镜像摘要、Deployment 配置和文档卷。发布验证失败时回滚，不删除 PVC 作为排错手段。
- 当前镜像拉取策略为 Never，新镜像须先导入宿主机 containerd，再更新 Deployment 摘要。
- 不修改宿主机 DNS、默认路由或代理；开发机自己的工具代理可按 docs 配置。

## 验证
- 验证登录、编辑器启动、WOPI 保存和 DOCX 转 PDF；必要时使用 Playwright。
- 对照发布前后其他 Namespace 的 Pod UID、镜像、就绪与重启次数，区分已验证结果和未验收项。
