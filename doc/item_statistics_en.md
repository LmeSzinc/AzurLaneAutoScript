# How to do statistics on item drop rate


> **DEPRECATED**
>
> This document uses cnocr==1.0.0, need old versions of Alas to run it.


This document will show how to use `dev_tools/item_statistics.py`

## Enable statistics in alas

In alas GUI, 

- set `enable_drop_screenshot` to `yes`, if enabled, alas will add a 1s sleep before screenshot, to avoid capture the flash. There's a flash light when item shows up.
- set `drop_screenshot_folder` to be the folder you want to save. It is recommended to save it in SSD.

After few hours or few days of running, you will get a folder structure like:

```
<your_folder>
    campaign_7_2
        get_items
            158323xxxxxxx.png
            158323xxxxxxx.png
            158323xxxxxxx.png
        get_mission
        get_ship
        mystery
        status
    campaign_10_4_HARD
        get_items
        get_mission
        get_ship
        status
    d3
        get_items
        get_mission
        get_ship
        status
```

Screenshot are named after millesecond timestamp.

## Prepare a new environment

- Prepare another virtual environment, accoring to `requirements.txt`. But use the GPU version of `mxnet`.

   I am using GTX1080Ti, and I installed `mxnet-cu80==1.4.1`, `CUDA8.0`, `cuDNN`. Google  `mxnet gpu install`, and see how to do in details. You may intall other version of CUDA, and mxnet for that CUDA, because you are using another graphic card.

- Look for the cnocr in your virtual environment. Replace site-packages\cnocr\cn_ocr.py line 89

```
mod = mx.mod.Module(symbol=sym, context=mx.cpu(), data_names=data_names, label_names=None)
```

​	to be:

```
mod = mx.mod.Module(symbol=sym, context=mx.gpu(), data_names=data_names, label_names=None)
```

​	Now cnocr will run on GPU.

​	You can skip these anyway, and use the same environment as alas, but the OCR will run really slow.

- Install tqdm, a package to show progressbar.

```
pip install tqdm
```

## Extract item_template

Copy folder `dev_tools\item_template` to the map folder such as `<your_folder>\campaign_7_2`.

Change the folder in line 24

These template are named in chinese, rename them in English.

>**How to a name template image**
>
>You should use their full name, such as "138.6mm单装炮Mle1929T3", instead of short name or nickname, such as "DD_gun".
>
>If you have same item with different image, use names like `torpedo_part.png`, `torpedo_part_2.png`, they will a classified as torpedo_part

Uncomment the part for item extract in dev_tools/item_statistics.py, and run, you will have some new item templates. Here's an example log:

```
  1%|          | 107/12668 [00:05<10:24, 20.10it/s]2020-06-03 10:39:42.609 | INFO | New item template: 50
  1%|          | 158/12668 [00:07<10:42, 19.47it/s]2020-06-03 10:39:45.098 | INFO | New item template: 51
  2%|▏         | 207/12668 [00:10<10:33, 19.66it/s]2020-06-03 10:39:47.772 | INFO | New item template: 52
  2%|▏         | 215/12668 [00:10<11:20, 18.29it/s]2020-06-03 10:39:48.304 | INFO | New item template: 53
100%|██████████| 12668/12668 [10:33<00:00, 19.99it/s]
```

Rename those new templates.

If you find some items haven't been extracted,  try use line 140, instead of 141.

## Final statistic

Uncomment the part for final statistic, configure the csv file you wang to save.

The ocr model may not works fine in EN.

Here's an example log:

```
2020-06-03 12:23:55.355 | INFO | [ENEMY_GENRE 0.007s] 中型侦查舰队
2020-06-03 12:23:55.363 | INFO | [Amount_ocr 0.009s] [1, 1, 22]
100%|█████████▉| 14916/14919 [20:32<00:00, 13.20it/s]2020-06-03 12:23:55.442 | INFO | [ENEMY_GENRE 0.007s] 大型航空舰队
2020-06-03 12:23:55.455 | INFO | [Amount_ocr 0.013s] [1, 1, 1, 17]
2020-06-03 12:23:55.539 | INFO | [ENEMY_GENRE 0.007s] 敌方旗舰
2020-06-03 12:23:55.549 | INFO | [Amount_ocr 0.010s] [1, 2, 1, 63]
100%|█████████▉| 14918/14919 [20:33<00:00, 12.35it/s]2020-06-03 12:23:55.623 | INFO | [ENEMY_GENRE 0.007s] 精英舰队
2020-06-03 12:23:55.633 | INFO | [Amount_ocr 0.010s] [1, 1, 1, 17]
100%|██████████| 14919/14919 [20:33<00:00, 12.10it/s]
```

Now you got a csv file, formated to be:

```
<get_item_timestamp>, <battle_status_timestamp>, <enemy_genre>, <item_name>, <item_amount>
```

like this:

```
1590271317900,1590271315841,中型主力舰队,主炮部件T3,1
1590271317900,1590271315841,中型主力舰队,物资,23
1590271359374,1590271357251,小型侦查舰队,通用部件T1,1
1590271359374,1590271357251,小型侦查舰队,鱼雷部件T2,1
1590271359374,1590271357251,小型侦查舰队,物资,13
1590271415308,1590271413207,敌方旗舰,彗星,1
1590271415308,1590271413207,敌方旗舰,通用部件T3,1
1590271415308,1590271413207,敌方旗舰,科技箱T1,1
1590271415308,1590271413207,敌方旗舰,物资,42
1590271415308,1590271413207,敌方旗舰,_比萨研发物资,1
1590271415308,1590271413207,敌方旗舰,_鸢尾之印,1
```

You can open it in Excel or load it into database.

## Improvement

These code is running on single thread, you can try adding multiprocess to speed up. I didn't do that because it's still acceptable (20it/s without ocr, 12it/s with ocr)