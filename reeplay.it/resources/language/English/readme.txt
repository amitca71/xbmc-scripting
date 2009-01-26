reeplay.it -  Script to view videos saved and shared at http://reeplay.it

SETUP:
 Install to \scripts\reeplay (keep sub folder structure intact)

USAGE: 
 run default.py

 PAD      - REMOTE      ACTION
 ---        ------      ------
 A        - SELECT      Select item from list
 WHITE    - TITLE/INFO  Main Menu
 B        - BACK        Back
 BACK     - Exit script


Startup
=======
On first run script will show the Menu, you will need to enter your reeplay.it username and password.

Once Username/Password are correct, exit menu and script will attempt to login and fetch your Playlists.

Select a Playlist, a list of Videos is shown.

Select a Video to view it.

Main Menu Options
=================
Check For Script Update On Startup 	- Change to True (yes) to force startup update check.
Videos Per Page				- This determines how many Videos are fetched for selected Playlist.
					  Setting this value too high may result in XBMC running out of memory.
					  To page throu Videos, select NEXT PAGE or PREVIOUS PAGE buttons on main screen (if shown)


Written By BigBellyBilly - Thanks to others if I've used code from your scripts.
Additional language string and Readme translations welcome.
bigbellybilly AT gmail DOT com - bugs, comments, ideas, help ...