[English Quick Guide](doc%2FQuick_guide.md) 

[English Readme](README_en.md) `Translation in progress`
# AzurLaneAutoScript

Alas, an Azur Lane automation tool with GUI (Support CN and EN, can support other server).

Alas, 一个带GUI的碧蓝航线脚本 (支持国服和国际服, 可以支持其他服务器).

EN support, Thanks **[@whoamikyo](https://github.com/whoamikyo)**

![gui](doc/README.assets/gui.png)



## 功能 Features

- **主线图出击** 暂时仅支持前六章和7-2

- **活动图出击** 支持「穹顶下的圣咏曲」(event_20200521_cn), 针对D1D3有优化, 支持处理光之壁(舰队无法在有光之壁的格子进行通行), 支持开荒

- **每日任务** 半小时左右一套做完, 重复运行时会跳过当天做过的

  每日任务(不支持潜艇每日). 困难图(暂时仅支持10-4). 演习, 自动SL.

- **活动图每日三倍PT** 半小时左右A1到B3一套做完

- **委托收派** 出击时每20分钟切出去收获, 支持收委托, 收科研, 收任务, 派委托

- **特定模式出击** 7-2三战拣垃圾, 12图练级. ~~碧蓝航线不就只有两张图吗? 最多再算上1-1~~ (

- **其他小功能**

  心情控制, 计算心情防止红脸或者保持经验加成状态

  血量监控, 低血量撤退, 先锋血量平衡

  整队换装备

  掉落截图记录

  自动退役

  开荒模式



## 安装 Installation

- Clone 本项目

- 安装依赖, 最好使用虚拟环境

```
pip install -r requirements.txt
```

### 安装模拟器 Install an emulator

| 设备       | Device     | 模拟器版本 | 安卓版本 | adb截图 | u2截图 | adb点击 | u2点击 |
| ---------- | ---------- | ---------- | -------- | ------- | ------ | ------- | ------ |
| 逍遥模拟器 | NemuPlayer | 7.1.3      | 5.1.1    | 0.308   | 0.275  | 0.294   | 0.146  |
| 雷电模拟器 | LDPlayer   | 3.83       | 5.1.1    | 0.329   | 0.313  | 0.291   | 0.146  |
| 夜神模拟器 | NoxPlayer  | 6.6.0.0    | 5.1.1    | 0.339   | 0.313  | 0.505   | 0.141  |
| MuMu模拟器 | MuMuPlayer | 2.3.1.0    | 6.0.1    | 0.368   | 0.701  | 0.358   | 0.148  |
| 一加5      | Oneplus5   |            | 7.1.1    | 1.211   | 0.285  | 0.447   | 0.160  |

这里给出了一些常见模拟器的性能测试结果, 测试平台 Windows 10, I7-8700k, 1080ti, nvme SSD, 模拟器分辨率1280x720, 碧蓝航线 60帧开启, 进入地图 7-2, 执行100次取平均, 单位秒.

由于海图识别模块对截图质量有很高的要求, `AzurLaneAutoScript` 暂时不支持手机, 必须使用模拟器. (Alas其实是支持手机的, 远古版本的Alas也是在手机上测试的, 但是长时间运行会发热和假死, 就放弃了)

- 安装一款安卓模拟器
- 模拟器分辨率设置为 `1280x720` .

### 配置ADB Set up ADB

- 获取 [ADB](https://developer.android.com/studio/releases/platform-tools)

- 将ADB配置于系统的环境变量中, 并测试是否配置成功.

```
adb devices
```

### 调教国产模拟器 Dealing with chinese emulator

国产模拟器一般会使用自己的 ADB, 而不同的ADB之间会互相结束对方, 这里提供一个一劳永逸的方法: 直接替换.

- 前往模拟器的安装目录, 搜索 `adb`, 备份这些文件
- 将自己的 `adb.exe` 复制进安装目录, 并且把名字改成刚才备份的文件的名字.

比如说夜神模拟器的安装目录有 `adb.exe` 和 `nox_adb.exe` , 备份它们. 把自己的 `adb.exe` 复制两份进来, 其中一份改名为 `nox_adb.exe` .

这并不会影响模拟器运行, 还会带来方便. 每次打开模拟器的时候, 模拟器就会自动连接至ADB, 相当于执行了

```
adb connect <your emulator address>
```

### 安装 uiautomator2 Install uiautomator2

[uiautomator2](https://github.com/openatx/uiautomator2), 是一个自动化测试的库, 可以加快截图和点击的速度.  `AzurLaneAutoScript` 也可以使用ADB来执行截图和点击, 就是慢一点而已. 

出于性能优化, 建议使用ADB截图, uiautomator2点击. (u2截图稍稍快于adb截图, 但是cpu占用翻倍, u2点击则全方位碾压adb)

- 执行

```
python -m uiautomator2 init
```

  会在所有连接的设备上安装 [uiautomator-server](https://github.com/openatx/android-uiautomator-server/releases) , [atx-agent](https://github.com/openatx/atx-agent), [minicap](https://github.com/openstf/minicap), [minitouch](https://github.com/openstf/minitouch) . 如果设备是模拟器, uiautomator2 将跳过 minicap 的安装.

- 检查 uiautomator2 是否安装成功

  修改 `module.dev_tools` 下的 `emulator_test.py` 中的 `SERIAL`, 并执行.

  一些模拟器的默认 serial:

	| 设备       | Device     | serial          |
	| ---------- | ---------- | --------------- |
	| 夜神模拟器 | NoxPlayer  | 127.0.0.1:62001 |
	| MuMu模拟器 | MuMuPlayer | 127.0.0.1:7555  |
	| 逍遥模拟器 | NemuPlayer | 127.0.0.1:21503 |
	| 雷电模拟器 | LDPlayer   | emulator-5554   |



## 使用方法 Usage

- 编辑`alas.bat`, 并双击运行
- 创建快捷方式, 把目标修改为`<绝对路径至python虚拟环境> <绝对路径至alas.pyw>`, 把起始位置修改为 `<绝对路径至AzurLaneAutoScript的目录>`, 双击运行
- (不推荐) 通过命令行运行. 虽然alas使用了 [Gooey](https://github.com/chriskiehl/Gooey), 一个将命令行转为GUI的库, 但是Alas并不是先有命令行方法运行再用gooey的, Alas是为了使用gooey快速编写GUI而去拼凑命令行参数的. 因此使用命令行会很难受.
- (不推荐) 修改配置文件 `config/alas.ini` , 在 `alas.py` 中调用相关函数
- 多开运行, 复制 alas.pyw, 并重命名. 首次运行时会复制template.ini的设置. 脚本运行时会使用同名的ini配置文件.



## 已知问题 Known issue

按出现频率排列

- **GUI启动慢, uiautomator2启动慢**
- **无法处理网络波动** 重连弹窗, 跳小黄鸡
- **会显示绿脸黄脸红脸** 这个是瓜游心情值更新BUG, Alas会每隔2小时重启游戏来更新心情.
- **演习可能SL失败** 演习看的是屏幕上方的血槽, 血槽可能被立绘遮挡, 因此需要一定时间(默认1s)血量低于一定值(默认40%)才会触发SL.  一个血皮后排就有30%左右的血槽, 所以别以为在1s内被打掉40%是不可能的. 另外如果后排立绘过大且CD重叠严重, 建议增大确认时间(比如3s), 或者换皮肤, 这样可以减少误判.
- **极少数情况下ADB和uiautomator2会抽风**
- **拖动操作在极少数情况下无效**



## 文档 Doc

[海图识别 perspective](doc/perspective.md)

`海图识别` 是一个碧蓝航线脚本的核心. 如果只是单纯地使用 `模板匹配 (Template matching)` 来进行索敌, 就不可避免地会出现 BOSS被小怪堵住 的情况.  `AzurLaneAutoScript` 提供了一个更好的海图识别方法, 在 `module.map` 中, 你将可以得到完整的海域信息, 比如:

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

[参与开发 development](doc/development.md)

- 如何添加一个按钮 How to add a button
- 如何适配一张新的地图 How to adapt to a new map
- 如何支持其他服务器/语言 How to support other server/language



## 参考 Reference

- (Not open source) http://asaiq2.lofter.com/

  现成的碧蓝航线脚本, 完成度很高. 参考了主要的功能和设置.

- https://github.com/Egoistically/ALAuto

  (Archived) https://github.com/perryhuynh/azurlane-auto

  EN服的碧蓝航线脚本, 模仿了脚本架构.

