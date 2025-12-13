#!/bin/bash

# 将终端窗口最小化
osascript -e 'tell application "Terminal" to set miniaturized of front window to true'

# 初始化 Conda
eval "$(conda shell.bash hook)"

# 激活 alas 环境
conda activate alas

# 切换到 alas 目录
cd AzurLaneAutoScript

# 删除三天前的日志文件
find log -type f -mtime +3 -delete

# 延迟1秒自动访问http://127.0.0.1:22267
(sleep 1 && open http://127.0.0.1:22267) &

# 运行 gui.py
python gui.py