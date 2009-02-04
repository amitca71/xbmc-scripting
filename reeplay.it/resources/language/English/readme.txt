reeplay.it -  Script to view videos saved and shared at http://reeplay.it

SETUP:
 Install to \scripts\reeplay (keep sub folder structure intact)
 Video Plugin will self install (or update) if required.

USAGE: 
 run default.py

 PAD      - REMOTE      ACTION
 ---        ------      ------
 A        - SELECT      Select item from list
 WHITE    - TITLE/INFO  Main Menu
 B        - BACK        Back
 BACK     - Exit script
 Y        - Play Playlist


Startup
=======
On first run script will show the Menu, you will need to enter your reeplay.it username and password.

Once Username/Password are correct, exit menu and script will attempt to login and fetch your Playlists.

Select a Playlist, a list of Videos is shown.

Select a Video to view it.

Main Menu Options
=================
Check For Script Update On Startup 	- Change to True (yes) to force startup update check.
Videos Per Page			- This determines how many Videos are fetched for selected Playlist.
				Setting this value too high may result in XBMC running out of memory.
				To page throu Videos, select NEXT PAGE or PREVIOUS PAGE buttons on main screen (if shown)


Includes many skins, if yours isn't directly supports it will default to PMIII PAL


Written By BigBellyBilly - Thanks to others if I've used code from your scripts.
Additional language string, Readme translations and new skins welcome.

bigbellybilly AT gmail DOT com - bugs, comments, ideas, help ...

Like my script? Why not buy me a beer?  (Use link below)
https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=bigbellybilly%40gmail%2ecom&item_name=Cheers&no_shipping=1&cn=Donate%20message&tax=0&currency_code=GBP&lc=GB&bn=PP%2dDonationsBF&charset=UTF%2d8