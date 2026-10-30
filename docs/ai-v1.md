# AI 第一版

门户采用右侧独立 AI 对话栏，默认 200px，可拖动左边界调至最多 600px，也可聚焦分隔线用左右方向键调整。关闭后编辑器恢复全宽，右上角 AI 按钮可重新打开。聊天记录独立滚动，输入框固定在底部；关闭保留当前会话与生成任务，刷新页面后会话重置。文档仍在左侧的原生编辑器中，不添加底部虚拟留白。适配器依赖当前自编译 Collabora 的同源 iframe，升级后须重跑验收。

未关联选区时调用 `/api/ai/chat`，支持最近 10 条消息的多轮对话；关联选区后调用 `/api/ai/edit` 生成修改建议。聊天记录只保存在当前页面内存，不写入浏览器持久存储。

先选中原文，点击“关联当前选区”，输入要求并生成建议。也可读取批注，选择批注以定位并使用批注文字作为要求，然后选取对应原文。批注锚点不自动等同于正文选区，必须由用户确认修改范围。

接受建议前重新读取当前选区，核对文档实例、选区变更序号、几何位置与原文。变化时拒绝写入。开启并确认原生修订状态后粘贴纯文本替换，保留 Word 插入/删除修订；在 Collabora 原生审阅菜单中继续接受或拒绝修订。“拒绝建议”不修改文档。原文内的局部格式可能随纯文本替换被重置，复杂表格和富文本建议按小段选择后核对。

## 服务端配置

在 wopi 容器环境中配置 `AI_BASE_URL`（含 `/v1`）、`AI_MODEL` 与 `AI_API_KEY`。API Key 通过 Kubernetes Secret 注入，禁止写入仓库或浏览器。私有 HTTP 模型网关需显式设置 `AI_ALLOW_HTTP=1`；默认要求 HTTPS，拒绝上游重定向。前端不提供任意模型地址覆盖。

`POST /api/ai/edit` 需要现有门户登录，校验同源、文件存在、正文大小与字段类型。共享实验室身份具有现有知识库权限；这不提供多租户隔离。最多同时处理四个模型请求，每次 60 秒超时。只返回建议，不在服务端改写文档。错误响应不回传上游异常正文。取消停止浏览器等待；已发给模型的请求可能继续执行至超时。

未配置时显示明确配置错误，不能视为真实模型联调通过。

## 验证

运行 `python3 -m unittest discover -s apps/office-portal -p 'test_*.py'`。浏览器验证脚本使用独立上传的合成文档，不改写用户已有文档；模型结果采用明确的测试替身，模型真实调用须另行配置验收。下载 DOCX 核对 `w:ins`、`w:del` 与修改正文。部署遵循现有 main 自动构建发布流程，保留 Secret、PVC 和其他三个渲染服务。

## MiniMax M3

选择 `AI_BASE_URL=https://api.minimax.io/v1` 与 `AI_MODEL=MiniMax-M3`，`AI_API_KEY` 引用服务器 Secret。代理为该模型启用 `reasoning_split=true`，只使用正文 `content`，不返回或写入 `reasoning_content`；使用 `max_completion_tokens=8192`，截断输出仍拒绝应用。

官方接口参考：https://platform.minimax.io/docs/api-reference/text-openai-api 。模型权限与计费由所用 MiniMax API Key 决定，配置完成后必须使用合成文本做真实请求验收。

服务器部署补丁：`deploy/k8s/wopi-ai-minimax.patch.json`。先在 office-lab 创建 `office-ai-minimax` Secret，字段为 `AI_API_KEY`，再应用补丁。补丁只包含引用，不包含密钥。

`python scripts/verify-ai-editor.py --real-model` 使用真实模型测试独立合成文档；默认仍使用模型测试替身。真实模式会产生少量模型调用费用。

当前部署使用中国区 `https://api.minimaxi.com/v1`，对应用户提供的中国区 API Key。国际区与中国区须使用各自匹配的凭据。`deploy/k8s/wopi-ai-egress.json` 仅向门户放行官方域名在部署时解析出的 IP 的 TCP 443；不移除现有隔离。MiniMax DNS 地址变动后需重新核对并更新 IP 白名单。
