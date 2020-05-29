# Quick guide

#### Requirements

* A good PC (Potato PC may have problems running the emulator correctly)
* [Python](https://www.python.org/downloads/release/python-376/) installed and added to PATH (recommended 3.7.6 64bit version only) 
* Latest [ADB](https://developer.android.com/studio/releases/platform-tools) added to PATH.
* [I don't know how to add to PATH](https://www.youtube.com/watch?v=Y2q_b4ugPWk)
* The use of a virtual environment (venv) in python is highly recommended
* ADB debugging enabled and emulator with 1280x720 resolution


# How to create e python virtual environment

* First install [Python](https://www.python.org/ftp/python/3.7.6/python-3.7.6-amd64.exe)

* Create a folder where you will put the virtual environment, I recommend creating a folder `venv` in the project's root directory
* Go to project root in command line
* type `python -m venv path_to_your_folder\venv`

    ![venv](quickguide.assets/venv.png)
    
    You can see that now python has created some folders and files in the venv folder, it has created a completely clean virtual environment, thus preventing any conflicts.
* Now, it is necessary to activate the virtual environment in command line, go to project root (the same where you have the file alas.py) and type `.\venv\scripts\activate.bat`

   ![venv_activate](quickguide.assets/venv_activate.png)
   
   Look that a `(venv)`, with that we know that we are in a virtual environment.
   
   If you type `pip list` should get this output:
   
   ![pip_list](quickguide.assets/pip_list.png)

    Now, you can proceed with the installation of the requirements through `pip install -r requirements.txt`



#### Installation

* Clone this repository
* Install the requirements.txt (`pip install -r requirements.txt`)
* Install an android emulator (Tested on BlueStacks)
* The android emulator resolution must be set to `1280x720`

* Test if the ADB is working correctly `adb devices`
            
    The output must be something like this

    ![ADB](quickguide.assets/adb_test.png)

    Test if your Python is working correctly `python --version`

    ![Python](quickguide.assets/python_test.png)
    
* Install uiautomator2

uiautomator2, is an automated test library that can speed up screenshots and clicks. You can also use ADB to perform screenshots and clicks, but it is a slower way.

For performance optimization, it is recommended to use ADB screenshots, uiautomat2 screenshot slightly faster than adb screenshot, but cpu consumption double.

* Perform

    `python -m uiautomator2 init`
    
    The output must be something like this:
    
    ![U2](quickguide.assets/u2_test.png)
    (in this case, I had already installed)
    
* Check if uiautomator2 was installed successfully

Modify the `serial` in \dev_tools\emulator_test.py line 31 and, execute from root project directory (the same where you have the file alas.py)

`python -m dev_tools.emulator_test`

The output must be something like this:

![emulator_test](quickguide.assets/emulator_test.png)

The default `serial` for some emulators:

| Android Emulator | serial          |
|------------------|-----------------|
| NoxPlayer        | 127.0.0.1:62001 |
| MuMuPlayer       | 127.0.0.1:7555  |
| Bluestacks       | 127.0.0.1:5555  |
| LDPlayer         | emulator-5554   |

You can check a new app installed in your emulator:

![emulator_test](quickguide.assets/atx.png)

If you open up can check if are running:

![emulator_test](quickguide.assets/atx_running.png)

If are not running, you cannot use U2 and will get error.


## How to use Use

Double-click alas.pyw to run via graphical interface (GUI), If dont work you can double-click alas.bat or type `py alas_en.pyw` from command line to open the GUI

Multi-usage: copy alas.pyw, and rename, double-click run on it. The settings of template.ini are copied when the first run runs. The script runtime uses the ini profile of the same name.




    

    
    