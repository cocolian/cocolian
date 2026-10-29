# Cocolian Office 国产化文档渲染与云文档中台

Cocolian Office 的目标是构建国产化的 LibreOffice，建设可自主构建、可私有部署的云文档中台，让中文文档在在线编辑、预览和 PDF 转换时，获得与 Microsoft Office Word 尽可能一致的渲染效果。

项目基于 LibreOffice 和 Collabora Online 持续开发，重点改进中文字体、行距、换行、分页、表格和中英文混排。我们追求最佳的中文文档与 Word 渲染一致性，并以对照文档和回归测试逐项推进。

**本项目开源，可按各组件许可证免费使用、部署和接入。欢迎贡献代码、接入业务系统，也欢迎捐款支持持续维护。**

## 项目能力与兼容性

- 通过浏览器在线编辑和协同，通过 WOPI 对接文档存储、鉴权和保存。
- 预览 DOCX 和转换 PDF，为业务应用提供文档处理能力。
- 持续修复中文字体、GB2312 和 GBK 字体匹配、段落行距、网格、表格跨页和混排规则。
- 从源码构建渲染引擎与在线服务，使用容器部署，并通过自动检查验证发布。

当前以 Mac 版 Microsoft Word 导出的 PDF 为主要对照，核对字体、文字位置、换行和分页。复杂文档仍可能存在布局差异，兼容性工作会持续推进。

## 开始使用与接入

```bash
git clone --filter=blob:none --branch main https://github.com/cocolian/online.mirror.git
cd online.mirror
```

- `engine/`：配套文档渲染引擎，承载主要中文排版修复。
- `browser/`、`wsd/`：在线编辑前端与服务端。
- [cocolian/office-lab](cocolian/office-lab/README.md)：项目集成、构建和部署资料。
- [office-portal](cocolian/office-lab/apps/office-portal)：文档门户与 WOPI Host 实现。
- [源码构建配方](cocolian/office-lab/deploy/source-build/)：源码构建及容器部署说明。

欢迎文档管理系统、知识库和业务平台接入。可以通过 WOPI 集成文档打开、编辑与保存，通过转换接口集成 DOCX 转 PDF。源码构建使用 Linux 环境；文档中的部署配置需按自己的环境调整。

第三方字体不随本仓库分发。部署时请提供有权使用的字体，并保持对照环境和服务端字体版本一致。

## 贡献与支持

欢迎贡献排版修复、合成测试、文档和系统集成。反馈渲染差异时，请说明字体、Word 版本、页面设置和复现步骤，优先提供可公开的最小合成案例。

真实业务文档、私有字体、生成的 PDF、构建产物和凭据应保存在仓库外。提交前请确认文件名和内容具备公开权限。

**欢迎捐款支持，可通过 [GitHub Issue](https://github.com/cocolian/online.mirror/issues) 联系项目维护者。** 捐款将支持中文排版兼容性开发、回归测试和构建资源；也欢迎提供算力、测试环境和集成反馈。捐款不影响按许可证免费使用开源代码。

## 项目介绍

- [项目介绍文章](cocolian/office-lab/docs/community/introduction-zh.md)
- [X 和其他媒体文案](cocolian/office-lab/docs/community/social-posts.md)

Cocolian Office is an open source cloud document platform based on LibreOffice and Collabora Online. We focus on Chinese document rendering, aiming for the closest possible fidelity to Microsoft Word across online editing, preview and PDF conversion. The project can be used and integrated free of charge under the applicable component licenses. Contributions, integrations and donations are welcome.

## 许可证与上游

感谢 LibreOffice、Collabora Online 及其社区。相关源码保留上游许可证与版权声明；使用、修改和分发时，请遵守 [COPYING](COPYING) 及各组件的许可文件。上游介绍和贡献流程如下。

## Collabora Online and Collabora Office 上游说明

> [!IMPORTANT]
> **The CollaboraOnline/online.mirror repository on GitHub is a read-only mirror.**
> Collabora Online and Collabora Office are developed on our Gerrit
> instance at **https://gerrit.collaboraoffice.com**; the GitHub repository only mirrors that
> source code.
>
> - **Code contributions** go through Gerrit, not GitHub. Pull requests are disabled here; see
>   [CONTRIBUTING.md](CONTRIBUTING.md#contributing-to-source-code) for how to submit a patch.
> - **Report issues** at the [CollaboraOnline/online issue tracker](https://github.com/CollaboraOnline/online/issues/new/choose).

[![Development: Gerrit](https://img.shields.io/badge/Development-Gerrit-orange?logo=git "Code development and review happen on Gerrit. GitHub pull requests are disabled.")](https://gerrit.collaboraoffice.com)
[![Collabora Office Development Preview](https://img.shields.io/badge/Collabora%20Office-Development%20Preview-blue "Test the latest development snaphots of Collabora Office.")](https://www.collaboraoffice.com/downloads/CODA-Hd7wwbJWxm/)


[![Matrix](https://img.shields.io/badge/Matrix-%23cool--dev-turquoise.svg)](https://matrix.to/#/#cool-dev:matrix.org)
[![Telegram](https://img.shields.io/badge/Telegram-Collabora%20Online-green.svg)](https://t.me/CollaboraOnline)
[![Forum](https://img.shields.io/badge/Forum-Discourse-blue.svg)](https://forum.collaboraonline.com/)
[![Website](https://img.shields.io/badge/Website-www.collaboraoffice.org-blueviolet.svg)](https://www.collaboraoffice.org/)
[![L10n](https://img.shields.io/badge/L10n-Weblate-lightgrey.svg)](https://hosted.weblate.org/projects/collabora-online/)


**Secure Document Collaboration. Controlled by You.**

![](https://www.collaboraonline.com/wp-content/uploads/2024/02/Website_COOL_2305_Home-1024x366.png)

## Learn more 💡
* [Collabora Online Development Edition (CODE)](https://www.collaboraonline.com/code/)
* [Collabora Online](https://www.collaboraonline.com/collabora-online/)
* [Collabora Office](https://www.collaboraonline.com/collabora-office/)
* [Collabora Office for iOS and Android](https://www.collaboraonline.com/collabora-office-android-ios/)
* For additional details, build instructions, downloads, and more, please visit [www.collaboraoffice.org](https://www.collaboraoffice.org/). You can also explore the [SDK Documentation](https://sdk.collaboraonline.com/).

## Key features
* View and edit text documents, spreadsheets, presentations & more
* Collaborative editing features
* Collabora Online works in any modern browser – no plugin needed
* [Integrate, extend and customise](https://www.collaboraonline.com/integrations/)
* Open Source – primarily under the [MPLv2](http://mozilla.org/MPL/2.0/) license. Some parts are under other open source licences, see e.g. [browser/LICENSE](https://github.com/CollaboraOnline/online/blob/main/browser/LICENSE).

## Get in touch 💬

* [📋 Forum](https://forum.collaboraonline.com/)
* [👥 Facebook](https://www.facebook.com/collaboraoffice/)
* [🅾 Instagram](https://www.instagram.com/collaboraoffice/)
* [🐣 𝕏(Twitter)](https://twitter.com/CollaboraOffice)
* [🦋 Bluesky](https://bsky.app/profile/collaboraonline.com)
* [🐘 Mastodon](https://mastodon.social/@CollaboraOffice)
* [💼 LinkedIn](https://www.linkedin.com/products/collaboraproductivity-collabora-online/)
* [🎥 YouTube](https://www.youtube.com/@CollaboraOnline)

## Integrating

To [integrate](https://sdk.collaboraonline.com/docs/why_integrate.html) Collabora Online into your own solution, you can see our [step-by-step tutorial](https://sdk.collaboraonline.com/docs/Step_by_step_tutorial.html), view the [available integrations](https://sdk.collaboraonline.com/docs/available_integrations.html), understand the [post message API](https://sdk.collaboraonline.com/docs/postmessage_api.html) used to customize and interact with Collabora Online, and a lot more.


### Test running with integration for developers

Set up Nextcloud or ownCloud on localhost and install the richdocuments app, or explore other integrations that can be used to test Collabora Online at https://www.collaboraonline.com/integrations/.

Good tutorials exist how to install ownCloud or Nextcloud, we don't repeat
them here. richdocuments is called Collabora Online in the respective app
stores / marketplaces / whatever.

When you have a running Nextcloud or ownCloud instance at
http://localhost/nextcloud or at http://localhost/owncloud
go to Collabora Online settings, and set the WOPI URL to
http://localhost:9980

Then in the build tree, edit the generated coolwsd.xml and set ssl setting to
false. You can run make run, and test coolwsd with the ownCloud or Nextcloud
integration.

Note: if SSL is enabled in either Online or the integration, both must
have SSL enabled. That is, you must access NC/OC using https:// as well
as configure the Collabora Online endpoint in NC/OC as https://localhost:9980.

## Find a partner

Do you want a ready-to-go or simplified solution? Find a trusted vendor from our [list of global partners](https://www.collaboraonline.com/partners/) who integrate and host Collabora Online.

## Developer assistance
Please ask your questions on any of the bridged Matrix/Telegram rooms
* Matrix: [#cool-dev:matrix.org](https://matrix.to/#/#cool-dev:matrix.org)
* Telegram: [CollaboraOnline](https://t.me/CollaboraOnline)

Join the conversation on our Discourse server at https://forum.collaboraonline.com/

Watch the tinderbox status (it should be green):

[![tinderbox status](https://cpci.cbg.collabora.co.uk:8080/buildStatus/icon?job=Tinderbox+for+online+main&subject=tinderbox)](https://cpci.cbg.collabora.co.uk:8080/view/Tinderbox/job/Tinderbox%20for%20online%20main/)

## Development bits

This project has several components:
* **engine/**
  * The document rendering engine
* **wsd/**
  * The Web Services Daemon - which accepts external connections
* **kit/**
  * The client which lives in its own chroot and renders documents
* **common/**
  * Shared code between these processes
* **browser/**
  * The client side JavaScript component
* **test/**
  * C++ based unit tests
* **cypress_test/**
  * JavaScript based integration tests

## Building for development

The engine (core) is built first, then online on top of it.

    cd engine
    ./autogen.sh --with-distro=CPLinux-LOKit-Dev
    make
    cd ..
    ./autogen.sh --enable-developer
    make

Then "make run" to start coolwsd. Both developer options are convenience
bundles; pass individual configure options to override a piece. To bootstrap
from scratch, see scripts/clone-online.sh.

See also README-gbuild.md for an ongoing merge of the two-step engine and online builds.

## Software Bill of Materials

Collabora Online generates SBOMs for the server, the browser client, the
engine and the container images. [SBOM.md](SBOM.md) describes how they are
generated, how to check them (`make sbom-check`, `make sbom-audit`,
`make sbom-freshness`), how to scan them for known vulnerabilities, and what
a clean scan does *not* tell you.

## Further recommended reading with build details

* **[Build Collabora Online](https://www.collaboraoffice.org/post/build-code/)**
* **[Build Collabora Office for iOS](https://www.collaboraoffice.org/post/build-code-ios/)**
* **[Build Collabora Office for Android](https://www.collaboraoffice.org/post/build-code-android/)**
* **[Build Collabora Office for Windows](https://www.collaboraoffice.org/post/build-co-windows/)**
* **[Build Collabora Office for macOS](https://www.collaboraoffice.org/post/build-co-mac/)**
* **[Build Collabora Office for Linux](https://www.collaboraoffice.org/post/build-co-linux/)**

## Admin Panel

You can access the admin panel by directly accessing the admin.html file
from browser directory.

Websocket connections to admin console can be made at path: /adminws/ on the
same url and port as coolwsd is running on. However, one needs a JWT token to
authenticate to the admin console websocket. This is stored as a cookie with
`Path: /adminws/` when user successfully authenticates when trying to access
/browser/dist/admin/admin\*html files (HTTP Basic authentication). Token
is expired after every half an hour, so websocket connection to admin console
must be established within this period.

It should also be possible to do various sorts of tasks such as killing
documents that are open for more than 10 hours etc. See protocol.txt for
various commands. Only tricky thing here is getting the JWT token which can
be obtained as described above.

## Protocol description

See **[protocol.txt](wsd/protocol.txt)** for a description of the protocol to be used over the
websocket.

## Architecture

Please refer to https://sdk.collaboraonline.com/docs/architecture.html

## Enjoy!
