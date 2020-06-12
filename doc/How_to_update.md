# How to use updater.bat

* This only will work if you have download the repository with GIT, if you downloaded the .zip you will have to delete the folder and download it again through GIT, see step 2.
* [Download and install the last GIT version](https://git-scm.com/download/win)
* Open the file `updater.bat` with any text editor
* Change the `C:\Program Files\Git\cmd` for the path that you are installed, you don't usually need to change it, but make sure it is installed in the same path as it is in the file.
* It is important that the path you enter is the same as the one with the git.exe file as shown in the image.

    ![](how_to_update.assets/git.png)
* In `updater.bat` we have 2 source options, most of the time there will be no difference between them, if in doubt, choose option 1.

# How to Download repository through GIT

* Like above, you need GIT installed and make sure it is installed in the same path as it is in the file `downloader.bat`.
* If you already download `AzurLaneAutoScript-master.zip`, just extract and double-click in `downloader.bat`, then the repository will be cloned again, but now the .git folder will be created.
* If you haven't downloaded the .zip, just download the `downloader.bat` file, created a folder where you want ALAS to be downloaded, put `downloader.bat` inside that folder and click.