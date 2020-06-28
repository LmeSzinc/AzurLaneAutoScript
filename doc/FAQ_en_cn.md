# FAQ 常见问题

Here list some frequently asked questions (FAQ).

这里列举了一些常见问题.

## Why Alas is not running 为什么Alas不运行

```
retire_method = one_click_retire
retire_amount = retire_all
enhance_favourite = no
enable_exception = yes
scout_hp_weights = 1000,1000,1000
INFO | <<< SETTINGS SAVED >>>
```

Please run other funtions.

The function you are running is the "Setting", is used to save settings. You see this because settings save is succeed. You can choose other functions to run, such as "Main_chapter" and "Event".

请运行其他功能.

你运行的功能是"设置", 是用来保存设置的. 你看见这个是因为设置保存成功了, 你可以运行其他功能比如"主线图"和"活动图".



## Why Alas get stuck in reward loop 为什么Alas卡在收获里

```
INFO | Reward loop wait
INFO | [Reward_loop_wait] 20 min
```

Please check your settings of "stop conditions".

You see this because Alas triggered a stop condition, all task you gave to Alas have finished. Alas go into reward loop to prevent player get nothing for a whole day. If you don't want Alas to stop, don't set any stop conditions.

请检查你的"停止条件"设置.

你看见这个是因为Alas触发了停止条件, 你给Alas的所有任务已经完成. Alas进入收获循环来避免玩家一天什么都没有得到. 如果你不希望Alas停下, 不要设置任何停止条件.



## Why Alas get stuck in emotion recover 为什么Alas卡在心情回复里

```
INFO | Click ( 507, 457) @ C3
INFO | Combat preparation.
INFO | [Emotion recovered] 2020-06-26 23:42:00
INFO | [Emotion recovered] 2020-06-26 23:42:00
INFO | [Emotion recovered] 2020-06-26 23:42:00
```

Because Alas is waiting for mood recovered.

If you think this is not what you expected, please check your setting in "Mood control". If you want to continue even if it's red face, turn off "enable_emotion_reduce" and turn on "ignore_low_emotion_warn". If you changed your fleet by hand, update `EmotionRecord` in `config/alas.ini`.

因为Alas正在等待心情回复.

如果你认为这不是你希望的, 请检查你的"心情设置". 如果你希望红脸出击, 关掉"启用心情消耗", 并开启"无视红脸出击警告". 如果你手动调整了队伍, 在 `config/alas.ini` 中更新 `EmotionRecord`.

## How to run Reward + Main module 怎样同时运行主线图出击和收获

You don't need to do anything, This is automatic.

When you running "Main_chapter", "Event", "Raid", Alas will check reward from time to time according to your settings.

你不需要做任何操作, 这是自动的

当你运行"主线图", "活动图", "共斗活动"的时候, Alas会根据设置, 时不时地检查收获.

## How to use only one fleet 怎样只使用一支舰队

```
WARNING | Mob fleet 1 and boss fleet 1 is the same
WARNING | They should to be set to different fleets
```

```
WARNING | You should use 2 fleets from chapter 7 to 13
WARNING | Current: mob fleet 1, boss fleet 0
```

Please use 2 fleets.

Don't try to edit the code to bypass these checks, because logics in every maps are hardcoded in 2 fleets. Use only one fleet will cause error. Using 2 fleets helps reducing the posibility of BOSS fleet get stuck by mob enemies from chapter 7 to chapter 9.

请使用两队.

不要试图修改代码来绕过这些检查, 因为每张地图的逻辑都是按两队写死在代码里的. 只使用一队会导致报错. 在第七章到第九章, 使用两队有助于降低BOSS队被道中怪堵住的概率.

## Starting from current page is not supported 不支持从当前界面启动

```
INFO | <<< UI ENSURE >>>
INFO | Unknown ui page
INFO | Unable to goto page_main
WARNING | Starting from current page is not supported
WARNING | Supported page: ['page_main', 'page_campaign', 'page_fleet', 'page_exercise', 'page_daily', 'page_event', 'page_sp', 'page_mission', 'page_raid']
WARNING | Supported page: Any page with a "HOME" button on the upper-right
```

Please check your page in game when you starting Alas.

Alas can goto the page it need automatically, but only allow starting at these pages: page_main, page_campaign, page_fleet, page_exercise, page_daily, page_event, page_sp, page_mission, page_raid. Alas can also start at any page with the "HOME" button on the upper-right. Most pages in game have that, except page_main itself, dorm, meowfficer.

请检查你在启动Alas时的游戏界面.

Alas可以自动切换到需要的游戏界面, 但是只允许在这些界面下启动: 主界面, 出击, 编队, 演习, 每日, 活动, SP活动, 任务领取, 共斗活动. Alas也可以在右上角有"一键回港"按钮的界面下启动, 游戏中大部分界面都有这个按钮, 除了主界面本身, 后宅, 指挥喵.



## Why Alas lost connection when I start another emulator 为什么我打开另一个模拟器时Alas会断开连接

Because you have 2 ADB in different versions.

Different version of ADB will kill each other when starting. Chinese emulators (NoxPlayer, LDPlayer, MemuPlayer, MuMuPlayer) use their own adb, instead of the one in system PATH, so when they start they kill the adb.exe Alas is using. There are 2 ways to solve this:

- Update both your emulator and your ADB to the latest.

  If you install Alas by Easy_install, update the ADB in `<your_alas_install_folder>\python-3.7.6.amd64\Lib\site-packages\adbutils\binaries` to the latest.
  
  If you install Alas in the advanced way, update the ADB in your system PATH.
  
- Replace the ADB in your emulator with the one Alas is using.

  If you install Alas by Easy_install, find your ADB in `<your_alas_install_folder>\python-3.7.6.amd64\Lib\site-packages\adbutils\binaries` . If you install Alas in the advanced way, find your ADB in system PATH. Then goto you emulator installation folder, replace them. 
  
  Take NoxPlayer as an example. There are 2 ADB in nox install folder, `adb.exe` and `nox_adb.exe`. Make backup for these 2 files and delete them. Copy two `adb.exe` to your nox install folder, and rename them to `adb.exe` and `nox_adb.exe`.

因为你有两个不同版本的ADB

不同版本的ADB之间会互相结束对方. 国产模拟器 (夜神模拟器, 雷电模拟器, 逍遥模拟器, MuMu模拟器) 都会使用自己的ADB, 而不会使用配置在环境变量中的ADB. 所以当它们启动时, 就会结束Alas正在使用的 adb.exe. 有两个方法解决这个问题:

- 将你的模拟器和你的ADB都更新到最新.

  如果你使用傻瓜式安装包安装的Alas, 更新位于 `<你的Alas安装目录>\python-3.7.6.amd64\Lib\site-packages\adbutils\binaries` 下的ADB.
  
  如果你使用的高级方法安装的Alas, 更新位于环境变量中的ADB.
  
- 将模拟器中的ADB替换为Alas使用的ADB.

  如果你使用傻瓜式安装包安装的Alas, 找到位于 `<你的Alas安装目录>\python-3.7.6.amd64\Lib\site-packages\adbutils\binaries` 下的ADB. 如果你使用的高级方法安装的Alas, 找到位于环境变量中的ADB.

  以夜神模拟器为例, 夜神模拟器安装目录下有两个ADB,  `adb.exe` 和 `nox_adb.exe` 备份它们并删除. 复制两份 `adb.exe` 到夜神模拟器安装目录, 重命名为 `adb.exe` 和 `nox_adb.exe`. 