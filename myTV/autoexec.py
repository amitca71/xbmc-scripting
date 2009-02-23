# Adding this code to your own autoexec.py will cause all previously
# saved myTV Alarm Clocks to be setup on XBMC startup.

import xbmc, os.path

xbmc.executescript(xbmc.translatePath(os.path.join('Q:'+os.sep,'scripts','myTV','AlarmClock.py')))

