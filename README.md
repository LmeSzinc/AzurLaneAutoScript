**| [English](README_en.md) | 简体中文 | [Español](README_es.md)** |


# StarRailCopilot

Star Rail auto script | 星铁速溶茶，崩坏：星穹铁道脚本，基于下一代Alas框架。

![gui](https://raw.githubusercontent.com/LmeSzinc/StarRailCopilot/master/doc/README.assets/gui_cn.png)



## 功能

- **打本**：每日副本，双倍活动副本。
- **收获**：尽量完成每日任务，委托，无名勋礼。
- **后台托管**：自动启动模拟器和游戏，后台托管清体力和每日。



## 安装 [![](https://img.shields.io/github/downloads/LmeSzinc/StarRailCopilot/total?color=4e4c97)](https://github.com/LmeSzinc/StarRailCopilot/releases)

[中文安装教程](https://github.com/LmeSzinc/StarRailCopilot/wiki/Installation_cn)，包含自动安装教程，使用教程，手动安装教程。

> **为什么使用模拟器？** 如果你用桌面端来运行脚本的话，游戏窗口必须保持在前台，我猜你也不想运行脚本的时候不能动鼠标键盘像个傻宝一样坐在那吧，所以用模拟器。

> **模拟器的性能表现如何？** Lme 的 8700k+1080ti 使用 MuMu 12 模拟器画质设置非常高是有 40fps 的，如果你的配置稍微新一点的话，特效最高 60fps 不是问题。



## 开发

Discord https://discord.gg/aJkt3mKDEr QQ群 752620927

- [小地图识别原理](https://github.com/LmeSzinc/StarRailCopilot/wiki/MinimapTracking)
- 开发文档（目录在侧边栏）：[Alas wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start)，但很多内容是新写的，建议阅读源码和历史提交。
- 开发路线图：[#10](https://github.com/LmeSzinc/StarRailCopilot/issues/10) ，欢迎提交 PR，挑选你感兴趣的部分进行开发即可。

> **如何添加多语言/多服务器支持？** 需要适配 assets，参考 [开发文档 “添加一个 Button” 一节](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/4.1.-Detection-objects#%E6%B7%BB%E5%8A%A0%E4%B8%80%E4%B8%AA-button)。



## 关于 Alas

SRC 基于碧蓝航线脚本 [AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript) 开发，Alas 经过三年的发展现在已经达到一个高完成度，但也累积了不少屎山难以改动，我们希望在新项目上解决这些问题。

- 更新 OCR 库。Alas 在 cnocr==1.2.2 上训练了多个模型，但依赖的 [mxnet](https://github.com/apache/mxnet) 已经不怎么活跃了，机器学习发展迅速，新模型的速度和正确率都碾压旧模型。
- 配置文件 [pydantic](https://github.com/pydantic/pydantic) 化。自任务和调度器的概念加入后用户设置数量倍增，Alas 土制了一个代码生成器来完成配置文件的更新和访问，pydantic 将让这部分更加简洁。
- 更好的 Assets 管理。button_extract 帮助 Alas 轻易维护了 4000+ 模板图片，但它有严重的性能问题，对外服缺失 Assets 的提示也淹没在了大量垃圾 log 中。
- 减少对于碧蓝的耦合。Alas 框架和 Alas GUI 有对接其他游戏及其脚本的能力，但已经完成的明日方舟 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 插件和正在开发的 [fgo-py](https://github.com/hgjazhgj/FGO-py) 插件都发现了 Alas 与碧蓝航线游戏本身耦合严重的问题。

