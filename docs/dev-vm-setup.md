# 开发虚拟机交付（2026-10-15）

## 配置与访问

- 宿主机：build.example.invalid 对应的 cocoserver，保持现有 Ubuntu/k3s。
- VM：build-host，KVM/QEMU + libvirt，4 vCPU、16384 MiB 内存、200 GiB qcow2 磁盘，已设置开机自启动。
- 系统：Ubuntu 24.04.5 LTS 最小基础镜像 + XFCE/Xorg 精简桌面，无完整 GNOME/办公套件。
- 用户名：codex。独立随机密码只保存在本机 outputs/dev-vm-access.txt，不写入 Git。
- 管理地址：PRIVATE_NETWORK_ADDRESS；宿主机管理网卡：PRIVATE_NETWORK_ADDRESS。
- 局域网地址：PRIVATE_NETWORK_ADDRESS，MAC 52:54:00:42:15:01。
- 远程桌面 TCP 3389，IPv4/IPv6 双栈，TLS；断开客户端后保留桌面，重新连接复用同一用户会话。
- 本次优先用于域名 AAAA 的 IPv6：PRIVATE_IPV6_ADDRESS。

SLAAC 地址的接口标识随固定 MAC 保持一致，已验证 VM 重启后不变；另一个 DHCPv6 地址在重启时发生过变化，不建议将其作为此处固定连接地址。运营商下发前缀变化时，路由器/DDNS 需要更新 AAAA。

路由器由用户配置：放行目的虚拟机 IPv6 的 TCP 3389，并把所选域名 AAAA 指向上述地址。没有修改路由器或域名记录；公网端到端 RDP 需用户完成这一步后验收。RDP 首次连接为自签名 TLS，可核对指纹：

EC:AF:F5:A5:A5:72:C4:9F:AF:C9:74:53:1E:11:EB:8E:B6:F8:BD:0A:41:E1:AD:68:BB:88:2A:01:F2:3E:1F:70

## 开发工作区

<workspace>/cocolian 已迁移当前门户/WOPI 代码、配置、脚本、说明及上游源码快照，并初始化 Git。省略 upstream 的 Git 对象和 node_shrinkpack 缓存，原始上游提交在 docs/upstream-lock.json；完整引擎源码编译仍需单独准备。

已安装：
- 官方 ChatGPT Linux 客户端 26.1007.71326；登录桌面自动打开，已实际显示中文登录界面。需用户登录自己的 ChatGPT 账号，尚未验收登录后的模型调用。
- 客户端附带 Codex CLI 通过 codex 命令可用，当前为 0.162.0-alpha.17.2。
- Chrome 155、Node.js v24.22.0、Python 3、Git、Docker 29.1.3、Buildx、kubectl v1.35.5。
- 项目 .venv 中 Playwright 1.64，使用系统 Chrome，不重复下载 Chromium。
- 中文字体与 IBus 智能拼音。可通过输入法托盘或快捷键切换。

终端示例：

```sh
cd ~/projects/cocolian
kubectl get pods -A
kubectl top nodes
OFFICE_IMAGE_NAME=docker.io/cocolian/office-portal:my-change python3 scripts/build-oci.py
scripts/import-office-image.sh build/office-portal.tar
# 使用导入返回的 deployment_image 摘要更新 office-lab，发布前先备份并验证。
```

镜像导入 SSH 密钥只能从 VM 管理地址调用宿主机受限导入程序，不能登录宿主机 Shell、转发端口或执行其他命令；程序校验 OCI 路径、SHA256、Linux amd64、应用用户和仓库前缀，只接受 docker.io/cocolian/office-portal 镜像。

kubeconfig 为独立 ServiceAccount：全局只读诊断，office-lab 内允许应用发布与排错，不提供其他 Namespace 写权限、Secret 直接读取权限或集群管理员证书。office-lab 已启用 baseline Pod 安全限制。退役时应删除 build-host-api-token Secret、ServiceAccount/相关绑定以及宿主机带 build-host-office-image 标记的受限 SSH 公钥。

## 网络与维护

局域网接口采用 macvtap，不重配宿主机物理网卡。另设隔离管理网卡解决 macvtap 主客通信。ChatGPT/Chrome/开发工具使用现有宿主机代理 PRIVATE_NETWORK_ADDRESS:7770，管理 API 走直连；仅 VM 自身的软件源、环境及 Docker 代理被配置，宿主机 DNS、默认路由和原有代理未改。

安装包来自 Ubuntu 官方云镜像与官方 ChatGPT Linux 文档下载链接；Ubuntu、Node、kubectl 均核对官方 SHA256，ChatGPT 包 SHA256：0e006b4931712f5a90d4cd04972c6e0b533cedcdfdb2b51946d5b9367471f556。

创建配置在 deploy/vm，安装维护脚本在 scripts/vm。源码与构建不依赖临时安装包 HTTP 服务，该服务验收后已关闭。临时 RDP 测试客户端、截图/虚拟显示工具及重复安装包已清理。

## 已验证与待用户完成

已验证 VM 重启、IPv6 地址持续性、真实 IPv6 RDP 登录及断线重连、ChatGPT 图形界面、独立源码构建/镜像导入、受限 kubectl、带沙箱 Chrome + Playwright 访问 Office HTTPS。现有全部 12 个 k3s Pod 的 UID、镜像、就绪与重启次数对比未变，宿主机 netplan 文件对比未变。

待用户完成：路由器 IPv6 入站放行及域名 AAAA、ChatGPT 账号登录。安装并显示登录界面不等于已验证账号的模型/插件权限。
