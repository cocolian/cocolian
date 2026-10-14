# 中文与紧凑工具栏

配置文件：apps/office-portal/editor.json。

- language: zh-CN，通过编辑器启动 URL 的 lang 参数传入。线上 CODE 镜像含 ui-zh_CN.json 与 help-zh_CN.json。
- ui_mode: compact，通过官方 ui_defaults 表单参数 UIMode=compact 传入。
- use_saved_ui_state: false，通过 ui_defaults 中的 SavedUIState=false 传入，避免浏览器已保存的带状界面覆盖本次默认设置。

compact 是内置的经典紧凑工具栏，改为菜单加图标的布局，不是仅用 CSS 隐藏原带状工具栏标题。保留菜单文字、悬浮提示、字体与字号选择框；图标按钮不再采用上方图标、下方名称的带状排版。本轮无需修改或重编译 Collabora 引擎。仅修改本地 WOPI 启动集成，使其读取配置文件，再把 server.py 和 editor.json 一并打包到门户镜像。

配置依据：官方 SDK 示例 upstream/collabora-online-sdk-examples/webapp/html/index.html（compact/tabbed、ui_defaults）以及线上 /etc/coolwsd/coolwsd.xml（user_interface.mode: default/compact/tabbed）。

访问密码仍从 Kubernetes Secret 注入，不写入本地配置文件。

构建发布：scripts/build-oci.py 与 scripts/generate-deployment-patch.py。为避免重复传输基础镜像，可用 pack-image-delta.py 生成新增层，再由服务器上的 merge-image-delta.py 与原基础镜像归档合并。构建内容仍全部来自本地源码和配置。

回滚：scripts/rollback-toolbar.py 按 /var/lib/office-lab/backups/toolbar-20261014/wopi-before.json 中保存的 Deployment 修订号恢复原界面集成，保留更新后的密码 Secret。

官方 SDK 配置示例：https://github.com/CollaboraOnline/collabora-online-sdk-examples/blob/dc55f596ec9bad460a2aac46eafac658b945e9e7/webapp/html/index.html 。本项目按其中 UIMode=compact 与 SavedUIState=false 参数传入。
