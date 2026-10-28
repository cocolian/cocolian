# 本地源码部署记录（2026-10-14）

> 地址和目录均为通用示例，实际部署值应由自己的私有配置提供。


已在 office-lab 发布自有门户/WOPI 服务，入口 https://office.example.invalid。

- 本地 OCI 打包产物：build/office-portal.tar。
- 镜像摘要：sha256:bf8bb76f3d025323701c01e83d1a8c0c68b18e701925f57697e0c3f3f55583b7。
- 门户源码：apps/office-portal/server.py。
- 上游仓库提交：docs/upstream-lock.json。
- 已发布 Deployment 清单：deploy/k8s/wopi.local-build.json。
- 服务备份：服务器 /var/lib/office-lab/backups/local-build-20261014/。

验证：错误密钥返回拒绝；正确登录及 Secure/HttpOnly Cookie 正常；390px 手机宽度无横向溢出；DOCX 转 PDF 返回 HTTP 200 与 PDF 文件；其他 9 个 Pod 的 UID、镜像、就绪与重启次数未变化。

完整 Collabora/LibreOffice 引擎未重新编译。Collabora 引擎仓库为部分克隆并稀疏检出浏览器文件；Gotenberg 与 SDK 示例为浅克隆。已有引擎版本、访问 Secret 和文档 PVC 保留。

双向协同复验通过：Alice 的新标记在 Bob 会话中无刷新可见，Bob 的新标记在 Alice 会话中无刷新可见；WOPI 保存后下载的 DOCX 包含两人的新标记。证据：outputs/local-build-collaboration-check.json。
