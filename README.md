**| [English](README_en.md) | 简体中文 |**


# StarRailCopilot

Star Rail auto script | 星铁副驾驶，崩坏：星穹铁道脚本，基于下一代Alas框架。

## 安装

### 获取源码

SRC 还在开发中，暂时不提供自动安装包，需要以正常流程安装。

Clone 这个项目。

```bash
git clone https://github.com/LmeSzinc/StarRailCopilot
```

进入项目目录。

```bash
cd StarRailCopilot
```

使用 conda 新建 python 3.10.10 环境，假设新环境的名字叫 `src`。

> 注意：我们不维护更高或者更低版本的依赖，建议使用 3.10.10

```bash
conda create -n src python==3.10.10
```

激活刚刚创建的虚拟环境。

```bash
conda activate src
```

安装 requirements.txt 中的依赖。

```bash
pip install -r requirements.txt
```

### 安装模拟器

1. 下载 [ADB](https://developer.android.com/tools/releases/platform-tools) 并配置到环境变量中。
1. 在模拟器里安装游戏，而不是桌面端，建议使用最牛批的 MuMu 12，次选蓝叠模拟器。

> **为什么使用模拟器？** 如果你用桌面端来运行脚本的话，游戏窗口必须保持在前台，我猜你也不想运行脚本的时候不能动鼠标键盘像个傻宝一样坐在那吧，所以用模拟器。

> **模拟器的性能表现如何？** Lme 的 8700k+1080ti 使用 MuMu 12 模拟器画质设置非常高是有 40fps 的，如果你的配置稍微新一点的话，特效最高 60fps 不是问题。

## 使用

还是在刚才的虚拟环境中，启动 GUI 后端（默认开在 22367 端口）。

```bash
python gui.py
```

在浏览器访问 `127.0.0.1:22367`

在 `SRC设置` - `模拟器设置` - `模拟器Serial` 中按照帮助文本填写。

进入 `总览` 界面，点击 `启动` 按钮。（SRC 将自动启动模拟器和游戏，如果它们没在运行的话，模拟器启动目前只支持 MuMu 系和夜神系模拟器）

保持脚本运行，SRC 将在体力恢复的时候自动登录清体力。建议将 `SRC设置` - `优化设置` - `当任务队列清空后` 设置为 `关闭游戏` 以节省资源。

## 开发

Discord https://discord.gg/aJkt3mKDEr QQ群 752620927

- 开发文档（目录在侧边栏）：[Alas wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start)，但很多内容是新写的，建议阅读源码和历史提交。

- 开发路线图：[#10](https://github.com/LmeSzinc/StarRailCopilot/issues/10) ，欢迎提交 PR，挑选你感兴趣的部分进行开发即可。

> **如何添加多语言/多服务器支持？** 需要适配 assets，参考 [开发文档 “添加一个 Button” 一节](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/4.1.-Detection-objects#%E6%B7%BB%E5%8A%A0%E4%B8%80%E4%B8%AA-button)。



## 关于 Alas

SRC 基于碧蓝航线脚本 [AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript) 开发，Alas 经过三年的发展现在已经达到一个高完成度，但也累积了不少屎山难以改动，我们希望在新项目上解决这些问题。

- 更新 OCR 库。Alas 在 cnocr==1.2.2 上训练了多个模型，但依赖的 [mxnet](https://github.com/apache/mxnet) 已经不怎么活跃了，机器学习发展迅速，新模型的速度和正确率都碾压旧模型。
- 配置文件 [pydantic](https://github.com/pydantic/pydantic) 化。自任务和调度器的概念加入后用户设置数量倍增，Alas 土制了一个代码生成器来完成配置文件的更新和访问，pydantic 将让这部分更加简洁。
- 更好的 Assets 管理。button_extract 帮助 Alas 轻易维护了 4000+ 模板图片，但它有严重的性能问题，对外服缺失 Assets 的提示也淹没在了大量垃圾 log 中。
- 减少对于碧蓝的耦合。Alas 框架和 Alas GUI 有对接其他游戏及其脚本的能力，但已经完成的明日方舟 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 插件和正在开发的 [fgo-py](https://github.com/hgjazhgj/FGO-py) 插件都发现了 Alas 与碧蓝航线游戏本身耦合严重的问题。

