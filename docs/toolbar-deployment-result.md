# 中文工具栏发布记录

配置：apps/office-portal/editor.json。

已从本地源码构建门户镜像并发布到 office-lab；Collabora 引擎未改代码或重新编译。中文使用 lang=zh-CN，紧凑布局使用 ui_defaults=UIMode=compact;SavedUIState=false。经典工具栏替换带状布局，保留菜单与字体字号选择框。

镜像摘要：sha256:877522cb9df4cfe3d6903f7584a1c37164f3e4ff8dcd0c40e7c662fc9319222e。

原部署备份：服务器 /var/lib/office-lab/backups/toolbar-20261014/wopi-before.json。回滚脚本 scripts/rollback-toolbar.py。

验证通过：中文菜单；30px 高的单行图标工具栏；保留字体字号选择；DOCX 转 PDF 返回 200。密码已按用户要求更新且没有写入本地源码、配置或文档；旧密码、Cookie、Bearer 均返回 401，新登录返回 303，新 Cookie/Bearer 访问转换健康端点返回 200。新凭据下实际编辑后通过 WOPI 保存，下载 DOCX 包含本轮测试标记。其他 9 个非 office-lab Pod 的 UID、镜像、就绪及重启次数未变化。

证据：outputs/toolbar-deployment-report.json、outputs/chinese-compact-toolbar.png。
