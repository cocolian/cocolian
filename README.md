# 本地源码工作区

目录规划见 [docs/directory-plan.md](docs/directory-plan.md)，源码版本见 [docs/upstream-lock.json](docs/upstream-lock.json)，本地构建见 [docs/local-build.md](docs/local-build.md)。原部署说明保留如下。

# office.example.invalid 部署与访问

2026-10-14 已接入现有 edge-proxy 反向代理。所有应用保持在 k3s 的独立 Namespace `office-lab`，原有资源限制及数据卷保留。

## 访问

入口：<https://office.example.invalid/>。登录后可选择 Alice、Bob 共同编辑同一份测试 DOCX，或上传 DOCX 转为 PDF。

本机自动登录：

```bash
python3 <workspace>/cocolian/outputs/open-office.py
```

脚本通过已有 SSH 权限读取 `office-lab/lab-auth` 的访问密钥，打开 HTTPS 入口并建立 Secure、HttpOnly、SameSite=Lax 的登录 Cookie；随后浏览器地址清除密钥参数。Cookie 有效期 4 小时。无需运行旧的 SSH 端口转发脚本。

如需手工登录或调用 API，可使用该脚本的 `--print-key` 选项在本人终端读取访问密钥。密钥不写入配置清单、报告或验证证据。

| 路径 | 用途 | 访问要求 |
|---|---|---|
| `/` | 登录、在线编辑入口、DOCX 转 PDF 表单 | 访问密钥登录 |
| `/edit?user=Alice`、`/edit?user=Bob` | 两个独立用户编辑同一测试文档 | 登录 Cookie |
| `/browser/`、`/cool/`、`/hosting/` | Collabora 前端、WSS 和发现接口 | 编辑会话使用独立 WOPI 令牌 |
| `/convert/forms/libreoffice/convert` | HTTP multipart DOCX 转 PDF | 登录 Cookie 或 `Authorization: Bearer <访问密钥>` |

转换 API 使用 POST，文件字段名为 `files`，例如 multipart 的 `files=@example.docx`；请求体上限 20 MiB。网页表单会自动携带登录 Cookie。

## 实际路由

浏览器 HTTPS/WSS → edge-proxy（EDGE_PROXY_ADDRESS）Nginx → WireGuard `PRIVATE_NETWORK_ADDRESS → PRIVATE_NETWORK_ADDRESS:80` → `office-lab/office` Ingress → WOPI/Nginx 网关 → Collabora 或 LibreOffice/Gotenberg。

TLS 在 edge-proxy 终止，复用覆盖 `*.example.invalid` 的现有证书。集群 Office Ingress 只接受 `PRIVATE_NETWORK_ADDRESS/32` 的代理来源；直接访问节点 Office 路由返回 403。转换 API 未授权请求返回 401。

WOPI 与 Collabora 的文件请求仍走 Namespace 内部地址 `http://wopi:8080/wopi/files/1`。Collabora 公共地址设为 `office.example.invalid:443`，启用外层 TLS 终止模式，浏览器编辑连接为 WSS。

Office 的 Nginx 访问日志仅记录路径、不记录查询参数和认证头；该 Ingress 关闭包含请求查询参数的默认访问日志。

## 已验证结果

- 正常证书校验下 HTTPS 首页和 HEAD 返回 200，HTTP 返回 301 跳转 HTTPS。
- 安全 Cookie 登录、错误密钥拒绝、匿名/错误 Bearer 转换请求 401，正确 Bearer 转换健康请求 200；内部鉴权端点不对外开放。
- 两个独立浏览器上下文通过公网 HTTPS 打开同一 DOCX，双向无需刷新即可读到对方输入，WSS 编辑和 WOPI 保存回写成功。
- 保存文件包含 `ALICE-HTTPS-20261014` 与 `BOB-HTTPS-20261014`；随后通过公网转换接口得到 HTTP 200、1 页 PDF、19,524 字节，中英文文本及页面渲染通过检查。
- 原有 9 个其他 Namespace Pod 的 UID、状态、就绪、重启数和镜像与接入前一致；edge-proxy Nginx 主进程 PID 保持 2314245，仅平滑重载。共享配置仅移除 Office 域名，其他域名内容保持不变。

验证为双用户、单份受控 DOCX 的功能检查，不代表复杂文档兼容性、容量或生产安全验收。服务继续采用原单副本测试配置。

证据位于 `outputs/`：`https-access-check.json`、`https-collaboration-check.json`、`https-conversion-check.json`、`domain-services-check.json`、`edge-change-receipt.json`、`open-office-check.json`；编辑截图和 PDF 预览同目录保存。

## 配置和回退

新配置：edge-proxy `/etc/nginx/conf.d/office.example.invalid.conf`；共享 `/etc/nginx/conf.d/example.invalid.conf` 仅移除了 `office.example.invalid` 的声明。

边缘备份：`/etc/nginx/backup/office-lab-3u9i_jc9/example.invalid.conf`。

k3s 回退清单：`/var/lib/office-lab/backups/domain-20261014/rollback-resources.json`（仅原 Collabora、WOPI Deployment 和 lab-source ConfigMap）。回退时先删除 `office-lab/office` Ingress 和 `office-lab/office-ingress` NetworkPolicy，再应用该清单；最后恢复边缘备份、移除独立 Office 配置，经 `nginx -t` 成功后平滑重载。回退前需检查共享文件是否存在其他后续改动。无需删除 Namespace、PVC、Secret 或测试文档。

本地最终清单为 `outputs/office-lab.yaml`，不含 Secret；镜像使用原固定摘要和 `imagePullPolicy: Never`，因此重建节点前须准备相同镜像缓存。

## Mac 开发

本机开发目录与迁移说明见 [docs/mac-development.md](docs/mac-development.md)。
