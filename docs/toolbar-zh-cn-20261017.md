# 工具栏中文补全（2026-10-17）

## 范围与原因

保留恢复后的默认 compact 界面及原有图标标题；同时检查标签栏各菜单，不重新引入隐藏标题的 CSS 或标签栏默认配置。

构建此前只启用了 en-US 引擎资源，浏览器中文 UNO 命令字典为空。门户中的 `language=zh-CN` 只能选择已打包的语言，无法补出缺失的语言文件。因此需要补齐匹配版本的翻译源码并重新构建，单改门户配置无法完整解决。

此外修正浏览器 FontColor、InsertPageNumberField 命令查询遗漏 `text` 组件的问题，补齐“功能导览”“悬挂缩进”及侧边栏段落间距、行距、缩进标签的中文翻译。

## 源码与复现

开发机：build-host，工作区 `<workspace>/cocolian-office`。

- Collabora 源码：`src/online.mirror`，基线 `19b4efae7fb8e9eda4a6d88baa959c838d3eb8c3`。
- 官方翻译仓库：`https://gerrit.collaboraoffice.com/translations`，分支 `distro/collabora/co-26.04`，固定提交 `17fb3698d5e86169d44076f7a992c572f8f780f1`。
- 下载镜像：`https://github.com/LibreOffice/translations`，已核对同分支提交相同。
- 引擎构建语言：`en-US zh-CN`。
- 浏览器与翻译补丁分别保存在 `patches/collabora/zh-cn-toolbar.patch` 和 `patches/collabora/zh-cn-native-commands.patch`。
- `scripts/fetch-translations-zh-cn.sh` 获取固定翻译版本；按补丁应用到匹配源码后，由 `scripts/build-zh-cn.sh` 构建。
- 构建脚本从源码和补丁内容派生浏览器资源版本，避免静态资源沿用旧缓存路径。

镜像采用既有 `deploy/source-build/Runtime.Dockerfile` 打包，推送 registry.example.invalid 后按不可变摘要发布到 office-lab/collabora；不修改 Pod 内文件。

## 验证记录

已发布至 `office-lab/collabora`：

`registry.example.invalid/cocolian/collabora-source@sha256:ddbf23ae4bf55792be7a36f5b701f73cbec87566f56c26eb61f424bec90b346f`

- 新浏览器资源版本：`d8052c75b2`；引擎及服务版本保持 `26.04.6.0`。
- 使用独立测试 DOCX，在开发机 loopback 服务中检查 compact 工具栏、标签栏全部 10 个菜单、侧边栏。按钮标题、悬浮提示及无障碍标签的英文扫描结果为空，侧边栏新增中文标签检查通过，并人工查看两种布局截图。
- 两个独立浏览器会话 Alice/Bob 启动成功，两人编辑标记均成功保存到同一 WOPI DOCX；未对生产文档做写入测试。
- k3s Deployment 滚动结果成功，Pod `collabora-75b9bc98ff-glrkw` 就绪，重启次数 0。
- 从集群内检查 `/hosting/capabilities`、`/hosting/discovery` 均 HTTP 200，均包含新的资源版本。
- 既有转换服务回归：DOCX 转 PDF HTTP 200，生成 24,725 字节 PDF，文本提取包含中文内容。
- 其余 11 个 Pod（9 个其他 Namespace Pod，及门户、转换服务）的 UID、镜像、就绪、重启次数均与发布前一致。

默认门户配置仍为 `language=zh-CN`、`ui_mode=compact`、`use_saved_ui_state=false`。字体名称、文档内容和文档校对语言不属于工具栏标题翻译范围。

未自动操作用户当前生产浏览器会话；已打开的编辑页面应关闭后重新进入，以加载新的资源路径。上述浏览器验证使用与发布镜像相同源码的独立候选镜像，线上验证为服务健康与版本核对。

## 回滚与证据

此前镜像保留为 `registry.example.invalid/cocolian/collabora-source@sha256:e52c1ff4995d901f4ff62620f881aa6f4ecb64a5e108fac7f6fc5429497ba894`。

开发机 `artifacts/zh-cn-20261017/` 保存 Deployment 前后快照、正反向 JSON Patch、工具栏审计及截图、转换 PDF。Mac `work/zh-cn-20261017/` 保存发布前 Pod/Deployment 快照、文档备份、检查结果与截图。未修改 Secret、PVC、代理或其他 Namespace 配置。

需要回滚时，在开发机执行：

```sh
kubectl -n office-lab patch deployment collabora --type=json --patch-file <workspace>/cocolian-office/artifacts/zh-cn-20261017/rollback-patch.json
kubectl -n office-lab rollout status deployment/collabora --timeout=180s
```

