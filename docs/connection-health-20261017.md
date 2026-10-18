# 编辑连接状态指示器（2026-10-17）

标题栏右侧增加连接状态按钮，覆盖桌面的标签栏及 compact 视图。默认视图设置、文档卷及门户未修改。

## 展示与测量

默认展示状态和已测得的往返响应时间；尚未测得时显示“正在检测连接”，不使用 0ms 作为占位。悬浮或点击后显示最近 30 秒稳定性及独立的保存反馈。慢速时提示检查网络、VPN 或代理设置。

通过当前编辑 WebSocket 每 5 秒发送一次小型 `ping netprobe=<id>`，服务端回复对应编号。仅匹配当前未完成请求，忽略过期回复；不会新增另一条编辑连接。既有未携带探测编号的 ping 仍兼容。

这项指标包含 WebSocket 链路、服务端消息排队和浏览器回调调度，不等同于 ICMP ping、带宽、丢包率、文字显示或完整保存的端到端耗时。不会声称能识别用户是否使用代理。

初始阈值：150ms 以下正常、150～400ms 偏高、400ms 以上明显缓慢。使用最近三个样本做状态去抖；短暂波动不会直接改变已稳定的状态，恢复也经过连续观察。15 秒没有收到对应回复时显示“等待服务端响应”；实际连接关闭后显示中断状态，由原有重连机制恢复。后台页面暂停探测，原有文档闲置机制保留。

保存状态来自现有 SaveState 的修改、保存中、确认保存及失败反馈，不从响应时间推断。尚未得到保存确认、等待响应或断线时，提示保存状态待确认。初次打开需要约 15 秒采样才能形成稳定的连接等级。

## 实现

- browser/src/app/Socket.ts：探测、提前建立连接的启动路径、定时器清理、状态判定及按钮。
- wsd/ClientSession.cpp：给 ping 回复附加受长度限制的探测编号，保留旧协议兼容。
- browser/src/control/Control.SaveState.tsx：输出已有保存状态反馈。
- browser/css/notebookbar.css：标题栏指示器及详情面板样式。
- browser/po/ui-zh_CN.po：中文翻译。
- scripts/build-zh-cn.sh：构建时同步浏览器和 wsd 改动，并记录服务端补丁哈希。

未修改 LibreOffice 引擎。

## 发布与验证

镜像：`registry.example.invalid/cocolian/collabora-source@sha256:a0f684bc20b914cc6d019bf2eaf8a73447d53e821e46f647f30b7d592ceabf01`。

资源版本：`bda0a4080b`；服务版本仍为 26.04.6.0。

- TypeScript、ESLint、CSS 检查及编译通过。
- 独立 loopback 测试文档中，标签栏、compact 首次打开均自动出现按钮，真实探测约 2～3ms。
- 利用 Socket 自带延迟包装器，在发送和接收方向各增加 250ms，实测约 503ms；提示转为响应缓慢，移除延迟后恢复。
- 模拟短暂波动、持续慢速、恢复、无响应、过期回复，状态判断通过；实际关闭独立测试 WebSocket 后出现连接中断提示。
- 验证现有保存反馈钩子；另做两个独立会话编辑及 WOPI 实际保存回归。
- k3s Deployment 更新成功，capabilities、discovery 均 HTTP 200，资源版本匹配。
- DOCX 转 PDF HTTP 200，输出 24,725 字节；其余 11 个 Pod 的 UID、镜像、就绪状态和重启次数与发布前相同。

浏览器验证使用独立测试服务与候选镜像，未操作用户的生产浏览器或写入生产文档。已打开的编辑页面需要关闭后重新进入，才能加载新资源。

开发机 artifacts/net-status-20261017/ 保存截图、原始测试结果、Deployment 前后快照和回滚 Patch；Mac work/net-status-20261017/ 保存本轮记录。

回滚镜像为 `registry.example.invalid/cocolian/collabora-source@sha256:e27d0b09078d23c2d8cb707aa3cda97e3488ede2a2bf97fa4fa1f594266b817d`。需要回滚时在开发机执行：

```sh
kubectl -n office-lab patch deployment collabora --type=json --patch-file <workspace>/cocolian-office/artifacts/net-status-20261017/rollback-patch.json
kubectl -n office-lab rollout status deployment/collabora --timeout=180s
```
