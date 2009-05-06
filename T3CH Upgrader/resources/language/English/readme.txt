T3CH Upgrader - Script to download, install and migrate to latest T3CH builds.

SETUP:
 Install to \scripts\T3CH Upgrader (keep sub folder structure intact)


USAGE: 
 run default.py

At startup Main Menu will indicate the availability of a new T3CH build.
Selecting option Download: <build_name> will start the process.

Pre Installation Settings:
--------------------------

You can setup several aspects of the installation using the Settings Menu:

1) Which drive & location to install to

   eg. E:\apps

   Will then result in build being unpacked to;
   eg.  E:\apps\<t3ch_build_name>\XBMC

2) The location of your xbox shortcut that boots to the XBMC as a dashboard, and the name of the shortcut that your mod chip boot too
   It is this location that a new shortcut will be written too inorder to boot to the newly installed T3CH build XBMC.
   It uses the TEAM XBMC Shortcut.xbe  and associated .cfg inorder to achieve this.


   Drive: eg. C:

   DashName:  eg. xbmc
   You can also use a subfolder in the dashname;
   
   eg. dashboard\xbmc

3) Maintain Copies;  
   This is a list of Folders and Files that you want to the post installation to be forced to COPY to new build.

4) Maintain Deletes;  
   This is a list of Folders and Files that you want to the post installation to be forced to DELETE from new build.


To Install a new T3CH Build
---------------------------

Select the Main Menu option "Download: <build_name>"

The following will happen;

1) Downloads T3CH rar
2) Extracts rar to location specified in Settings Menu.
3) Copies old build UserData (if still located within XBMC folder structure).
4) Copies Scripts (if they don't exist in new build) - same for vizualisations, skins etc.
5) Copies additional files/folders as per 'Maintain Copies'.
6) Deletes files/folders as per 'Maintain Deletes'.
7) Prompts to create and install new dash booting shortcuts.
   Backups are always made, named *.xbe_old and *.cfg_old on boot drive.
8) Prompt to Reboot

If all is well after reboot, you will be now running the latest T3CH build!


Local Installation:
-------------------
If you ftp a T3CH build archive (RAR or ZIP) to the designed rar download location (eg. E:\apps\) the Main Menu will show an option to install from that.


SVN Nightly Builds
------------------
NB. These are nightly builds of the xbox branch with nothing extra added and no tweaks (skins addons etc)
REMOTE INSTALL:

  1) Start script, change Build Location to 'SVN Nightly'
  2) Select Check now and install as normal

LOCAL INSTALL:
You can Local Install Nightly Builds from www.sshcs.com/xbmc

  1) Goto website and download xbox build
  2) Rename archive filename to format XBMC-YYYYMMDD_<whatever else here>.rar
     eg XBMC_XBOX_r19801.rar -> XBMC-20090429-r19801.rar
  3) ftp to xbox
  4) Select archive using Local Install


Switch To Another Build
-----------------------
The Menu option 'Switch to Another T3CH Build' will allow to either;
1) Switch to an existing local T3CH installation.
or
2) Select from the web archive of old T3CH builds, download, then install.

NB. Although the presented lists of available builds should have had the current build date removed, take caution not to overwrite current build!


Auto startup with XBMC Startup:
-------------------------------
It is possible to have the script start with XBMC by the use of autoexec.py.
It is included, all you need to do is copy it to Q:\scripts

It can startup in three modes:
# SILENT = do whole upgrade without GUI interaction.
# NOTIFY = just inform of new build
# NORMAL = Interactive prompt driven

The required mode needs to be edited into autoexec.py executebuiltin.  The script comes with it set to NOTIFY
eg.
xbmc.executebuiltin("XBMC.RunScript(Q:\\scripts\\T3CH Upgrader\\default.py, NOTIFY)")


Known Problems:
---------------
XBMC free RAM of less than ~ 31mb *may* cause unrar to fail.  If this happens, try lowering XBMC screen resolution to NTSC 4:3

If you're stuck, post in the appropiate forum at http://www.xboxmediacenter.com/forum/


Written By BigBellyBilly

Thanks to others for ideas, testing, graphics, language translations, skins ... VERY MUCH APPRECIATED !

bigbellybilly AT gmail DOT com