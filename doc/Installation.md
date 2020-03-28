# 安装 Installation

- Clone 本项目

- 安装依赖, 最好使用虚拟环境

  ```
  pip install -r requirements.txt
  ```

### 安装模拟器 Install a emulator

| 设备       | Device     | 模拟器版本 | 安卓版本 | adb截图 | u2截图 | adb点击 | u2点击 |
|------------|------------|------------|----------|---------|--------|---------|--------|
| 逍遥模拟器 | NemuPlayer | 7.1.3      | 5.1.1    | 0.308   | 0.275  | 0.294   | 0.146  |
| 雷电模拟器 | LDPlayer   | 3.83       | 5.1.1    | 0.329   | 0.313  | 0.291   | 0.146  |
| 夜神模拟器 | NoxPlayer  | 6.6.0.0    | 5.1.1    | 0.339   | 0.313  | 0.505   | 0.141  |
| MuMu模拟器 | MuMuPlayer | 2.3.1.0    | 6.0.1    | 0.368   | 0.701  | 0.358   | 0.148  |
| 一加5      | Oneplus5   |            | 7.1.1    | 1.211   | 0.285  | 0.447   | 0.160  |

这里给出了一些常见模拟器的性能测试结果, 测试平台 Windows 10, I7-8700k, 1080ti, nvme SSD, 模拟器分辨率1280x720, 碧蓝航线 60帧开启, 进入地图 7-2, 执行100次取平均.

由于海图识别模块对截图质量有很高的要求, `AzueLaneAutoScript` 暂时不支持手机, 必须使用模拟器.

- 安装一款安卓模拟器
- 模拟器分辨率设置为 `1280x720` .

### 配置ADB Set up ADB

- 获取 [ADB](https://developer.android.com/studio/releases/platform-tools)

- 将ADB配置与系统的环境变量中, 并测试是否配置成功.

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

[uiautomator2](https://github.com/openatx/uiautomator2), 是一个自动化测试的库, 可以加快截图和点击的速度.  `AzueLaneAutoScript` 也可以使用ADB来执行截图和点击, 就是慢一点而已.

- 执行

  ```
  python -m uiautomator2 init
  ```

  会在所有连接的设备上安装 [uiautomator-server](https://github.com/openatx/android-uiautomator-server/releases) , [atx-agent](https://github.com/openatx/atx-agent), [minicap](https://github.com/openstf/minicap), [minitouch](https://github.com/openstf/minitouch) . 如果设备是模拟器, uiautomator2 将跳过 minicap 的安装.

- 检查 uiautomator2 是否安装成功

  修改 `module.dev_tools` 下的 `emulator_test.py` 中的 `SERIAL`, 并执行.

  一些模拟器的默认 serial:

	| 设备       | Device     | serial          |
	|------------|------------|-----------------|
	| 夜神模拟器 | NoxPlayer  | 127.0.0.1:62001 |
	| MuMu模拟器 | MuMuPlayer | 127.0.0.1:7555  |
	| 逍遥模拟器 | NemuPlayer | 127.0.0.1:21503 |
	| 雷电模拟器 | LDPlayer   | emulator-5554   |

## 使用方法 Usage

- 运行 `main.pyw` , 通过图形界面运行
- 修改配置文件 `config/main.ini` , 在 `main.py` 中调用相关函数

