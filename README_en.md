**| English | [简体中文](README.md) |**

# StarRailCopilot

Star Rail Copilot, a bot for Honkai: Star Rail, based on the next generation ALAS framework.

# Install

### Get source code

SRC is still in development, does not have an auto-installer yet, requires classic python project deployment.

Clone this repository.

```bash
git clone https://github.com/LmeSzinc/StarRailCopilot
```

Enter project directory.

```bash
cd StarRailCopilot
```

Create a python 3.10.10 environment using conda. Let's say the new environment is named `src`.

>Note that we don't maintain requirements for lower or higher python versions, 3.10.10 is recommended.

```bash
conda create -n src python==3.10.10
```

Activate the environment just created.

```bash
conda activate src
```

Install requirements.

```
pip install -r requirements.txt
```

### Install an Emulator

1. Download [ADB](https://developer.android.com/tools/releases/platform-tools) and configure it into environment variables.
2. Install the game client in emulator, not the desktop client. BlueStacks is recommented.

> **Why use emulators?** If you run a bot on the desktop client, game windows must stay at front. I guess you don't wanna baby-sit there without being able to move the mouse and keyboard while running the bot, so use the emulators.

> **How's the performance?** Lme's 8700k+1080ti using MuMu12 emulator with graphic settings very high  gets 40 fps. It shouldn't be a problem to run with maximum graphic settings and 60 fps if you have newer PC specs.

## Usage

Still in the environment just now, launch the GUI backend. (running on port 22367 by default)

```bash
python gui.py
```

Access `127.0.0.1:22367` in browser.

Goto `SRC settings` - `Emulator Settings` - `Serial`, fill it according to help texts.

Goto `Overview` page, click `Run` button. (SRC will auto launch emulator and game client if they are not running. Emulator launch only supports MuMu family and Nox Player family for now)

Keep the bot running, SRC will auto login and empty trailblaze power when it's recovered. To save resources, set `SRC Settings` - `Optimazation Settings` - `When Task Queue is Empty` to `Close Game`.

## Development

Discord https://discord.gg/aJkt3mKDEr QQ Group 752620927

- Development Docs (menu is on sidebar): [Alas wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start) (in Chinese). However, there is ton of code newly written, it is recommended to read the source code and historical commits.

- Development Road Map: [#10](https://github.com/LmeSzinc/StarRailCopilot/issues/10). Pull Requests are welcomed, just pick the part you interested to work on.

> **How to add multi-language or multi-server support?** Need assets updates, see ["Adding a Button" in development docs](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/4.1.-Detection-objects#%E6%B7%BB%E5%8A%A0%E4%B8%80%E4%B8%AA-button).



## About ALAS

SRC is based on an Azur Lane bot [AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript). After 3 years of development, ALAS has reached a high degree of completion, but it has also accumulated a lot of shit code that is difficult to change. We hope that Fix these issues on a new project.

- Update OCR. ALAS has trained multiple models on cnocr==1.2.2, but the dependent [mxnet](https://github.com/apache/mxnet) is no longer active, machine learning is developing rapidly, and the speed of new models and the correct rate crushes the old model.
- Converting setting files into [pydantic](https://github.com/pydantic/pydantic) models. Since the concept of task and scheduler was added, the number of user settings greatly increased. ALAS has built a code generator to implement setting read and update. pydantic will make things more elegantly.
- Better Assets management. button_extract helps ALAS to easily maintain 4000+ template images, but it has a serious performance issue, and the reminder of multi-server supported is also submerged in a large amount of meaningless logs.
- Reduced coupling to Azur Lane. The ALAS framework and ALAS GUI have the ability to interface with other games and their not, but the completed [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) plug-in for Arknights and [fgo-py](https: //github.com/hgjazhgj/FGO-py) plug-in under development have found serious coupling problems between ALAS and the Azur Lane game itself.