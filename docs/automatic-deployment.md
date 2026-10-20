# main 分支自动部署

build-host 约每分钟监测 main。cocolian/main 有任何新提交时，自动构建、推送并部署本项目对应的 wopi 门户；无需其他仓库同时更新。三个渲染/转换服务的镜像和 Pod 保持不变。

cocolian-office/main 或 online.mirror/main 更新时，对应更新 collabora、collabora-wordmac、libreoffice；多个项目同时更新时取模块并集。引擎直接跟随 online.mirror/main，不依赖 cocolian-office 更新子模块固定提交号。

部署范围为当前 office-lab。每次记录源码提交、选定模块、镜像摘要与验证结果；候选检查通过后串行更新，失败回滚。未变化的引擎源码允许复用编译缓存，但项目选定模块仍重新打包发布。

[完整流程及运维说明](https://github.com/cocolian/online.mirror/blob/main/cocolian/office-lab/scripts/devops/README.md)
