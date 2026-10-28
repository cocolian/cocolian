# Mac 开发工作区

> 地址和目录均为通用示例，实际部署值应由自己的私有配置提供。


门户仓库：`<workspace>/cocolian`。引擎工作区：`<workspace>/cocolian-office`。两个工作区均由 GitHub 克隆。

- 门户、WOPI Host 与 UI 资源在 `apps/office-portal`。
- 最新引擎源码使用同级 `cocolian-office/src` 下锁定的仓库；历史 `upstream/` 快照依据 `docs/upstream-lock.json` 追溯，不重复提交源码。
- 构建镜像、Python 虚拟环境、缓存和凭据不提交。Linux 容器/引擎编译依赖另行准备；服务器构建产物保留在服务器。
- 部署脚本含历史服务器绝对路径；首次使用先核对目标与路径，不在 Mac 重跑 VM 安装脚本。
- 生产发布仍需按 AGENTS.md 授权。
