# 按文档选择渲染配置

`WORD_MAC_DOCUMENT_IDS` 配置以逗号分隔的文档 ID。只有明确列出的文档会使用独立的 `collabora-wordmac` 服务，其余文档仍使用 `collabora`。

需要同时部署独立服务及网关 `/word-mac/` 代理。兼容服务必须设置 `net.service_root=/word-mac`，使 discovery、静态资源和 WebSocket 使用一致的前缀。关闭该环境变量即可让所有文档回到默认服务。

`RenderProfile.Dockerfile` 用于在已验证的门户镜像上增量打包两个 Python 源文件。完整构建仍使用原 `Dockerfile`。验证：`python3 -m unittest test_render_profile.py`。
