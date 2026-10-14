# 本地源码与部署目录

- apps/office-portal：自有门户、WOPI Host、Dockerfile。
- upstream：GitHub 上游仓库；固定提交记录，不在此目录直接改动。
- deploy/k8s：部署清单与原版本备份。
- deploy/nginx：office.example.invalid 边缘代理配置。
- scripts：构建、访问和验证脚本。
- docs：架构、构建记录与操作说明。
- build：本地打包产物、源码归档，不存放访问密钥。
- outputs、work：保留历史验证材料，不覆盖。

本轮部署范围为门户/WOPI 容器。Collabora 与 LibreOffice/Gotenberg 引擎保持已有版本；完整引擎源码编译另行记录。
