# 编辑页固定标题栏及工具栏（2026-10-17）

修改 apps/office-portal/server.py 的 /edit 页面，保留 Collabora 内部文档滚动及现有工具栏样式。

## 原因和修改

此前编辑器 iframe 是默认的行内元素，尺寸为 100vw × 100vh。行内元素的基线留白会让外层页面比视口高，触摸板或鼠标滚动可将整个 iframe 上移。Mac 的滚动链及边界回弹还可能放大这一视觉现象。

独立测试中复现：900px 视口对应 904px 页面，外层 scrollY 可以达到 4，iframe 顶部变为 -4px。编辑器内部的标题栏和工具栏位置未改变，发生移动的是外层嵌入页面。

修正内容：

- html、body 使用 100% 视口尺寸，禁止外层溢出滚动和 overscroll。
- body 和编辑器 iframe 固定铺满视口；iframe 使用 display:block，去除行内基线留白。
- 隐藏只用于提交启动参数的表单。
- 增加字符集与 viewport 元数据。
- 不拦截文档的 wheel 事件，不改变文档内部滚动，不重排 Collabora 的标题栏和工具栏。

## 发布

先修改本地源码并同步开发机，在开发机打包、推送仓库、确认节点拉取后，仅更新 office-lab/wopi 的 wopi 容器。其镜像拉取策略设为 IfNotPresent；gateway 容器仍使用原镜像与 Never。未修改 Secret 或文档卷。

镜像：`registry.example.invalid/cocolian/office-portal@sha256:9d424bc92b2a0bf0831e5febf32d823ef89177ff87bb78690a7179b784e8eb5c`。

## 验证及边界

在开发机独立 loopback 服务中，以测试文档、Chrome 和自动化 wheel 事件分别验证 compact、tabbed：

- 修正前能复现额外 4px 外层滚动。
- 修正后页面高度等于视口高度，强制 scrollTo、文档向下滚动、滚到顶端及在工具栏上滚动，外层 scrollY 均为 0，iframe 顶部始终为 0。
- 标题栏、工具栏的坐标和高度始终不变。
- 文档内部视图从顶部滚动约 102px，再返回顶部，确认内容滚动未锁死。
- 两个独立会话启动、编辑和 WOPI 保存通过。
- 发布后登录 303，健康与编辑页 HTTP 200，编辑页含固定视口样式。
- DOCX 转 PDF 回归通过；其余 11 个 Pod 的 UID、镜像、就绪和重启次数不变。

没有自动操作用户的生产浏览器，也未模拟 Mac 原生弹性滚动。Mac 实体触摸板效果待用户关闭旧编辑页、重新进入后确认。

原始记录：Mac work/fixed-editor-20261017；开发机 <workspace>/cocolian-office/artifacts/fixed-editor-20261017。测试脚本 verify-scroll.py 保存于 Mac 工作记录中。

## 回滚

开发机保留带前置条件的反向 JSON Patch，恢复原门户镜像和拉取策略，保留文档及密钥：

```sh
kubectl -n office-lab patch deployment wopi --type=json --patch-file <workspace>/cocolian-office/artifacts/fixed-editor-20261017/rollback-patch.json
kubectl -n office-lab rollout status deployment/wopi --timeout=180s
```
