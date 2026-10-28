# Cocolian Office 文档门户

本仓库提供 Cocolian Office 的文档门户与 WOPI Host 实现，负责文档打开、鉴权、编辑会话、保存回调以及转换服务接入。

Cocolian Office 的目标是构建国产化的 LibreOffice 和云文档中台，持续提升中文文档在在线编辑、预览和 PDF 转换中与 Microsoft Office Word 的渲染一致性。项目基于 LibreOffice 和 Collabora Online 开发，可按各组件许可证免费使用和接入。

## 代码结构

- [apps/office-portal](apps/office-portal)：门户页面、WOPI Host 与文档处理接口。
- [deploy](deploy)：部署配置示例，使用前按自己的环境调整。
- [scripts](scripts)：构建、验证和部署工具。
- [docs](docs)：开发与接口资料。

## 接入与部署

业务系统通过 WOPI 对接文档打开、编辑和保存；DOCX 转 PDF 通过转换服务接口集成。部署方需要自行配置文档存储、编辑器地址、身份认证、HTTPS、访问控制和字体。

对外文档应使用通用示例或环境变量说明配置，真实服务器地址、账号路径、网络拓扑、访问密钥、证书私钥及运维备份信息应保存在独立的私有配置中。

当前复杂文档的兼容性仍在持续改进。欢迎提供可公开的最小合成案例，协助定位字体、换行、表格和分页差异；请勿提交真实业务文档、私有字体或生成的 PDF。

## 项目与社区

- [公开渲染源码与项目介绍](https://github.com/cocolian/online.mirror)
- [项目介绍文章](https://github.com/cocolian/online.mirror/blob/main/cocolian/office-lab/docs/community/introduction-zh.md)
- [问题反馈与接入咨询](https://github.com/cocolian/online.mirror/issues)

欢迎接入本项目，欢迎贡献代码、测试和文档。欢迎捐款支持，可通过 GitHub Issue 联系项目维护者。

相关源码保留原有许可证和版权声明，使用、修改和分发时请遵守各组件许可。
