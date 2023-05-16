# StarRailCopilot

Star Rail auto script / bot | 星铁副驾驶，崩坏：星穹铁道脚本，基于下一代Alas框架

## 安装

SRC 还在开发中，暂时不提供自动安装包，需要以正常流程安装。

Clone 这个项目。

```bash
git clone https://github.com/LmeSzinc/StarRailCopilot
```

进入项目目录。

```bash
cd StarRailCopilot
```

使用 conda 新建 python 3.11.2 环境，假设新环境的名字叫 `src`。

> 注意：我们不维护更高或者更低版本的依赖，建议使用 3.11.2

```bash
conda create -n src python==3.11.2
```

安装 requirements.txt 中的依赖。

```bash
pip install -r requirements.txt
```



## 使用

阿巴阿巴，没写完怎么用（



## 关于 Alas

SRC 将基于碧蓝航线脚本 [AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript) 开发，Alas 经过三年的发展现在已经达到一个高完成度，但也累积了不少屎山难以改动，我们希望在新项目上解决这些问题：

- 更新 OCR 库。Alas 在 cnocr==1.2.2 上训练了多个模型，但依赖的 [mxnet](https://github.com/apache/mxnet) 已经不怎么活跃了，机器学习发展迅速，新模型的速度和正确率都碾压旧模型。
- 配置文件 [pydantic](https://github.com/pydantic/pydantic) 化。自任务和调度器的概念加入后用户设置数量倍增，Alas 土制了一个代码生成器来完成配置文件的更新和访问，pydantic 将让这部分更加简洁。
- 更好的 Assets 管理。button_extract 帮助 Alas 轻易维护了 4000+ 模板图片，但它有严重的性能问题，对外服缺失 Assets 的提示也淹没在了大量垃圾 log 中。
- 减少对于碧蓝的耦合。Alas 框架和 Alas GUI 有对接其他游戏及其脚本的能力，但已经完成的明日方舟 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 插件和正在开发的 [fgo-py](https://github.com/hgjazhgj/FGO-py) 插件都发现了 Alas 与碧蓝航线游戏本身耦合严重的问题。

