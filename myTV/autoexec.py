# Adding this code to your own autoexec.py will cause all previously
# saved myTV Alarm Clocks to be setup on XBMC startup.

import xbmc

xbmc.executescript(xbmc.translatePath('Q:/scripts/myTV/AlarmClock.py'))

