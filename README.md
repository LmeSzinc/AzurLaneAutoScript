**| [English](README_en.md) | 简体中文 | [日本語](README_jp.md) |**

# AzurLaneAutoScript

#### Discord [![](https://img.shields.io/discord/720789890354249748?logo=discord&logoColor=ffffff&color=4e4c97)](https://discord.gg/AQN6GeJ) QQ群  ![](https://img.shields.io/badge/QQ%20Group-1087735381-4e4c97)
Azur Lane bot with GUI (Supports CN, EN, JP, TW, able to support other servers), designed for 24/7 running scenes, can take over almost all Azur Lane gameplay. Azur Lane, as a mobile game, has entered the late stage of its life cycle. During the period from now to the server down, please reduce the time spent on the Azur Lane and leave everything to Alas.

Alas is a free open source software, link: https://github.com/LmeSzinc/AzurLaneAutoScript

Alas，一个带GUI的碧蓝航线脚本（支持国服, 国际服, 日服, 台服, 可以支持其他服务器），为 7x24 运行的场景而设计，能接管近乎全部的碧蓝航线玩法。碧蓝航线，作为一个手游，已经进入了生命周期的晚期。从现在到关服的这段时间里，请减少花费在碧蓝航线上的时间，把一切都交给 Alas。

Alas 是一款免费开源软件，地址：https://github.com/LmeSzinc/AzurLaneAutoScript

EN support, thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[@nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, thanks **[@ferina8-14](https://github.com/ferina8-14)**, **[@noname94](https://github.com/noname94)** and **[@railzy](https://github.com/railzy)**.

TW support, thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

GUI development, thanks **[@18870](https://github.com/18870)** , say HURRAY.

![](https://img.shields.io/github/commit-activity/m/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/tokei/lines/github/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/repo-size/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-pr-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97)

这里是一张GUI预览图：
![gui](https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/doc/README.assets/gui.png)



## 功能 Features

- **出击**：主线图，活动图，共斗活动，紧急委托刷钻石。
- **收获**：委托，战术学院，科研，后宅，指挥喵，大舰队，收获，商店购买，开发船坞，每日抽卡，档案密钥。
- **每日**：每日任务，困难图，演习，潜艇图，活动每日AB图，活动每日SP图，共斗活动每日，作战档案。
- **大世界**：余烬信标，每月开荒，大世界每日，隐秘海域，短猫相接，深渊海域，塞壬要塞。

#### 突出特性：

- **心情控制**：计算心情防止红脸或者保持经验加成状态。
- **活动图开荒**：支持在非周回模式下运行，能处理移动距离限制，光之壁，岸防炮，地图解谜，地图迷宫等特殊机制。
- **无缝收菜**：时间管理大师，计算委托科研等的完成时间，完成后立即收获。
- **大世界**：一条龙完成，接大世界每日，买空港口商店，做大世界每日，短猫相接，购买明石商店，每27分钟清理隐秘海域，清理深渊海域和塞壬要塞，~~计划作战模式是什么垃圾，感觉不如Alas......好用~~。
- **大世界月初开荒**：大世界每月重置后，不需要购买作战记录仪（5000油道具）即可开荒。



## 安装 Installation [![](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total?color=4e4c97)](https://github.com/LmeSzinc/AzurLaneAutoScript/releases)

[中文安装教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_cn)，包含自动安装教程，使用教程，手动安装教程，远程控制教程。

[设备支持文档](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Emulator_cn)，包含模拟器运行、云手机运行以及解锁各种骚方式运行。



## 正确地使用调度器

- **理解 *任务* 和 *调度器* 的概念**

  在 Alas 中每个任务都是独立运行的，被一个统一的调度器调度，任务执行完成后会自动设置这个任务的下一次运行时间。例如，*科研* 任务执行了一个 4 小时的科研，调度器就会把 *科研* 任务推迟 4 小时，以达到无缝收菜的目的。

- **理解 *自动心情控制* 机制**

  Alas 的心情控制以预防为主，不会等到出现红脸弹窗才去解决，这样可以保持心情值在 120 以上，贪到 20% 的经验。例如，当前心情值是 113，放置于后宅二楼（+50/h），未婚（+0/h），Alas 会等到 12 分钟之后，心情值回复到 120 以上再继续出击。而在这个等待的期间，Alas 也会穿插执行其他任务。

- **正确地使用调度器**

  调度器的 **错误使用方法是只开一两个** 任务，手动管理任务或开关 Alas，调度器的 **正确使用方法是启用全部** 你觉得可能有用的任务，让调度器自动调度，把模拟器和 Alas 都最小化到托盘，忘记碧蓝航线这个游戏。



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



## 如何上报bug How to Report Bugs

在提问题之前至少花费 5 分钟来思考和准备，才会有人花费他的 5 分钟来帮助你。"XX怎么运行不了"，"XX卡住了"，这样的描述将不会得到回复。

- 在提问题前，请先阅读 [常见问题(FAQ)](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/FAQ_en_cn)。
- 检查 Alas 的更新和最近的 commit，确认使用的是最新版。
- 上传出错 log，在 `log/error` 目录下，以毫秒时间戳为文件夹名，包含 log.txt 和最近的截图。若不是错误而是非预期的行为，提供在 `log` 目录下当天的 log和至少一张游戏截图。



## 已知问题 Known Issues

- **无法处理网络波动**，重连弹窗，跳小黄鸡。
- **在极低配电脑上运行可能会出现各种问题**，极低配指截图耗时大于1s，一般电脑耗时约0.5s，高配耗时约0.3s。
- **演习可能SL失败**，演习看的是屏幕上方的血槽，血槽可能被立绘遮挡，因此需要一定时间（默认1s）血量低于一定值（默认40%）才会触发SL。一个血皮后排就有30%左右的血槽，所以有可能在 1s 内被打死。
- **极少数情况下 ADB 和 uiautomator2 会抽风**，是模拟器的问题，重启模拟器即可。
- **拖动操作在模拟器卡顿时，会被视为点击**



## Alas 社区准则 Alas Community Guidelines

见 [#1416](https://github.com/LmeSzinc/AzurLaneAutoScript/issues/1416)。



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

更多文档，请前往 [WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki)。



## 参与开发 Join Development

Alas 仍在活跃开发中，我们会不定期发布未来的工作在 [Issues](https://github.com/LmeSzinc/AzurLaneAutoScript/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22) 上并标记为 `help wanted`，欢迎向 Alas 提交 [Pull Requests](https://github.com/LmeSzinc/AzurLaneAutoScript/pulls)，我们会认真阅读你的每一行代码的。

哦对，别忘了阅读 [开发文档](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start)。



## 相关项目 Relative Repositories

- [AzurStats](https://azur-stats.lyoko.io/)，基于 Alas 实现的碧蓝航线掉落统计平台。
- [AzurLaneUncensored](https://github.com/LmeSzinc/AzurLaneUncensored)，与 Alas 对接的碧蓝航线反和谐。
- [ALAuto](https://github.com/Egoistically/ALAuto)，EN服的碧蓝航线脚本，已不再维护，Alas 模仿了其架构。
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta)，Alas 引入了其中的单应性变换至海图识别模块中。
- [PyWebIO](https://github.com/pywebio/PyWebIO)，Alas 使用的 GUI 库。
- [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights)，明日方舟小助手，全日常一键长草，现已加入Alas豪华午餐 -> [MAA 插件使用教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/submodule_maa_cn)
- [FGO-py](https://github.com/hgjazhgj/FGO-py)，全自动免配置跨平台开箱即用的Fate/Grand Order助手.启动脚本,上床睡觉,养肝护发,满加成圣诞了解一下?
- [StarRailCopilot](https://github.com/LmeSzinc/StarRailCopilot)，星铁速溶茶，崩坏：星穹铁道脚本，基于下一代Alas框架。



## 联系我们 Contact Us

- Discord: [https://discord.gg/AQN6GeJ](https://discord.gg/AQN6GeJ)
- QQ 六群：[410355575](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=AzW2qRgtfAYCXJFFbzVjYUNxoUInYZOP&authKey=8tMiii5txWNZlmuRyxblLlN1jIvyPKbqeRBbHOIsiOayqhr5HvoEei3Y7n4p5TFI&noverify=0&group_code=410355575)
- QQ 一群：[1087735381](https://jq.qq.com/?_wv=1027&k=I4NSqX7g) （有开发意向请加一群，入群需要提供你的Github用户名）
- Bilibili 直播间：https://live.bilibili.com/22216705 ，偶尔直播写Alas，~~为了拯救Alas，Lme决定出道成为偶像~~






# Alas修改版，适用于云


## 相较于原版Alas


* 合并了一个奇怪的库


* 将GamePageUnknownError和RequestHumanTakeover写入重启，重启一次后再运行上次未完成的任务如果依旧报错则抛出错误并用OnePush通知(如果有设置OnePush的话)





## 相较于原版Alas
- 将`GamePageUnknownError`和`RequestHumanTakeover`写入重启，重启一次后再运行上次未完成的任务如果依旧报错则抛出错误并用OnePush通知(如果有设置OnePush的话)
- 将`优化设置`中的`放慢截图速度至 X 秒一张`和`战斗中放慢截图速度至 X 秒一张`的时间限制分别从`0.1 ~ 0.3`和`0.1 ~ 1.0`放宽至`0.1 ~ 2.0`和`0.1 ~ 5.0`
- 将`GameStuckError`中`无操作连续截图超过 1 分钟`放宽至`3 分钟`
- 修复了在云端时由于网络延迟所导致的换装备时卡住(目前还在测试)
- 修复了在云端时战术学院选择舰船时的bug(由于难以复现，目前还在观察测试)

仪表盘。

出现未知界面，直接重启。 



紧急委托前排可以选择更换为10级以上的驱逐舰。

困难图可使用紧急委托功能3油刷D3。

演习推迟功能，可以在演习更新次数前1小时再打，但在指定清空次数的时候一刷新次数就清空。

  ## 使用方法：

1，将alas库地址修改为本地址。

2，在以下位置修改配置文件。

![image](https://github.com/Zuosizhu/Alas-with-Dashboard/assets/60862861/5cabd341-d4bc-47c2-a7b2-fe2a7cd73e3b)

3，GG明确表明蓝叠模拟器很慢。加上目前水平太菜无法解决蓝叠时常出现的UI Automator2无法使用的问题。加上蓝叠不能导入文件夹+本人网速极慢。因此若出现问题，不作任何支持。


