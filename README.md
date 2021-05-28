
[Check Wiki for installation guide](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki)

**| [English](README_en.md) | Chinese |**

# AzurLaneAutoScript
![GitHub LmeSzinc Releases](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total)

#### Discord
[![](https://img.shields.io/discord/720789890354249748?logo=discord)](https://discord.gg/AQN6GeJ)

### QQ群 1087735381

Alas, an Azur Lane automation tool with GUI (Support CN, EN, JP, TW, able to support other servers).

Alas, 一个带GUI的碧蓝航线脚本 (支持国服, 国际服, 日服, 台服, 可以支持其他服务器).

EN support, Thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, Thanks **[@ferina8-14](https://github.com/ferina8-14)** and **[@noname94](https://github.com/noname94)** , some features might not work.

TW support, Thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

> **Event Announcement 活动公告**
>
> [CN] 支持活动「镜位螺旋」.
>
> [EN] Support event "Mirror Involution".
>
> [JP] Support event 「照らす螺旋の鏡海」.

![gui](doc/README.assets/gui.png)



## 功能 Features

- **主线图出击** 针对复杂地图优化, 降低BOSS队被堵住而多打一战的可能性, 能处理伏击空袭

- **活动图出击** 支持在非周回模式下运行, 能处理移动距离限制, 光之壁, 传送门, 岸防炮, 地图解谜, 地图迷宫

- **每日任务** 半小时左右一套做完, 重复运行时会跳过当天做过的

  每日任务, 困难图, 演习(自动SL), 活动每日AB图+SP图, 共斗活动每天15把

- **委托收派** 出击时自动切出去收获, 支持收派委托, 收派科研, 收派战术学院, 收任务

- **特定模式出击** 7-2三战拣垃圾, 12图练级. 1-1刷好感, 打潜艇图.

- **大世界全自动** 一条龙完成: 接大世界每日, 买空港口商店, 做大世界每日, 短猫相接直到完成两次余烬信标.

  每月重置后清理所有危险海域.

- **其他小功能**

  心情控制, 计算心情防止红脸或者保持经验加成状态

  血量监控, 低血量撤退, 先锋血量平衡(自动更换承伤位和保护位)

  掉落截图记录, 掉率统计, 科研统计



## 安装 Installation

详见 [中文安装教程](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_cn)

包含傻瓜式安装教程, 傻瓜式更新教程和高级用户安装教程.



## 使用注意事项 Note

- 模拟器分辨率需要为 1280 x 720.
- 需要关闭`开发者选项-输入-指针位置(屏幕叠加层显示当前触摸数据)`, 因为这会遮挡模拟器内的游戏画面.
- 当修改完设置后, 需要点击 `开始` 来保存选项, 然后点击 `编辑` 返回主界面. 因为位于左侧的每一项功能都是分别保存和运行的.
- 当你的图打到一半的时候, 需要手动打完或者手动撤退, 再启动 Alas.



## 如何上报bug How to report

- 在提问题前, 请先阅读 [常见问题(FAQ)](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/FAQ_en_cn)
- 检查 Alas 的更新和最近的 commit. 确认使用的是最新版.
- 上传出错log. 在 `log/error` 目录下, 以毫秒时间戳为文件夹名, 包含 log.txt 和最近60张截图.



## 已知问题 Known issue

按出现频率排列

- **GUI启动慢, uiautomator2启动慢**

- **无法处理网络波动** 重连弹窗, 跳小黄鸡

- **在极低配电脑上运行可能会出现各种问题** 缓慢修复中

  极低配, 指截图耗时大于1s. 一般电脑耗时约0.5s, 高配耗时约0.3s, 高配+aScreenCap截图耗时小于0.15s.

- **会显示绿脸黄脸红脸** 这个是瓜游心情值更新BUG, Alas会每隔2小时重启游戏来更新心情.

- **演习可能SL失败** 演习看的是屏幕上方的血槽, 血槽可能被立绘遮挡, 因此需要一定时间(默认1s)血量低于一定值(默认40%)才会触发SL.  一个血皮后排就有30%左右的血槽, 所以别以为在1s内被打掉40%是不可能的. 另外如果后排立绘过大且CD重叠严重, 建议增大确认时间(比如3s), 或者换皮肤, 这样可以减少误判.

- **极少数情况下ADB和uiautomator2会抽风**

- **拖动操作在极少数情况下无效**



## 文档 Doc

[海图识别 perspective](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/perspective)

`海图识别` 是一个碧蓝航线脚本的核心. 如果只是单纯地使用 `模板匹配 (Template matching)` 来进行索敌, 就不可避免地会出现 BOSS被小怪堵住 的情况.  `AzurLaneAutoScript` 提供了一个更好的海图识别方法, 在 `module.map` 中, 你将可以得到完整的海域信息, 比如:

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

[参与开发 development](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/development)

- 如何添加一个按钮 How to add a button
- 如何适配一张新的地图 How to adapt to a new map
- 如何支持其他服务器/语言 How to support other server/language

更多文档, 请前往 [WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki).



## 参考 Reference

- [code:azure](https://asaiq.lofter.com/), 浅. (Not open source) 现成的碧蓝航线脚本, 完成度很高. 参考了主要的功能和设置.
- [ALAuto](https://github.com/Egoistically/ALAuto), Egoistically. EN服的碧蓝航线脚本, 模仿了脚本架构.
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta), asd111333. 引入了单应性变换至海图识别模块中.

