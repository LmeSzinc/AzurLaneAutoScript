# AzurLaneAutoScript

Alas, an Azur Lane automation tool with GUI (For CN server, can support other server).

![gui](doc/README.assets/gui_en.png)

## Features  

- **Campaign**: Currently support the first 6 chapter and 7-2  

- **Events**: Support「Skybound Oratorio」, specifically map D1 and D3, supporting handling of 光之壁? (Fleet is unable to proceed into square that has 光之壁. Support 开荒)

- **Daily Mission**: Able to finish everything in 30 minutes, repeated run will skip over what has been done on that day  

  Daily Mission(Submarine not support). Hardmode(Currently only support 10-4). Exercise, Auto SL.  
  
- **Events x3 PT**: 30 minutes to finish A1-B3  

- **Commissions**: Dispatch commision every 20 minutes during campaign, accept commission rewards, research rewards, and daily mission rewards.  

- **Misc Features**  

  Morale Control, Calculate Morale to prevent it from going sad, or to maintain Morale to earn experience   

  HP Monitoring, Low HP Retire, Frontline HP Balancing  

  Equipment Change  
 
  Periodic Screeshot Record  
 
  Auto Retire  
 
  Map completion mode, when running new map, it will try to do 3 star clear



## Installation

- Clone this item

- Installing dependacy using a virutal enviroment

```
pip install -r requirements.txt
```


| Device     | Emulator Version | Android Version | ADB Screenshot | UIAutomator2 Screenshot | ADB Click | UIAutomator2 Click |
| ---------- | ---------- | -------- | ------- | ------ | ------- | ------ |
| MemuPlayer | 7.1.3      | 5.1.1    | 0.308   | 0.275  | 0.294   | 0.146  |
| LDPlayer   | 3.83       | 5.1.1    | 0.329   | 0.313  | 0.291   | 0.146  |
| NoxPlayer  | 6.6.0.0    | 5.1.1    | 0.339   | 0.313  | 0.505   | 0.141  |
| MuMuPlayer | 2.3.1.0    | 6.0.1    | 0.368   | 0.701  | 0.358   | 0.148  |
| Oneplus5   |            | 7.1.1    | 1.211   | 0.285  | 0.447   | 0.160  |

This are the common emulation setting that we have tested on, tested Platform Windows 10, I7-8700K, 1080ti, nvme SSD, emulator resolution 1280x720, Azur Lane 60FPS, tested on map 7-2, on average execute 100 commands in seconds.  

As screenshot recognition has a high requirement needed to run, AzurLaneAutoScript currently does not support mobile devices, you MUST use an emulator.  

- Install an Android emulator  
- Set emulator resolution to 1280x720

### ADB Setup

- Install [ADB](https://developer.android.com/studio/releases/platform-tools)
- Add ADB to enviroment variables of the system and test wheather the configurationis successful using the below command

```
adb devices
```

### Installing UIAutomator2

[UIAutomator2](https://github.com/openatx/uiautomator2), is a library for automation, it can be use to speedup screenshots and clicks. `AzurLaneAutoScript` can also use ADB to perform screenshots and clicks, but it will be slightly slower.  

For performance optimisation, it is recommended to use ADB for screenshot, and UIautomator2 for clicks. (As U2 Screenshot is slightly faster compare to ADB screenshot, but CPU resource usage is doubled, while U2 click is superior in all ways compare to ADB)  

- Starting up

```
python -m uiautomator2 init
```

All connected devices will be install with [uiautomator-server](https://github.com/openatx/android-uiautomator-server/releases) , [atx-agent](https://github.com/openatx/atx-agent), [minicap](https://github.com/openstf/minicap), [minitouch](https://github.com/openstf/minitouch)
. If the device is a emulator, UIautomator2 will skip over the installation of minicap.  

- Check if the installation of UIautomator 2 is successful  

  Modify the serial in \dev_tools\emulator_test.py line 31 and, execute from root project directory (the same where you have the file alas.py) 
  
  The default serial for some emulators:
  
  | Device     | serial          |
  | ---------- | --------------- |
  | BlueStacks | 127.0.0.1:5555  |
  | NoxPlayer  | 127.0.0.1:62001 |
  | MuMuPlayer | 127.0.0.1:7555  |
  | MemuPlayer | 127.0.0.1:21503 |
  | LDPlayer   | emulator-5554   |

## Usage
 
- Double-click alas.pyw to run via graphical interface (GUI)
- (Not Recommeneded) to run alas.pyw throught cmd even thought Alas is using [Gooey](https://github.com/chriskiehl/Gooey) a library that converts the command line to a GUI, Alas didnt have a method for running command line before using gooey. Alas was meant to be use with gooey, as such the command line function was create hastily. Therefore, using command line to run Alas will not be easy.  
- (Not Recommended) to modify the configuration file 'config'alas.ini' and relation function in 'alas.py'
- Multi-usage: copy alas.pyw, and rename, double-click run on it. The settings of template.ini are copied when the first run runs. The script runtime uses the ini profile of the same name.

## Known issue

Sort by frequency

- **GUI move slowly, UIautomator2 move slowly**
- **Unable to deal with network issues** Reconnect pop-up, little chick pop-up
- **It will display green face, yellow face, red face** This is a bug, Alas will restart the game every 2 hour to update the affections level.
- **Exercise may fail SL**
- **Under rare circumstance ABD and UIAutomator2 will have convulsive seizures**
- **Screen draging will not work in rare circumstances**




## Doc
[Map Perspective](doc/perspective.md)

`Map Perspective` is the core foundation of Azur scripts. If you simply use (Template Matching) to search for enemies, it is inevitable that in some rare cases, the BOSS will be blocked by mobs. `AzurLaneAutoScript` provides a better map recognition menthod in `module.map`, you will be able to get a more complete sea information such as:


```
2020-03-10 22:09:03.830 | INFO |    A  B  C  D  E  F  G  H
2020-03-10 22:09:03.830 | INFO | 1 -- ++ 2E -- -- -- -- --
2020-03-10 22:09:03.830 | INFO | 2 -- ++ ++ MY -- -- 2E --
2020-03-10 22:09:03.830 | INFO | 3 == -- FL -- -- -- 2E MY
2020-03-10 22:09:03.830 | INFO | 4 -- == -- -- -- -- ++ ++
2020-03-10 22:09:03.830 | INFO | 5 -- -- -- 2E -- 2E ++ ++
```


[Development](doc/development.md)
- How to add a button
- How to adapt to a new map
- How to support other server/language

## Reference

- (Not open source) http://asaiq2.lofter.com/

  Ready made Azur scripts that has high completetion rate. Refer to the main functions and settings.

- https://github.com/Egoistically/ALAuto

  (Archived) https://github.com/perryhuynh/azurlane-auto

  EN Server script, use to mimic server architect.
