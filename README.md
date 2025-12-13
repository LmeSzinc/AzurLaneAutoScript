**| [English](README_en.md) | 简体中文 | [日本語](README_jp.md) |**

# !!!私库使用须知!!!
- **使用私库时出现任何问题请自行解决**
请勿在源库issue提出私库使用相关的问题，源库作者没有义务维护私库功能
- **使用私库时请常备一个源库**

# 私库功能

添加了源库Pr的仪表盘，感谢 **[@Air111](https://github.com/Air111)** **[@guoh064](https://github.com/guoh064)**

![gui](https://raw.githubusercontent.com/baizi826/AzurLaneAutoScript/refs/heads/master/doc/README.assets/gui-Dashboard.png)

添加了源库Pr的紧急委托装备码，感谢 **[@guoh064](https://github.com/guoh064)**

![gui](https://raw.githubusercontent.com/baizi826/AzurLaneAutoScript/refs/heads/master/doc/README.assets/gui-GearCode.png)

开启了github actions，现在它会在北京时间凌晨2点，上午10点，下午6点尝试拉取源库更新，也可以手动运行

![gui](https://raw.githubusercontent.com/baizi826/AzurLaneAutoScript/refs/heads/master/doc/README.assets/sync-upstream.png)

# AzurLaneAutoScript

#### Discord [![](https://img.shields.io/discord/720789890354249748?logo=discord&logoColor=ffffff&color=4e4c97)](https://discord.gg/AQN6GeJ) QQ群  ![](https://img.shields.io/badge/QQ%20Group-1087735381-4e4c97)

Alas，一个带GUI的碧蓝航线脚本（支持国服, 国际服, 日服, 台服, 可以支持其他服务器），为 7x24 运行的场景而设计，能接管近乎全部的碧蓝航线玩法。碧蓝航线，作为一个手游，已经进入了生命周期的晚期。从现在到关服的这段时间里，请减少花费在碧蓝航线上的时间，把一切都交给 Alas。

Alas 是一款免费开源软件，地址：https://github.com/LmeSzinc/AzurLaneAutoScript

EN support, thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[@nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, thanks **[@ferina8-14](https://github.com/ferina8-14)**, **[@noname94](https://github.com/noname94)** and **[@railzy](https://github.com/railzy)**.

TW support, thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

GUI development, thanks **[@18870](https://github.com/18870)** , say HURRAY.

![](https://img.shields.io/github/commit-activity/m/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/tokei/lines/github/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/repo-size/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-pr-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97)

这里是一张GUI预览图：
![gui](https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/doc/README.assets/gui.png)


## 安装 Installation [![](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total?color=4e4c97)](https://github.com/LmeSzinc/AzurLaneAutoScript/releases)

[中文安装教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_cn)，包含自动安装教程，使用教程，手动安装教程，远程控制教程。

[设备支持文档](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Emulator_cn)，包含模拟器运行、云手机运行以及解锁各种骚方式运行。

[mac安装教程](https://github.com/Dreamry2C/MAC-arm-conda-alas)，本仓库已包含该教程所示environment.yml文件，感谢 **[@Dreamry2C](https://github.com/Dreamry2C)**

## 修改游戏设置

对照这个表格修改游戏内的设置，~~正常玩过游戏的都这么设置~~。

> 对着改的意思是，这是统一的标准，照着给定的内容执行，不要问为什么，不允许有不一样的。

主界面 => 右下角：设置 => 左侧边栏：选项

| 设置名称                            | 值   |
| ----------------------------------- | ---- |
| 帧数设置                            | 60帧 |
| 大型作战设置 - 减少TB引导           | 开   |
| 大型作战设置 - 自律时自动提交道具   | 开   |
| 大型作战设置 - 安全海域默认开启自律 | 关   |
| 剧情自动播放                        | 开启 |
| 剧情自动播放速度调整                | 特快 |
| 待机模式设置 - 启用待机模式         | 关    |
| 其他设置 - 重复角色获得提示         | 关   |
| 其他设置 - 快速更换二次确认界面     | 关   |
| 其他设置 - 展示结算角色             | 关   |

大世界 => 右上角：雷达 => 指令模块(order)：潜艇支援：
| 设置名称                                                 | 值               |
| -------------------------------------------------------- | ---------------- |
| X 消耗时潜艇出击  |取消勾选|

主界面 => 右下角：建造 => 左侧边栏： 退役 => 左侧齿轮图标：一键退役设置：

| 设置名称                                                 | 值               |
| -------------------------------------------------------- | ---------------- |
| 选择优先级1                                              | R                |
| 选择优先级2                                              | SR               |
| 选择优先级3                                              | N                |
| 「拥有」满星的同名舰船时，保留几艘符合退役条件的同名舰船 | 不保留           |
| 「没有」满星的同名舰船时，保留几艘符合退役条件的同名舰船 | 满星所需或不保留 |

将角色设备的装备外观移除，以免影响图像识别

更多文档，请前往 [WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki)。

## 相关项目 Relative Repositories

- [AzurStats](https://azur-stats.lyoko.io/)，基于 Alas 实现的碧蓝航线掉落统计平台。
- [AzurLaneUncensored](https://github.com/LmeSzinc/AzurLaneUncensored)，与 Alas 对接的碧蓝航线反和谐。
- [ALAuto](https://github.com/Egoistically/ALAuto)，EN服的碧蓝航线脚本，已不再维护，Alas 模仿了其架构。
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta)，Alas 引入了其中的单应性变换至海图识别模块中。
- [PyWebIO](https://github.com/pywebio/PyWebIO)，Alas 使用的 GUI 库。
- [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)，明日方舟小助手，全日常一键长草，现已加入Alas豪华午餐 -> [MAA 插件使用教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/submodule_maa_cn)
- [FGO-py](https://github.com/hgjazhgj/FGO-py)，全自动免配置跨平台开箱即用的Fate/Grand Order助手.启动脚本,上床睡觉,养肝护发,满加成圣诞了解一下?
- [StarRailCopilot](https://github.com/LmeSzinc/StarRailCopilot)，星铁速溶茶，崩坏：星穹铁道脚本，基于下一代Alas框架。
