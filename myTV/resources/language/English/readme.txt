myTV - A tv guide, using listing data from your own DataSource.

INSTALLATION
============

Unpack package, keeping folder structure intact, to Q:\scripts\myTV

USAGE
=====

run default.py

CONTROLS:
---------

 PAD        - REMOTE
 ---            ------
 X (blue)   - DISPLAY   Toogle Channel/Day/Time List Navigation footer (NavLists).
 A (green)  - SELECT    On EGP; Display programme infomation.
                        On NavLists; Selects item (ie Channel/Day/Time)
 DPAD       - ARROWS    On ; Move between programmes.
                        On Lists; switch between lists.
 Triggers   - SKIP -/+  On EPG; Guide page up/down
 WHITE      - TITLE/INFO  MainMenu (leading to Settings Menu)
 B (red)    - BACK        In Menus=BACK; 
                          On EPG with NOTV Card:    View HD CHannels;
                          On EPG with TV Card:      Record
 Y (yellow) - IMDb lookup
 BACK         Back (in menus) or Exit script


NOTES:
    - This script requires a XBMC build from 'Atlantis' (2008-0812) onwards (inorder to supports new WindowXML and Language builtin.
    - Downloaded channel listing data files are stored in T:\UserData\script_data\myTV\cache\<channel_id>_<date>.dat files.
    - Send me your custom DataSource files/suggestions for inclusion into future releases.

    - LOGOS:  No logos are supplied.  
              Use the Setting Menu option 'Download Missing Logos'.
              Select country; from which you will be able to match missing logos to downloadable logos.

              Logos are saved using filesafe names (eg '+' renamed to 'plus' space as '_') based on Channel Name.
              myTV will attempt to match channel to logo using Channel Name or ID (from 'UserData\myTv\cache\Channels_<datasource_name>.dat')
              
              If you wish to ftp your own logos to "UserData\myTv\logos" - name them as either filesafe Channel Name or ID.
              They must be image type gif.
              Recommended size is approx 100 x 75 (aspect ratio kept when displayed)

    - Updates:  Script can be set to check for script update from Settings menu.  If update found on script startup it
                Will make a backup then download/install the update and restart.

    - Skins / Langauge Translations: If you wish to contribute, please send me it for inclusion in a future release. Thanks
    - Most things can be changed in the Settings Menu, if it broken, please contact me.


SUPPORTED TV CARDS
==================
Hauppauge (Nova-T, Win2000, Nova USB)
Nebula
myTheater
Dreambox
WebScheduler
SageTV


NOTES ON ZAP2IT DATASOURCE (US users)
=====================================
sign up for an account at labs.zap2it.com using certificate code MYTV-9K2N-UTG1


USING 'SAVE PROGRAMME'
======================
Has 3 options;
1) SMB - send programme information to a PC that has a Shared folder.
    This option uses the SaveProgramme string stored in the Config.dat file and sends to a PC Share folder, using the filename also
    taken from the Config.dat file.
    Both the SaveProgramme string and the destination filename can use the $ substitution system. ie $T = programme title

2) CUSTOM Script - Calls 'SYSTEM\SaveProgramme_<tvcard>.py' - in there you can do whatever you want.
    An included example of using this method is the file 'SaveProgramme_Nebula.py'.
    This module takes the Programme and Channel information, reformats it suitable for a Nebula tv card, then send the data to the
    Nebula cards HTTP server.

3) CUSTOM Script then SMB - Calls your own 'SaveProgramme_<tvcard>.py' script which will format a return string, THEN send that string to your SMB
    An included example of using this method is the file 'SaveProgramme_Hauppage.py'.
    This module takes the Programme and Channel information, forms a return string (a Windows XP 'Schedule Task' cmd line),
    then the return string is sent in a file to the SMB.


EPG SCHEMES
===========
Schemes are folders stored under path myTV\System\epg\<skin folder name>
You can add your own skin folder, it should contain these gfx files:

    dialog-panel.png
    skin.dat

Skin.dat configures myTV display settings particular for that skin. 
Example:
[SKIN]
font_title = special13
font_short_desc = font10
font_epg = font13
font_chname = font10
colour_chnames= 0xFFFFFFFF
colour_title = 0xFFFFFFFF
colour_title_desc = 0xFFFFFFFF
colour_epg_text_odd = 0xFFFFFFFF
colour_epg_text_even= 0xFFFFFFFF
colour_epg_text_fav = 0xFF000000
file_epg_nofocus_odd = DarkBlue.png
file_epg_nofocus_even = DarkBlue.png
file_epg_nofocus_fav = DarkYellow.png
file_epg_focus = LightBlue.png
height_epg_row = 30
height_epg_row_gap = 3
colour_arrows = 0xFFFFFFCC


USING FAV SHOWS FEATURE
=======================
ADDING
1) Highlight programme in tv guide
2) From menu, select Add To Fav Shows
DELETING
1) From menu, select Maintain Fav Shows
2) Select show from list, confirm to delete
7-DAY DISPLAY
1) From menu, select '7-Day Display'


ALARM CLOCK
===========
Highlight a programme, then from the MainMenu, select 'Set Alarm'
This is will set a XBMC Alarm Clock, also reset it if xbox turned off/on.
If you wish XBMC to be rest with saved Alarms, edit autoexec.py to add this line:

xbmc.executescript('q:\\scripts\\mytv\\system\\AlarmClock.py')


INSTRUCTION TO SETUP myTV TO USE NEBULA TV CARD RECORDING
=========================================================
1) On your PC that has the Nebula tv card installed, Enable the 'DigiTV Web Page Interface'

2) Edit 'SaveProgramme_Nebula.py' and enter your remote PC IP

4) run myTV - Select Nebula TV Card when asked. This can also be selected from the Config Menu.

5) In MENU; Setup your PC SMB settings (ie IP address, share folder name etc)

6) In MENU; Select SaveProgramme method of 'CUSTOM SCRIPT'

7) To save a programme;
    a) Highlight programme in the guide
    b) Enter MENU and select SaveProgramme


INSTRUCTION TO SETUP myTV TO USE HAUPPAUGE TV CARD RECORDING
============================================================
This method works by sending a file, that contains a formatted Schedule Task command line, to the remote PCs share folder.
On the PC, another Schedule Tasks which runs every minute, will check for files called 'myTV_rec_<date>_<Time>_<Duration>_<Title>.bat
in the shared folder, then run them.  Its those Scheduled Tasks that inturn activate the Hauppauge tv card.

1) On PC; copy these file to your PCs shared folder' (ie. C:\XBMC)
    SYSTEM\mytv_schedular_setup.bat
    SYSTEM\mytv_schedular.bat

2) On PC; Edit both those files, changing the folder name to be that of your own share folder.

3) On PC; run mytv_schedular_setup.bat - A Scheduled Task will be created that now runs every minute, monitoring the shared folder.

4) On XBOX; Edit 'SaveProgramme_Hauppauge.py' 
    a) Change the following line to point the where the installed Hauppauge exe lives
        HAUPP_EXE = "C:\\Program Files\\Hauppauge\\WinTV NOVA\\DVB-TV.exe"
    b) Change the following line to point to where recordings will be saved too
        HAUPP_REC_DIR =    "E:\\TV Recordings\\"

5) On XBOX; run myTV script - Select Hauppauge TV Card when asked.

7) In myTV MENU; Setup your PC SMB settings (ie IP address, share folder name etc) 

8) In myTV MENU; Setup your PC SMB settings - set filename to be mytv_rec_$Y$M$D_$H$I_$l.bat
    This is the filename that will be saved in the remote PC SMB folder and its name is important

9) In myTV MENU; Select SaveProgramme method of 'CUSTOM SCRIPT then SMB'

10) To save a programme;
    a) Highlight programme in the guide
    b) Enter MENU and select SaveProgramme

NB. I recommend that you enable the XBMC Internet Time Sync and your PC Time sync option to try and get them to have
the same times.


INSTRUCTION TO SETUP myTV TO USE myTheater TV CARD RECORDING
============================================================
Instruction same as for Hauppaueg tv card.  
But, the myTheater codes are setup to translate only Zap2it Station IDs to myTheater codes.


HOW TO WRITE YOUR OWN DATASOURCE
================================

Two essential things are required from a data source site.

    1) Channel list.    - Used to provide channel ID and associated Channel name.
    2) Channel data.    - Supplies Channel/Programme information.
                          - "Must supply" - Title, Description, Start Time

I've provided several DataSources.  So the easiest way is to copy one of those to get started.

1) Create a file myTV\DataSource\<somename>_DataSource.py

2) <somename>_DataSource.py must contain;
    a) class ListingData

    b) function    def getName()
            return string of data source name
        
    c) function    def getChannels()
            return list containing [chID, chName]

    There is generic function to do this in the library 'getChannelsLIB'.
    This will work for you if you can scrape your site and gather [chID, ch name] from a regular expression.

    d) function    def getChannel()
            return list of Programme class  ie [Programme(title, description, startTimeInSecs, endTimeInSecs)]
            start/end times, must be secs since epoch.  
            See Bleb_DataSource.py for example of filling endTime if not known.

3) Thats it.

Written By BigBellyBilly            - Thanks to others if I've used code from your scripts.
bigbellybilly AT gmail DOT com     - bugs, comments, ideas, skin / language contributions ...


        
Find my scripts useful, why not Buy Me A Beer ? 
https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=bigbellybilly@gmail.com&item_name=Cheers!&no_shipping=1&tax=0&currency_code=GBP&lc=GB
