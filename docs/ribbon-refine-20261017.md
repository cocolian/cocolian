# Word 风格工具栏微调（2026-10-17）

本次仅调整桌面端标签栏的排版与视觉密度，保留图标标题、中文翻译及全部操作入口。默认门户配置仍为 compact，不强制切换用户视图。未缩放文档正文、侧边栏或系统弹窗。

## 调整

| 项目 | 调整结果 |
|---|---|
| 菜单标签 | 14px，选中菜单使用适度加粗 |
| 图标标题 | 12px，分组名称 11px |
| 普通图标 | 20px，按钮点击区域 26px |
| 工具栏内容区 | 从 82px 收紧到 76px |
| 字体、字号控件 | 12px 字体、26px 高度，浅色模式使用白色输入背景 |
| 样式预览 | 单行 96×60px 卡片，保留样式预览和中文名称；较长名称省略显示，悬浮提示保留 |
| 悬浮、选中状态 | 浅蓝边框、轻量背景与圆角；保留原有禁用状态和字体替代提示 |
| 窄屏 | 沿用原有工具组折叠、样式滚动和展开入口 |

样式限定在宽度至少 768px、精确指针设备的标签栏。compact 模式保持原排版。

## 源码和构建

开发机 `<workspace>/cocolian-office/src/online.mirror/browser/css/notebookbar.css` 保存实际修改；可移植补丁为 `patches/collabora/ribbon-refine.patch`，应用于已有中文补全版本之后。没有修改 LibreOffice 引擎代码。

`scripts/build-zh-cn.sh` 增加 `BUILD_ENGINE=0` 的前端增量构建选项；此选项要求当前引擎及中文资源已完成匹配版本的构建。此次复用已验证的 26.04.6.0 中文引擎，重新构建浏览器与服务端，并使用原 Runtime.Dockerfile 打包。

新资源版本：`42204b6034`。

发布镜像：

`registry.example.invalid/cocolian/collabora-source@sha256:e27d0b09078d23c2d8cb707aa3cda97e3488ede2a2bf97fa4fa1f594266b817d`

已先推送镜像仓库、确认 k3s 节点拉取，再更新 office-lab/collabora；保留 IfNotPresent。未直接修改 Pod 文件。

## 验证

- 样式、JavaScript 和构建检查通过。
- 独立测试文档中检查 1800、1440、1024 宽度；实测菜单 14px、普通图标 20px、工具栏内容区 76px，样式卡片均为 96px 宽。
- 遍历标签栏 10 个菜单，按钮标题、提示及无障碍名称未发现英文遗漏。
- 1024 宽度下，字体工具组会折叠；打开下拉菜单后确认加粗按钮可访问。
- compact 1440 宽度回归：普通图标仍为 24px，未应用标签栏卡片样式。
- 双独立编辑会话启动并保存成功；两人的输入标记均写入同一个测试 WOPI DOCX。
- 上述浏览器验证使用独立 loopback 服务和与发布内容相同的候选镜像，没有操作用户的生产浏览器或写入生产文档。
- k3s 更新成功，Collabora Pod 就绪且重启次数 0；集群内 capabilities、discovery 均为 HTTP 200，并返回新资源版本。
- DOCX 转 PDF HTTP 200，输出 24,725 字节，中文文本提取通过。
- 其余 11 个 Pod 的 UID、镜像、就绪状态和重启次数与发布前相同。

效果图及完整记录：Mac `work/ribbon-refine-20261017/`，开发机 `artifacts/ribbon-refine-20261017/`。

已打开的编辑器应关闭后重新进入，以加载新资源版本。标签栏模式下可见本次调整。

## 回滚

发布前镜像：

`registry.example.invalid/cocolian/collabora-source@sha256:ddbf23ae4bf55792be7a36f5b701f73cbec87566f56c26eb61f424bec90b346f`

开发机保留 Deployment 前后快照和带前置条件的正反向 JSON Patch。需要回滚时执行：

```sh
kubectl -n office-lab patch deployment collabora --type=json --patch-file <workspace>/cocolian-office/artifacts/ribbon-refine-20261017/rollback-patch.json
kubectl -n office-lab rollout status deployment/collabora --timeout=180s
```
