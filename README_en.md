**| English | [简体中文](README.md) | [日本語](README_jp.md) |**

# AzurLaneAutoScript

Azur Lane bot with GUI (Supports CN, EN, JP, TW, able to support other servers), designed for 24/7 running scenes, can take over almost all Azur Lane gameplay. Azur Lane, as a mobile game, has entered the late stage of its life cycle. During the period from now to the server down, please reduce the time spent on the Azur Lane and leave everything to Alas.

Alas is a free open source software, link: https://github.com/LmeSzinc/AzurLaneAutoScript

EN support, thanks **[@whoamikyo](https://github.com/whoamikyo)** and **[@nEEtdo0d](https://github.com/nEEtdo0d)**.

JP support, thanks **[@ferina8-14](https://github.com/ferina8-14)**, **[@noname94](https://github.com/noname94)** and **[@railzy](https://github.com/railzy)**.

TW support, thanks **[@Zorachristine](https://github.com/Zorachristine)** , some features might not work.

GUI development, thanks **[@18870](https://github.com/18870)** , say HURRAY.

![](https://img.shields.io/github/commit-activity/m/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/tokei/lines/github/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/repo-size/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97) ![](https://img.shields.io/github/issues-pr-closed/LmeSzinc/AzurLaneAutoScript?color=4e4c97)

![gui](https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/doc/README.assets/gui_en.png)



## Features

- **Farm**: Main chapter, events, raids, 1-1 affinity farming, 7-2 mystery farming, 12-2 medium leveling, 12-4 large leveling, gems farming.
- **Reward**: Commission, tactical class, research, dorm, meowfficer, guild, missions, shop, shipyard, gacha, data key.
- **Daily**: Daily mission, hard, exercise, SOS, event daily AB, event daily SP, raid daily, war archives.
- **Opsi**: Ash beacon assist, Opsi monthly explore, Opsi daily, obscured zones, meowfficer farming, abyssal zones, siren strongholds.

#### Highlighted Features

- **Mood Control**: Calculates mood consumption, keep exp bonus or prevent red faces.
- **Event Exploring**: Able to run without clear mode, also handles fleet moving limits and other event mechanism.
- **Seamless Reward**: Calculates the finish time of research, commission, etc. Receive reward and dispatch again when time reached.
- **Operation Siren**: Receive Opsi dailies, purchase port shops, do Opsi dailies, do meowfficer farming, purchase Akashi's shop, clear obscured zones every 27 min, clear abyssal and strongholds. ~~What the ... is the strategic search, like sh*t, compares to Alas.~~
- **Opsi Explore**: After Opsi monthly reset, re-explore all zones without special radar (5000 oil item)



## Installation [![](https://img.shields.io/github/downloads/LmeSzinc/AzurLaneAutoScript/total?color=4e4c97)](https://github.com/LmeSzinc/AzurLaneAutoScript/releases)

Refers to [Installation tutorial](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en), including easy-installer manual, use manual, manual installation tutorial, remote access manual.

## Correctly Using the Scheduler

- **For *Task* and *Scheduler***

  In Alas, each task runs independently and is coordinated by a central scheduler. Once a task finishes, the scheduler automatically sets the next execution time. For example, if the *Research* task takes four hours to complete, the scheduler postpones it for four hours afterward, so it can seamlessly pick up where it left off.

- **For *Emotion Settings***

  Alas focuses on prevention, so it doesn’t wait for a warning about to appear before addressing morale. This approach helps keep morale above 120 and gain an extra 20% experience. For instance, if a fleet’s morale is at 113 and is rested in the Dorm’s second floor (+50/h) without bonuses from Oath (+0/h), Alas waits about twelve minutes for morale to recover to 120+ before resuming. Meanwhile, other tasks can still be run.

- **Making the Most of the Scheduler**

  An *incorrect* way to use the scheduler is turning on only a couple of tasks and manually managing them or restarting Alas. The *correct* approach is to enable all tasks that might be useful, let the scheduler do its job, minimize both the emulator and Alas to the background, and you can enjoy your life while Alas does the work for you. 


## Modify Game Settings

Modify the in-game settings according to this table.

|                    Name                    |   Value   |
|:------------------------------------------:|:---------:|
|            Frame Rate Settings             |  60 FPS   |
|         OpSi - Reduce TB Guidance          |    On     |
|   OpSi - Auto use items during Auto Mode   |    On     |
| OpSi - Default to Auto Mode in Threat Safe |    Off    |
|               Story Autoplay               |  Enable   |
|           Text Auto-Scroll Speed           | Very Fast |
|        No Sleep Mode on Main Menu          |    Off    |
|           Duplicate Ship Display           |    Off    |
|        Display Quick-Switch Prompt         |    Off    |
|       Display Battle Result Cutscene       |    Off    |

Operation Siren => Navigation Orders => Submarine Support:

|              Name             | Value |
|:-----------------------------:|:-----:|
| Automatically call submarines |  Off  |

Main Page => Build =>  Retirement => Quick Retire Options(left gear icon)：

|                Name                |                  Value                  |
|:----------------------------------:|:---------------------------------------:|
|        Prioritize Rarity 1         |                    R                    |
|        Prioritize Rarity 2         |                    E                    |
|        Prioritize Rarity 3         |                    N                    |
|   「own」a fully Limit Broken ship   |               Don't Keep                |
| 「has not」a fully Limit Broken ship | `Keep Enough to Max LB` or `Don't Keep` |

Remove the ship's equipment skins to avoid affecting image recognition.

## How to Report Bugs

Spend at least 5 minutes for thinking and preparing, before someone spend his/her 5 minutes to help you. Issues like "Why isn't running", "Why stuck here" will not be answered.

- Check [Frequently Asked Questions (FAQ)](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/FAQ_en_cn).
- Check updates of Alas, ensure it's the latest.
- Upload error logs under `log/error`, which include `log.txt` and recent screenshots. If it's an  unexpected behavior not an error, provide today's log under `log` and at least one screenshot.



## Known issues

- **Unable to handle network issues**
- **Low-end PCs might have issues**, Low-end PCs have a screenshot time cost over 1s, while middle-end costs about 0.5s, high-end costs about 0.3s.
- **Exercise may too late to quit when it's going to failed**
- **NemuPlayer does not support two-finger zoom out send from minitouch, unable to collect loves and coins in dorm**. NemuPlayer is not recommended.
- **Swipe may be treated as click if emulator stuck randomly**



## Alas Community Guidelines

See [#1416](https://github.com/LmeSzinc/AzurLaneAutoScript/issues/1416).



## Documents

[Map detection](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/perspective_en)

The core of an Azur Lane bot is map detection. If you simply use `Template matching` to search enemies, will encounter situation that mob enemies block the boss. Alas provide a better map detection method. In `module.map_detection`, you will be able to access full map data, like this.

```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```

Development documents, refer to [WIKI](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki).



## Join Development

Alas is still in active development, we will occasionally publish future work on [Issues](https://github.com/LmeSzinc/AzurLaneAutoScript/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22) and mark it as `help wanted`, feel free to submit [Pull Requests](https://github.com.com/LmeSzinc/AzurLaneAutoScript/pulls) to Alas, we will read every line of your code.

Oh yeah, don't forget to read the [development documentation](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start).



## Relative Repositories

- [AzurStats](https://azur-stats.lyoko.io/), An Azur Lane drop statistics platform based on Alas.
- [AzurLaneUncensored](https://github.com/LmeSzinc/AzurLaneUncensored), [For CN only] Repository for uncensoring Azur Lane CN, connecting to Alas.
- [ALAuto](https://github.com/Egoistically/ALAuto), Another Azur Lane bot for EN, not maintaining anymore. Alas imitated its structure.
- [ALAuto homg_trans_beta](https://github.com/asd111333/ALAuto/tree/homg_trans_beta), Alas introduced its homography transition into map detection.
- [PyWebIO](https://github.com/pywebio/PyWebIO), GUI framework that Alas uses.
- [MaaAssistantArknights](https://github.com/MaaAssistantArknights/MaaAssistantArknights), an Arknights assistant based on image recognition, helps you to complete daily quests efficiently! -> [MAA submodule tutorial](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/submodule_maa_cn)

## Contact Us

- Discord: [https://discord.gg/AQN6GeJ](https://discord.gg/AQN6GeJ)
