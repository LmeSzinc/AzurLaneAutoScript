# macOS 安装指南（Apple 芯片）

本指南为 macOS 上的 Alas 提供 Apple 芯片 OCR 运行适配。它使用仓库自带的游戏文字模型和 ONNX Runtime，不需要 Tesseract 或 MXNet。适配使用仓库内原有的 CN、日文、通用中文和繁体中文模型；ONNX 文件在本地生成，不需要单独下载模型。

## 前置条件

- macOS 13 或更新版本的 Apple 芯片 Mac，以及已按 Alas 常规流程配置好的仓库和 Python 环境。本补丁提供 OCR 适配，不包含基础环境的一键安装器。
- MuMu 模拟器 Pro 中已启动碧蓝航线。常规的 MuMu ADB 连接需要在 `config/alas.json` 中配置。
- Android platform-tools 已安装且 `adb` 在 `PATH` 中；也可以在启动时通过 `ADB` 指定可执行文件路径。
- OCR 适配针对 Python 3.10 验证。若 Alas 使用其他 Python，请用 `ALAS_PYTHON` 指定该环境的解释器。

## 安装 OCR 运行时

在仓库根目录运行：

```sh
PYTHON="${ALAS_PYTHON:-python3}"
"$PYTHON" -m pip install --no-deps --only-binary=:all: \
  --target deploy/macos/packages -r deploy/macos/requirements-ocr.txt
PYTHONPATH=deploy/macos/packages "$PYTHON" deploy/macos/convert_models.py
chmod +x deploy/macos/run_alas_mac.sh
```

ONNX Runtime 及 OCR 转换依赖安装在 `deploy/macos/packages/`，不会升级 Alas 环境已有的 NumPy、Pillow 或 ImageIO。`deploy/macos/constraints.txt` 列出了经验证的 GIF 解码版本；适配安装过程不重装这些基础依赖。

## 检查与启动

先执行离线检查：

```sh
./deploy/macos/run_alas_mac.sh --check
```

检查确认十组程序生成的文字、五套原始 OCR 模型、字符白名单和批处理隔离均可使用，并测试新进程加载以及地图 GIF 解码。检查不读取账号配置或连接模拟器。通过后启动 Alas：

```sh
./deploy/macos/run_alas_mac.sh
```

如果 Python 不在默认位置，可以这样启动：

```sh
ALAS_PYTHON="/path/to/alas/bin/python" ./deploy/macos/run_alas_mac.sh
```

启动器依次使用 `ALAS_PYTHON`、仓库 `.venv/bin/python`、`PATH` 中的 `python3`。在安装和启动时使用同一解释器。首次启动若尚无 `config/alas.json`，请在 GUI 中创建配置并设置模拟器序列号。

首次安装或更换 Python、ONNX Runtime、ImageIO、Pillow 版本后，请重新运行检查。`sitecustomize.py` 只在通过此启动脚本创建的进程中启用 OCR 替换；不要直接运行 `gui.py`。

## 重新生成模型

如果仓库 OCR 权重有更新，回到仓库根目录重新执行：

```sh
PYTHONPATH=deploy/macos/packages "$PYTHON" deploy/macos/convert_models.py
./deploy/macos/run_alas_mac.sh --check
```

加载模型时会核对转换模型中记录的原始权重摘要。ONNX 文件写入被 Git 忽略的 `deploy/macos/models/`，不要把本地生成文件加入提交。

若自检报告 `GIF decoder regression`，请在同一 Python 环境恢复兼容的图像解码依赖，然后再自检：

```sh
"$PYTHON" -m pip install -c deploy/macos/constraints.txt imageio pillow
./deploy/macos/run_alas_mac.sh --check
```

此适配使用 Alas 已提供的模拟器与输入方式；游戏内任务、地图、舰队、资源限制和调度行为仍由 Alas 原有配置控制。首次运行或更改游戏/模拟器设置后，请在 Alas 控制页检查任务配置和模拟器连接。

## 验证范围与维护

在 Apple 芯片 Mac、Python 3.10、MuMu Pro 1.4.11 上，CN 客户端 16-4 安全海域已自动通关一次，包括四场道中和 Boss，五场结算均为 S。此实测来自整理前的相同推理模块；本提交重新验证了新路径的转换与离线检查。Intel Mac、其他语言的实机任务和未通关地图的开荒流程尚未验证。

依赖和模型目录为本地生成物。不要提交账号配置、运行日志、完整游戏截图、虚拟环境、`packages/` 或 `models/`。离线样本为程序生成的普通文字，不含游戏账号信息。

更新仓库后继续使用本指南的启动器。macOS 环境应将部署配置中的 `InstallDependencies` 设为 `false`，防止通用依赖安装流程重新安装不兼容的 MXNet；其他自动更新设置按需保留。若收到模型摘要不匹配错误，重新转换并运行自检。
