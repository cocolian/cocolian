# GitHub 源码

| 目录 | 官方仓库 | 本次范围 |
|---|---|---|
| upstream/gotenberg | https://github.com/gotenberg/gotenberg | 浅克隆，完整当前文件 |
| upstream/collabora-online-sdk-examples | https://github.com/CollaboraOnline/collabora-online-sdk-examples | 浅克隆，完整当前文件 |
| upstream/collabora-online | https://github.com/CollaboraOnline/online | 浅克隆，当前构建发布与 Helm 文件 |
| upstream/collabora-engine | https://github.com/CollaboraOnline/online.mirror | 部分克隆，稀疏检出 browser；不包含完整 LibreOffice 引擎工作树 |

完整引擎构建需要另外下载引擎源文件、工具链及依赖，不能把当前门户容器打包记为 Collabora 或 LibreOffice 编译完成。当前引擎镜像保持原版本。
