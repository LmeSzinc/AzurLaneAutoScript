# 海图识别

`海图识别` 是一个碧蓝航线脚本的核心. 如果只是单纯地使用 `模板匹配 (Template matching)` 来进行索敌, 就不可避免地会出现 BOSS被小怪堵住 的情况.  `AzurLaneAutoScript` 提供了一个更好的海图识别方法, 在 `module.map` 中, 你将可以得到完整的海域信息, 比如:

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

module.map 主要由以下文件构成:

- perspective.py 透视解析
- grids.py 海域信息解析
- camera.py 镜头移动
- fleet.py 舰队移动
- map.py 索敌逻辑

## 一点透视

在理解 `AzurLaneAutoScript` 是如何进行海图识别之前, 需要快速了解一下 `一点透视` 的基本原理. 碧蓝航线的海图是一个一点透视的网格, 解析海图的透视, 需要计算出灭点和距点.

在一点透视中:

- 所有的水平线的透视仍为水平线.
- 所有的垂直线相交于一点, 称为 `灭点` . 灭点距离网格越远, 垂直线的透视越接近垂直.

![vanish_point](perspective.assets/vanish_point.png)

- 所有的对角线相交于一点, 称为 `距点` . 距点离灭点越远, 网格越扁长. 距点和灭点在同一水平线上. 距点其实有两个, 它们关于灭点对称, 图中画出的是位于灭点左边的距点.

![distant_point](perspective.assets/distant_point.png)

## 截图预处理

![preprocess](perspective.assets/preprocess.png)

拿到一张截图之后, `load_image` 函数会进行以下处理

- 裁切出用于可以用于识别的区域.
- 去色, 这里使用了 `Photoshop` 里的去色算法, (MAX(R, G, B) + MIN(R, G, B)) // 2
- 去UI, 这里使用 `overlay.png` .
- 反相

(上面的图是反相前的结果, 反相后的图过于恐怖, 就不放了)

## 网格识别

### 网格线识别

网格线, 是一条 20% 透明度的黑色线, 在 `720p` 下, 有3至4像素粗. 在旧UI时, 只需要把图像上下左右移动一个像素, 再除以原图像, 便可以得到网格线. 新UI的海图格子增加了白色框, 白色框有透明度渐变, 增加了识别难度.

`find_peaks` 函数使用了 `scipy.signal.find_peaks` 来寻找网格线. `scipy.signal.find_peaks` 可以寻找数据中的峰值点 : https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html

截取 height == 370 处图像, 使用以下参数:

```
FIND_PEAKS_PARAMETERS = {
    'height': (150, 255 - 40),
    'width': 2,
    'prominence': 10,
    'distance': 35,
}
```

![find_peaks](perspective.assets/find_peaks.png)

可以看出, 有一些被遮挡的没有识别出来, 还有很多识别错误, 不过问题不大. 

然后扫描每一行, 绘制出图像. (出于性能优化, 实际中会把图像展平至一维再识别, 这将缩短时间消耗至约 1/4.)

![peaks](perspective.assets/peaks.png)

至此, 我们得到了四幅图像, 分别对应 `垂直的网格内线` `水平的网格内线` `垂直的网格边线` `水平的网格边线` . 这一过程在 `I7-8700k` 上需要花费约 0.13 s, 整个海图识别流程将花费约 0.15 s.

注意, 识别内线和边线所使用的参数是不一样的. 不同的地图, 应该使用对应的参数, 如果偷懒的话, 也可以使用默认参数, 默认参数是针对 `7-2` 的, 可以在第七章中使用, 甚至可以用到 `北境序曲 D3` .

## 网格线拟合

`hough_lines` 函数使用了 `cv2.HoughLines` 来识别直线, 可以得到四组直线.

![hough_lines_1](perspective.assets/hough_lines_1.png)

以 `垂直的网格内线` 为例, 可以看到, 识别结果有一些歪的线.

我们在图片中间拉一条水平线, 称为 `MID_Y` (如果要修正水平线, 就拉垂直线), 交于垂直线, 交点称为 `mid` , 如果 `mid` 之间的距离小于3, 就认为这些线是相近线, 并用他们的平均值代表他们. 这样就修正了结果.

## 灭点拟合

我们知道, 在一点透视中所有垂直线相交于灭点, 但是网格识别的结果是有误差的, 不能直接求直线的交点.

`_vanish_point_value` 函数用于计算, 某一点到所有垂直线的距离, 并用 `scipy.optimize.brute` 暴力解出离直线组最近的点, 它就是 `灭点` . 这个曲面描绘了点到垂直线的距离和. 为了在求解是能大胆抛弃距离较远的线, 在求距离是加了 `log` 函数.

![vanish_point_distance](perspective.assets/vanish_point_distance.png)

得到灭点后, 还记得之前的 `mid` 吗, 将它们连接至灭点, 作为垂直线. 这是对结果的第二次修正.

## 距点拟合

将最初得到的垂直线和水平线相交, 得到交点. 我们知道距点和灭点在同一水平线上, 在这条水平线上取点, 将所有交点连接至这点, 得到斜线, `_distant_point_value` 函数将计算斜线的 `mid` 之间的距离, 同样使用 `scipy.optimize.brute` 暴力解出距离最小的点, 它就是  `距点` .

如果将斜线绘制出来, 会有这样的图像, 虽然有很多错误的斜线, 但确实求出了正确的距点.

![diatant_point_links](perspective.assets/diatant_point_links.png)

## 网格线清洗

经过以上步骤, 我们得到了以下网格线, 大体正确, 但是有错误.

![mid_cleanse_before](perspective.assets/mid_cleanse_before.png)

取垂直线的 `mid` , 

```
[ 185.63733413  315.65944444  441.62998244  446.89313842  573.6301653
  686.40881027  701.20376316  830.27394123  959.00511191 1087.91874026
 1220.58809477]
```

因为每个格子都是等宽的, 所以 `mid` 理论上是一个等差数列, 但实际识别结果可能有错误的项, 也可能有缺失的项. 我们用一次函数表达这个关系 `y = a * x + b`. 由于错误和缺失, 这里的 `x` 不一定是项数 `n` ,  但只要没有10个以上的错误或者缺失, 就会有 `x ∈ [n - 10, n + 10]` .

接下来, 把表达式改写为 `b = -x * a + y` , 其中 `x ∈ [n - 10, n + 10]` . 如果把`a`当作自变量, 把`b`当作因变量, 那么这是一组直线, 它有 11 * 21 条. 把它们描绘出来:

![mid_cleanse_lines_with_circle](perspective.assets/mid_cleanse_lines_with_circle.png)

可以发现, 用橙色圈起来的地方有多条直线重合, 我们称为 `重合点` (`coincident_point`). 那些错误的 `mid` 产生的直线无法与其他直线交于重合点, 自然被剔除.

使用 `scipy.optimize.brute` 暴力求解所有直线的最近点, 得到`重合点` 的坐标 

```
[-201.33197146  129.0958336]
```

因此一次函数就是 `y = 129.0958336 * x - 201.33197146` .

> 在计算点到直线的距离时, 使用了以下函数:
>
> ```
> distance = 1 / (1 + np.exp(9 / distance) / distance)
> ```
> 这个函数将削弱距离较远的直线的影响, 鼓励优化器选择局部最优解.
>
> ![mid_cleanse_function](perspective.assets/mid_cleanse_function.png)

>如何处理水平线?
>
>过`距点`作任意一条直线, 与水平线相交. 将得到的交点与`灭点`连接, 就完成了水平线到垂直线的映射. 处理完再映射回水平线即可.
>
>![mid_cleanse_convert](perspective.assets/mid_cleanse_convert.png)

最后, 以海图或者屏幕为边界生成 `mid` , 此时缺失的 `mid` 也得到了填充. 重新连接至灭点, 完成了垂直线的清洗.

绘制出网格识别的结果:

![mid_cleanse_after](perspective.assets/mid_cleanse_after-1584008112022.png)

# 网格裁切

事实上, 海域中的舰娘, 敌人, 问号等, 都是固定在网格中心的图片, 只不过这些图片会因为透视产生缩放而已. 注意, 仅仅是缩放, 图片不会因为透视产生变形, 产生变形的只有地面的红框和黄框.

![crop_basic](perspective.assets/crop_basic.png)

`grid_predictor.py` 中提供了 `get_relative_image` 函数, 它可以根据透视, 裁切出关于网格中心相对位置的图片, 统一缩放到特定大小, 这样就可以愉快地使用模板匹配了.

```
from PIL import Image
from module.config.config import cfg
i = Image.open(file)
grids = Grids(i, cfg)
out = Image.new('RGB', tuple((grids.shape + 1) * 105 - 5))
for loca, grid in grids.grids.items():
    image = grid.get_relative_image(
    	(-0.415 - 0.7, -0.62 - 0.7, -0.415, -0.62), output_shape=(100, 100))
    out.paste(image, tuple(np.array(loca) * 105))
out
```

![crop_scale](perspective.assets/crop_scale.png)

## 海域信息解析

未完待续