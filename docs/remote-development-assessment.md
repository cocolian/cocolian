# 远程开发桌面评估（2026-10-14）

## 建议

主开发桌面采用宿主机上的独立 KVM/QEMU 虚拟机，由 libvirt 管理，不把完整长期开发桌面作为 k3s Pod 部署。按当前 Collabora、WOPI 和 Linux 容器开发需求，首选 Ubuntu Desktop 24.04 LTS x86_64；如果必须让 ChatGPT 直接操控桌面应用（Computer Use），优先 Windows 11 Pro 虚拟机。

## 本次只读核验

- 宿主系统 Ubuntu 24.04.2 LTS，AMD Ryzen 7 5825U，8 核 16 线程。
- 内存约 58 GiB，当前 available 约 54 GiB；根文件系统剩余约 633 GiB。
- /dev/kvm 存在，kvm 与 kvm_amd 已加载，嵌套虚拟化参数为 1，QEMU 命令已安装。
- 未找到正在运行的 QEMU 虚拟机进程；libvirt 管理服务未运行，virsh/virt-install 不在当前 PATH 中。
- 3389、5900、6080 端口本次未见监听。k3s 内已有浏览器容器，但其定位不是完整长期开发桌面。
- 没有安装软件、创建虚拟机、修改防火墙或调整 k3s。

资源是当前快照，不是完整 LibreOffice 构建的压测结果；KVM 基础条件已具备，尚未进行实际虚拟机与桌面客户端验收。

## 客户端与操作系统

OpenAI 官方文档当前提供 ChatGPT Linux 桌面客户端预览版，支持 Ubuntu 24.04/26.04 LTS、Debian 13、Fedora 43/44 和 Arch，含 x64 包。Linux 预览版暂不支持 Computer Use，Wayland 原生支持仍为实验性，默认可经 XWayland 运行。

Windows 客户端支持原生 PowerShell 开发和 WSL2。需要标准 Windows RDP 服务端时选择 Pro，Home 不能作为内置 RDP 服务端。Windows 路线需准备相应许可；若在 VM 内使用 WSL2，需要进一步验证嵌套虚拟化与实际兼容性。

Ubuntu 24.04 Desktop 自带 GNOME 远程登录 RDP。先按默认桌面与 XWayland 客户端路径验证；若远程桌面兼容性或会话持续性不满足要求，再评估 Xorg + xrdp。不会把 GNOME 与 xrdp 同时抢占同一端口作为默认方案。

## 初始规格与部署边界

- 建议 4 vCPU、16 GiB 内存、200 GiB qcow2 磁盘上限；这是规划值。
- Git、VS Code、ChatGPT、Chrome、Python、Node.js 与 Docker/BuildKit 在 VM 中运行。
- 编译初期限制并行度 2–4，按实测再调整。完整 Collabora/LibreOffice 编译所需空间、内存和耗时单独评估。
- 独立 NAT 网段需避开现有 k3s、局域网、WireGuard 与代理虚拟网段；保留宿主机现有默认路由和物理网络配置。
- 经现有 SSH/WireGuard 通道访问 VM 的 RDP；初期使用 SSH 本地端口转发，不增加公开 RDP 入口。
- k3s 继续运行 Office 服务；开发桌面在 VM 中维护独立源码和构建缓存，通过镜像发布流程部署到 office-lab。
- VM 与 k3s 仍共享同一宿主机，CPU、内存、磁盘 I/O 配额及重负载编译需要控制；VM 不是独立物理故障域。

安装后的验收点：远程登录、断线重连与后台任务保持、ChatGPT 登录和持续联网、中文输入与剪贴板、浏览器预览、项目读写与构建、镜像导入测试 Namespace、宿主现有服务未受影响。账号登录与客户端实际能力需要在新桌面中实测。

## 官方依据

- ChatGPT Linux 客户端：https://learn.chatgpt.com/docs/linux/linux-app
- ChatGPT Windows 客户端：https://learn.chatgpt.com/docs/windows/windows-app
- Ubuntu 远程桌面：https://ubuntu.com/desktop/docs/en/24.04/how-to/share-your-desktop-remotely/
- Ubuntu libvirt：https://ubuntu.com/server/docs/how-to/virtualisation/libvirt/
- Windows RDP 服务端支持：https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/remotepc/remote-desktop-allow-access
