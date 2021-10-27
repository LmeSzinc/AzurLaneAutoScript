**| [English](README_en.md) | Chinese |**

# AzurLaneAutoScript

#### Discord [![](https://img.shields.io/discord/720789890354249748?logo=discord&logoColor=ffffff&color=4e4c97)](https://discord.gg/AQN6GeJ) QQ群  ![](https://img.shields.io/badge/QQ%20Group-1087735381-4e4c97)
Alas, an Azur Lane automation tool with GUI (Supports CN, EN, JP, TW, able to support other servers), designed for 24/7 running scenes, can take over almost all Azur Lane gameplay. Azur Lane, as a mobile game, has entered the late stage of its life cycle. During the period from now to the server down, please reduce the time spent on the Azur Lane and leave everything to Alas.

Alas，一个带GUI的碧蓝航线脚本（支持国服, 国际服, 日服, 台服, 可以支持其他服务器），为 7x24 运行的场景而设计，能接管近乎全部的碧蓝航线玩法。碧蓝航线，作为一个手游，已经进入了生命周期的晚期。从现在到关服的这段时间里，请减少花费在碧蓝航线上的时间，把一切都交给 Alas。

EN support, thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[@nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, thanks **[@ferina8-14](https://github.com/ferina8-14)**, **[@noname94](https://github.com/noname94)** and **[@railzy](https://github.com/railzy)**.

TW support, thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

GUI development, thanks **[@18870](https://github.com/18870)** , say HURRAY.

![](https://img.shields.io/github/commit-activity/m/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/tokei/lines/github/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/repo-size/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-pr-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97)

![gui](doc/README.assets/gui.png)



## 功能 Features

- **出击**：主线图，活动图，共斗活动，1-1 伏击刷好感，7-2 三战捡垃圾，12-2 中型练级，12-4 大型练级，紧急委托刷钻石。
- **收获**：委托，战术学院，科研，后宅，指挥喵，大舰队，收获，商店购买，开发船坞，每日抽卡，档案密钥。
- **每日**：每日任务，困难图，演习，潜艇图，活动每日AB图，活动每日SP图，共斗活动每日，作战档案。
- **大世界**：余烬信标，每月开荒，大世界每日，隐秘海域，短猫相接。

#### 突出特性：

- **心情控制**：计算心情防止红脸或者保持经验加成状态。
- **活动图开荒**：支持在非周回模式下运行，能处理移动距离限制，光之壁，传送门，岸防炮，地图解谜，地图迷宫等特殊机制。
- **无缝收菜**：时间管理大师，计算委托科研等的完成时间，完成后立即收获。
- **大世界**：一条龙完成，接大世界每日，买空港口商店，做大世界每日，短猫相接，购买明石商店，每30分钟清理隐秘海域。
- **大世界月初开荒**：大世界每月重置后，不需要购买作战记录仪（5000油道具）即可开荒。



## 安装 Installation [![](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total?color=4e4c97)](https://github.com/LmeSzinc/AzurLaneAutoScript/releases)

详见 [中文安装教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_cn)，包含自动安装教程，使用教程，手动安装教程，远程控制教程。



## 如何上报bug How to Report Bugs

在提问题之前至少花费 5 分钟来思考和准备，才会有人花费他的 5 分钟来帮助你。"XX怎么运行不了"，"XX卡住了"，这样的描述将不会得到回复。

- 在提问题前，请先阅读 [常见问题(FAQ)](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/FAQ_en_cn)。
- 检查 Alas 的更新和最近的 commit，确认使用的是最新版。
- 上传出错 log，在 `log/error` 目录下，以毫秒时间戳为文件夹名，包含 log.txt 和最近的截图。若不是错误而是非预期的行为，提供在 `log` 目录下当天的 log和至少一张游戏截图。



## 已知问题 Known Issues

- **无法处理网络波动**，重连弹窗，跳小黄鸡。
- **在极低配电脑上运行可能会出现各种问题**，极低配指截图耗时大于1s，一般电脑耗时约0.5s，高配耗时约0.3s。
- **演习可能SL失败**，演习看的是屏幕上方的血槽，血槽可能被立绘遮挡，因此需要一定时间（默认1s）血量低于一定值（默认40%）才会触发SL。一个血皮后排就有30%左右的血槽，所以有可能在 1s 内被打死。
- **逍遥模拟器不支持 minitouch 长按，无法进行后宅喂食**，建议不用逍遥模拟器。
- **极少数情况下 ADB 和 uiautomator2 会抽风**，是模拟器的问题，重启模拟器即可。
- **拖动操作在模拟器卡顿时，会被视为点击**



## 文档 Documents

[海图识别 perspective](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/perspective)

`海图识别` 是一个碧蓝航线脚本的核心，如果只是单纯地使用 `模板匹配 (Template matching)` 来进行索敌，就不可避免地会出现 BOSS被小怪堵住 的情况。 Alas 提供了一个更好的海图识别方法，在 `module.map_detection` 中，你将可以得到完整的海域信息，比如：

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

开发文档，请前往 [WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki)。



## 相关项目 Relative Repositories

- [AzurStats](https://azur-stats.lyoko.io/)，基于 Alas 实现的碧蓝航线掉落统计平台。
- [AzurLaneUncensored](https://github.com/LmeSzinc/AzurLaneUncensored)，与 Alas 对接的碧蓝航线反和谐。
- [ALAuto](https://github.com/Egoistically/ALAuto)，EN服的碧蓝航线脚本，已不再维护，Alas 模仿了其架构。
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta)，Alas 引入了其中的单应性变换至海图识别模块中。
- [PyWebIO](https://github.com/pywebio/PyWebIO)，Alas 使用的 GUI 库。

