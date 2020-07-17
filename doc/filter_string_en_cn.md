# Write filter string in research

This doc will show how to write "filter string" to choose research projects.

本文档将阐述如何编写"过滤字符串"来选择科研项目.

## Select research series 选择科研期数

| Expression | Description       | 描述     |
| ---------- | ----------------- | -------- |
| S1         | research series 1 | 一期科研 |
| S2         | research series 2 | 二期科研 |
| S3         | research series 3 | 三期科研 |

## Select project type 选择科研类型

| Expression | Description                    | 描述       |
| ---------- | ------------------------------ | ---------- |
| B          | clear main chapter             | 打主线图   |
| C          | free research project          | 白嫖科研   |
| D          | face research                  | 定向科研   |
| E          | disassemble gear               | 装备分解   |
| G          | coins research                 | 金币科研   |
| H          | cube research                  | 魔方科研   |
| Q          | plate research                 | 部件分解   |
| T          | commission research            | 委托科研   |
| DR         | Azuma + Friedrich + Drake face | 彩科研定向 |
| PRY        | other ships face               | 其余定向   |
| Neptune    | Neptune                        | 海王星     |
| Monarch    | Monarch                        | 君主       |
| Ibuki      | Ibuki                          | 伊吹       |
| Izumo      | Izumo                          | 出云       |
| Roon       | Roon                           | 罗恩       |
| SaintLouis | Saint Louis                    | 路易九世   |
| Seattle    | Seattle                        | 西雅图     |
| Georgia    | Georgia                        | 佐治亚     |
| Kitakaze   | Kitakaze                       | 北风       |
| Azuma      | Azuma                          | 吾妻       |
| Friedrich  | Friedrich der Große            | 腓特烈大帝 |
| Gascogne   | Gascogne                       | 加斯科涅   |
| Champagne  | Champagne                      | 香槟       |
| Cheshire   | Cheshire                       | 柴郡       |
| Drake      | Drake                          | 德雷克     |
| Mainz      | Mainz                          | 美因茨     |
| Odin       | Odin                           | 奥丁       |

## Select research duration 选择科研耗时

Use the duration in hours, such as `0.5`, `6`, `12`.

使用按小时计算的时间, 比如 `0.5`, `6`, `12`.

## Create filter string 创建过滤字符串

Link the selection with dash `-` , such as `S3-DR-0.5`, `S3-Q-0.5`,  `Q-1`.

- Selections are all optional.
- You link without dash, such as `S3DR0.5` and `Q1`.
- You can use lowercase. It's not case sensitive.

Connect projects with greater than symbol `>` , such as

```
S3-DR-0.5 > Q-0.5 > S3-H-1 > S3-DR-2.5 > Q-1 > shortest
```

Alas will select research project from the left to the right. If no research matched, alas will do nothing. B (clear main chapter) and E (disassemble gear) will not be selected.

Some build-in strings:

- `shortest`, get the research project with the shortest duration. Equal to:

```
0.5 > 1 > 1.5 > 2 > 2.5 > 3 > 4 > 5 > 6 > 8 > 10 > 12
```

- `cheapest`, get the research project with the lowest cost. Equal to:

```
Q1 > Q2 > T3 > T4 > Q4 > C6 > T6 > C8 > C12 > G1.5 > D2.5 > G2.5 > D5 > Q0.5 > G4 > D8 > H1 > H2 > H0.5 > D0.5 > H4
```

- `reset`, example `x-xx > reset > x-xx`. Alas will refresh projects when selection reach there. If reset is already used today, do nothing.



使用横杠`-`连接选择, 比如 `S3-DR-0.5`, `S3-Q-0.5`,  `Q-1`.

- 所有的选择都不是必须的
- 可以不用横杠连接, 比如 `S3DR0.5` and `Q1`.
- 可以用小写, 大写小写都无所谓.

用大于号`>`连接科研项目, 比如

```
S3-DR-0.5 > Q-0.5 > S3-H-1 > S3-DR-2.5 > Q-1 > shortest
```

Alas 会从左到右地选择科研项目. 如果没有科研符合要求, 什么都不做. B (打主线图) 和 E (装备分解) 不会被选中.

一些内置的字符串:

- `shortest`, 选择时间最短的科研项目. 相当于:


```
0.5 > 1 > 1.5 > 2 > 2.5 > 3 > 4 > 5 > 6 > 8 > 10 > 12
```

- `cheapest`, 选择消耗最少的科研项目. 相当于:

```
Q1 > Q2 > T3 > T4 > Q4 > C6 > T6 > C8 > C12 > G1.5 > D2.5 > G2.5 > D5 > Q0.5 > G4 > D8 > H1 > H2 > H0.5 > D0.5 > H4
```

- `reset`, 举例 `x-xx > reset > x-xx`. 当查找到此处时, Alas 会刷新科研列表. 如果今天的刷新已经用过了, 什么都不做.

## Use your filter string in Alas 在Alas中使用过滤字符串

Open config/alas.ini , search `research_filter_string`, and paste filter string there, like this:

Choose "research_filter_prefix" to be "customized" in Alas GUI, and press "run" to save settings.

打开  config/alas.ini , 找到 `research_filter_string`, 并在那粘贴过滤字符串, 像这样:

在 Alas GUI 中把 "科研项目选择预设" 设置为 "自定义", 并点击 "运行" 保存设置.

```
research_filter_string = S3-DR-0.5 > S3-0.5 > Q0.5 > cheapest
```



## Some pre-written filter string 一些预制的过滤字符串

- `series_3_fastest` Do series 3 ASAP, whatever it costs. 快速完成三期科研, 不惜一切代价.

```
S3-DR-0.5 > S3-0.5 > S3-DR-2.5 > S3-H-1 > S3-H-4 > S3-H-2 > S3-DR-8 > S3-DR-5 > Q1 > Q2 > reset > shortest
```

- `series_3` Do series 3, need gears, use cubes and coins.

```
S3-DR-0.5 > S3-0.5 > Q0.5 > S3-DR-2.5 > S3-DR-8 > S3-DR-5 > S3-H-1 > S3-H-4 > S3-H-2 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > cheapest
```

- `series_3_than_2` Do series 3, also consider series 2, need gears, use cubes and coins. 做三期科研兼顾二期, 需要装备, 使用魔方和金币.

```
S3-DR-0.5 > S3-0.5 > S2-DR-0.5 > Q0.5 > S3-DR-2.5 > S3-DR-8 > S3-DR-5 > S3-H-1 > S3-H-4 > S3-H-2 > S2-DR-2.5 > S2-DR-8 > S2-DR-5 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > cheapest
```

- `free_research_only` Do free research only. 只做白嫖科研.

```
C12 > C8 > C6 > Q1 > Q2 > Q4 > T3 > T4 > T6 > reset > cheapest
```

- `cubes_to_chips` Consume cubes in exchange of chips, need gears. 切魔方换心智单元, 需要装备.

```
Q0.5 > H0.5 > H1 > H2 > H4 > Q1 > Q2 > Q4 > reset > G1.5 > G2.5 > cheapest
```

