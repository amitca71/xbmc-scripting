############################################################################################################
#
# Dreambox - Custom script called from myTV 'Save Programme' menu option.
#
# NOTES:
# Sends URL cmds to Dreambox PVR web interface that can set/list/delete timers and programmes.
#
# This is currently setup to use Channel IDs found with the RadioTimes Datasource, to use any other
# you need to edit in the appropiate Channel IDs.
#
# Setup Dreambox IP below.
#
# Many Thanks to kaisersose for the idea and Dreambox testing.
# Any problems contact me at BigBellyBilly AT gmail dot com
# ChangeLog:
# 09/03/06 - Created
# 03/05/06 - Updated to only pass Channel/Programme to run().
# 11/05/06 - Updated. Config now done throu GUI.
# 22/08/06 - Updated: Uses new Config.
# 09/09/08 - Updated for myTV v1.18
# 22/03/09 - Updated for myTV v1.19 - new config and settings
############################################################################################################

import xbmc, urllib, time
from mytvLib import *
from bbbGUILib import *
import mytvGlobals
from string import zfill, find
xbmc.output("SaveProgramme - Dreambox - Date: 08-04-2009")

__language__ = sys.modules["__main__"].__language__

# CHANNELS - Translates Channel ID into Dreambox REF ID
REF_CODES = {

# USING RADIOTIMES DATASOURCE
# You will have to change the Channel Codes if your using a different DataSource
"3577" : "1:0:1:80EA:21:1000:6180000:0:0:0:",   # ABC - VIC
"2577" : "1:0:1:80E9:21:1000:6180000:0:0:0:",  # ABC - N.S.W
"7577" : "1:0:1:80EC:21:1000:6180000:0:0:0:",  # ABC - Q.L.D
"8577" : "1:0:1:80ED:21:1000:6180000:0:0:0:",  # ABC - S.A
"9577" : "1:0:1:7D0B:20:1000:6180000:0:0:0:",  # ABC - WA
"468" : "1:0:1:80F1:21:1000:6180000:0:0:0:",    # ABC2
"3551" : "1:0:1:4A3A:13:1000:6180000:0:0:0:",   # SBS - Melbourne
"2551" : "1:0:1:7D02:20:1000:6180000:0:0:0:",   # SBS - Sydney
"7551" : "1:0:1:7D03:20:1000:6180000:0:0:0:",   # SBS - Brisbane
"3555" : "1:0:1:7D0E:20:1000:6180000:0:0:0:",   # Ch7 - Melbourne
"2555" : "1:0:1:7D0D:20:1000:6180000:0:0:0:",   # Ch7 - Sydney
"7555" : "1:0:1:7D0F:20:1000:6180000:0:0:0:",   # Ch7 - Brisbane
"3558" : "1:0:1:791C:1F:1000:6180000:0:0:0:",   # Ch9 - Melbourne
"2558" : "1:0:1:791D:1F:1000:6180000:0:0:0:",   # Ch9 - Sydney
"7558" : "1:0:1:791A:1F:1000:6180000:0:0:0:",   # Ch9 - Brisbane
"3574" : "1:0:1:791B:1F:1000:6180000:0:0:0:",   # Ch10 - Melbourne
"2574" : "1:0:1:791E:1F:1000:6180000:0:0:0:",   # Ch10 - Sydney
"7574" : "1:0:1:7919:1F:1000:6180000:0:0:0:",   # Ch10 - Brisbane
"5" : "1:0:1:3ED:1:1000:6180000:0:0:0:",		# Arena
"285" : "1:0:1:3A9D:F:1000:6180000:0:0:0:",    # Arena +2
"151" : "1:0:1:1F4B:8:1000:6180000:0:0:0:",    # AURORA
"68" : "1:0:1:0fA8:1F:1000:6180000:0:0:0:",           # Bio.
"3" : "1:0:1:3EB:1:1000:6180000:0:0:0:",		# Comedy
"283" : "1:0:1:3A9B:1F:1000:6180000:0:0:0:",    # Comedy +2
"228" : "1:0:1:2EE8:C:1000:6180000:0:0:0:",		# E!
"67" : "1:0:1:0fA8:4:1000:6180000:0:0:0:",     # FOOD
"6" : "1:0:1:03EE:1:1000:6180000:0:0:0:",      # FOX Classics
"286" : "1:0:1:3A9E:1F:1000:6180000:0:0:0:",    # Classics +2
"8" : "1:0:1:3F0:1:1000:6180000:0:0:0:",		# FOX8
"288" : "1:0:1:3AA0:1F:1000:6180000:0:0:0:",    # FOX8 +2
"26" : "1:0:1:07D6:2:1000:6180000:0:0:0",     # Hallmark
"327" : "1:0:1:426F:11:1000:6180000:0:0:0",    # HITS
"9" : "1:0:1:3F1:1:1000:6180000:0:0:0:",		# LifeStyle
"289" : "1:0:1:3AA1:1F:1000:6180000:0:0:0:",    # LifeStyle +2
"46" : "1:0:1:0BBE:3:1000:6180000:0:0:0",     # Ovation
"86" : "1:0:1:138E:5:1000:6180000:0:0:0:",		# Sci Fi
"1" : "1:0:1:3E9:1:1000:6180000:0:0:0:",		# TV1
"281" : "1:0:1:3A99:1F:1000:6180000:0:0:0:",    # TV1 +2
"4" : "1:0:1:3EC:1:1000:6180000:0:0:0:",		# UKTV
"284" : "1:0:1:3A9C:1F:1000:6180000:0:0:0:",    # UKTV +2
"10" : "1:0:1:3F2:1:1000:6180000:0:0:0:",		# W
"290" : "1:0:1:3AA2:1F:1000:6180000:0:0:0:",    # W2
"7" : "1:0:1:3EF:1:1000:6180000:0:0:0:",		# Movie One
"287" : "1:0:1:3A9F:1F:1000:6180000:0:0:0:",    # Movie Two
"22" : "1:0:1:7D2:2:1000:6180000:0:0:0:",		# Movie Extra
"23" : "1:0:1:7D3:2:1000:6180000:0:0:0:",		# Movie Greats
"30" : "1:0:1:7DA:2:1000:6180000:0:0:0:",		# Showtime Greats
"2" : "1:0:1:3EA:1:1000:6180000:0:0:0:",		# Showtime
"282" : "1:0:1:3A9A:1F:1000:6180000:0:0:0:",    # Showtime +2
"82" : "1:0:1:138A:5:1000:6180000:0:0:0:",		# TCM
"24" : "1:0:1:7D4:2:1000:6180000:0:0:0:",		# World Movies
"70" : "1:0:1:FAA:4:1000:6180000:0:0:0:",		# ESPN
"41" : "1:0:1:BB9:3:1000:6180000:0:0:0:",		# FOX Sports 1
"42" : "1:0:1:BBA:3:1000:6180000:0:0:0:",		# FOX Sports 2
"25" : "1:0:1:7D5:2:1000:6180000:0:0:0:",		# FOX Sports 3
"87" : "1:0:1:138F:5:1000:6180000:0:0:0:",		# FUEL TV
"223" : "1:0:1:2EE3:C:1000:6180000:0:0:0:",		# NG Adventure
"45" : "1:0:1:BC8:3:1000:6180000:0:0:0:",		# Sky Racing
"65" : "1:0:1:FA5:4:1000:6180000:0:0:0:",		# Animal Planet
"427" : "1:0:1:791F:1F:1000:6180000:0:0:0:",    # BBC Knowledge
"88" : "1:0:1:1390:5:1000:6180000:0:0:0:",		# CI
"225" : "1:0:1:2EE5:C:1000:6180000:0:0:0:",		# Disc Health
"229" : "1:0:1:2EE9:C:1000:6180000:0:0:0:",		# Disc Science
"231" : "1:0:1:2EEB:C:1000:6180000:0:0:0:",		# Disc Travel
"27" : "1:0:1:7D7:2:1000:6180000:0:0:0:",		# Discovery
"29" : "1:0:1:7D9:2:1000:6180000:0:0:0:",		# History
"28" : "1:0:1:7D8:2:1000:6180000:0:0:0:",		# Nat Geo
"50" : "1:0:1:BC2:3:1000:6180000:0:0:0:",		# Boomerang
"31" : "1:0:1:7DB:2:1000:6180000:0:0:0",     # Cartoon
"12" : "1:0:1:3F4:1:1000:6180000:0:0:0:",		# CBeebies
"11" : "1:0:1:3F3:1:1000:6180000:0:0:0:",		# Disney
"21" : "1:0:1:7D1:2:1000:6180000:0:0:0:",		# Nickelodeon
"230" : "1:0:1:2EEA:C:1000:6180000:0:0:0:",		# Nick Jr
"326" : "1:0:1:426E:11:1000:6180000:0:0:0",    # Playhouse
"85" : "1:0:1:138D:5:1000:6180000:0:0:0:",		# Channel [V]
"221" : "1:0:1:2EE1:C:1000:6180000:0:0:0:",		# Channel [V]2
"226" : "1:0:1:2EE6:C:1000:6180000:0:0:0",    # Country Music
"90" : "1:0:1:1392:5:1000:6180000:0:0:0:",		# MAX
"89" : "1:0:1:1391:5:1000:6180000:0:0:0:",		# MTV
"83" : "1:0:1:138B:5:1000:6180000:0:0:0:",		# VH1
"171" : "1:0:1:2333:9:1000:6180000:0:0:0",    # A-PAC
"81" : "1:0:1:1389:5:1000:6180000:0:0:0:",		# BBC Wld news
"64" : "1:0:1:FA4:4:1000:6180000:0:0:0:",		# Bloomberg
"191" : "1:0:1:271B:A:1000:6180000:0:0:0:",		# CNBC
"69" : "1:0:1:FA9:4:1000:6180000:0:0:0:",     # CNN
"224" : "1:0:1:2EE4:C:1000:6180000:0:0:0:",		# Eurosportnews
"63" : "1:0:1:FA3:4:1000:6180000:0:0:0:",		# FOX News
"49" : "1:0:1:BC1:3:1000:6180000:0:0:0:",		# FoxSportsNews
"47" : "1:0:1:BBF:3:1000:6180000:0:0:0:",		# Sky Business
"84" : "1:0:1:138C:5:1000:6180000:0:0:0:",		# Sky News
"66" : "1:0:1:FA6:4:1000:6180000:0:0:0:",     # Weather

}

class SaveProgramme:
	def __init__(self, cachePath=""):
		debug("> SaveProgramme().__init__")

		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.configSaveProgramme = ConfigSaveProgramme()

		debug("< SaveProgramme().__init__")

	def getName(self):
		return self.name

	def saveMethod(self):
		return SAVE_METHOD_CUSTOM
		
	def isConfigured(self):
		return self.configSaveProgramme.checkValues()

	############################################################################################################
	def config(self, reset=True):
		debug("> config() reset=%s" % reset)
		try:
			if reset:
				self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				serverIP = self.configSaveProgramme.getValue(mytvGlobals.config.KEY_SMB_IP)
				serverUser = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_USER)
				serverPwd = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PASS)
				self.preRecMins = int(self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PRE_REC))
				self.postRecMins = int(self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_POST_REC))
				self.isEnigma = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_IS_ENIGMA)

				# URLs
				if serverUser and serverPwd:
					self.URL_BASE = 'http://%s:%s@%s/' % (serverUser,serverPwd,serverIP)
				elif serverUser:
					self.URL_BASE = 'http://%s@%s/' % (serverUser,serverIP)
				else:
					self.URL_BASE = 'http://%s/' % (serverIP)
				if not self.isEnigma:
					self.URL_TIMER_CREATE = self.URL_BASE + "addTimerEvent?type=regular&ref=$REF&start=$TIME" \
											"&duration=$DUR$&channel=$CHNAME&descr=$TITLE"
					self.URL_TIMER_DELETE = self.URL_BASE + "deleteTimerEvent?&ref=$REF&start=$STIME" \
											"&type=$TYPE&force=yes"
					self.URL_TIMER_LIST = self.URL_BASE + 'body?mode=controlTimerList'
				else:
					self.URL_BASE += 'web/'
# sampe 'Enigma 2' Dreambox  URL
# http://192.168.0.3/web/wap/timeradd?justplay=0&syear=2008&smonth=9&sday=16&shour=16&smin=25&eyear=2008&emonth=9&eday=16&ehour=18&emin=25
# &sRef=1%3A134%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM+BOUQUET+&name=Name+of++Prog&description=Description+of+Program&afterevent=0&disabled=0
# &deleteOldOnSave=0&command=add&save=Add%2FSave
#URL=http://192.168.1.3/web/timeraddbyeventid?sRef=1%3A0%3A1%3AFA5%3A4%3A1000%3A6180000%3A0%3A0%3A0%3A&eventid=2563&justplay=0
#URL=http://192.168.1.3/web/timeradd?sRef=1:0:1:FA5:4:1000:6180000:0:0:0:&begin=1238798640&end=1238802240&name=%20Testing%20123&description=&afterevent=3&eit=0&disabled=0&justplay=0&repeated=0&channelOld=&beginOld=0&endOld=0&eventID0&deleteOldOnSave=0
					self.URL_TIMER_CREATE = self.URL_BASE + "timeradd?sRef=$REF" \
											"&begin=$SMIN&end=$EMIN&name=$TITLE&description=" \
											"&afterevent=3&eit=0&disabled=0&justplay=0&repeated=0&channelOld=&beginOld=0&endOld=0&eventID0&deleteOldOnSave=0"
					self.URL_TIMER_DELETE = self.URL_BASE + "wap/timerdelete?&ref=$REF&begin=$STIME&end=$ETIME"
					self.URL_TIMER_LIST = self.URL_BASE + 'wap/timerlist.html'

				debug("dreambox URL_BASE=" + self.URL_BASE)
				debug("dreambox URL_TIMER_LIST=" + self.URL_TIMER_LIST)
				debug("dreambox URL_TIMER_CREATE=" + self.URL_TIMER_CREATE)
				debug("dreambox URL_TIMER_DELETE=" + self.URL_TIMER_DELETE)
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success

	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme.run()")
		success = False

		chid = channelInfo[TVChannels.CHAN_ID]
		ref = self.lookupREF(chid)
		if ref:
			currentTime = time.mktime(time.localtime())
			chName = channelInfo[TVChannels.CHAN_NAME]
			title = cleanPunctuation(programme[TVData.PROG_TITLE])
			startTimeSecs = int(programme[TVData.PROG_STARTTIME]) - (self.preRecMins * 60)
			endTimeSecs = int(programme[TVData.PROG_ENDTIME])+ (self.postRecMins * 60)
			durSecs = int(endTimeSecs - startTimeSecs)

			if endTimeSecs <= currentTime:
				messageOK(__language__(801),__language__(802), title)			# prog already finished
			else:
				# create final URL
				if not self.isEnigma:
					url = self.URL_TIMER_CREATE.replace('$REF', ref) \
							.replace('$TIME', str(startTimeSecs)) \
							.replace('$DUR', str(durSecs)) \
							.replace('$CHNAME', chName) \
							.replace('$TITLE', title)
				else:
					startTime_tm = time.localtime(startTimeSecs)
					endTime_tm = time.localtime(endTimeSecs)
					title += "_" + time.strftime("%Y%m%d", startTime_tm)
					url = self.URL_TIMER_CREATE.replace('$REF', ref) \
							.replace('$SYEAR', str(startTime_tm.tm_year)) \
							.replace('$SMONTH', str(startTime_tm.tm_mon)) \
							.replace('$SDAY', str(startTime_tm.tm_mday)) \
							.replace('$SHOUR', str(startTime_tm.tm_hour)) \
							.replace('$SMIN', str(startTimeSecs)) \
							.replace('$EYEAR', str(endTime_tm.tm_year)) \
							.replace('$EMONTH', str(endTime_tm.tm_mon)) \
							.replace('$EDAY', str(endTime_tm.tm_mday)) \
							.replace('$EHOUR', str(endTime_tm.tm_hour)) \
							.replace('$EMIN', str(endTimeSecs)) \
							.replace('$TITLE', title)

				doc = fetchURL(url)
				success = self.checkServerResult(doc)
				
				# give option to browse to playback recording file if being recorded now
				if success and startTimeSecs <= currentTime and xbmcgui.Dialog().yesno(self.name, "Play recording now?"):
					smbPath = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PLAYBACK_SMB)
					if not smbPath:
						messageOK(self.name,"LiveTV SMB path missing.","Use SaveProgramme setup to configure it.")
					else:
						fn = xbmcgui.Dialog().browse(1, "Playback File:", "files", ".ts", False, False, smbPath)
						debug("LiveTV fn=%s" % fn)
						if fn and fn != smbPath:
							xbmc.Player().play(fn)
							xbmc.executebuiltin("xbmc.ActivateWindow('video')")
					
		debug("< SaveProgramme.run() success=%s" % success)
		return success

	############################################################################################################
	# Called from myTV: Delete given timer
	############################################################################################################
	def deleteTimer(self, timer):
		debug("> SaveProgramme().deleteTimer()")
		success = False

		msgTitle = "%s: %s" % (__language__(511), self.name)
		delURL = timer[ManageTimers.REC_DEL_URL]
		if not self.isConfigured():
			messageOK(msgTitle, __language__(828))	# failed
		elif not delURL:
			messageOK(msgTitle, "Programme delete URL missing from timer!")
		else:
			# DELETE TIMER ON SERVER
			dialogProgress.create(msgTitle, __language__(821))	# deleting timer

#			startTimeSecs = timer[ManageTimers.REC_STARTTIME]
#			chName = timer[ManageTimers.REC_CHNAME]
#			durSecs = timer[ManageTimers.REC_DUR]
#			progName = timer[ManageTimers.REC_PROGNAME]
#			type = timer[ManageTimers.REC_PROG_ID]	# not really progID

			doc = fetchURL(delURL)
			dialogProgress.close()
			success = self.checkServerResult(doc)

		debug("< SaveProgramme().deleteTimer() success=%s" % success)
		return success

	############################################################################################################
	# method that can be called from myTV directly to fetch remote Timers files.
	############################################################################################################
	def getRemoteTimers(self):
		debug("> SaveProgramme().getRemoteTimers()")

		timers = self.getTimers()

		debug("< SaveProgramme().getRemoteTimers()")
		return timers

	############################################################################################################
	def getTimers(self):
		debug("> SaveProgramme().getTimers()")
		timersList = None		# unassigned

		dialogProgress.create(self.name, __language__(824))
		doc = fetchURL(self.URL_TIMER_LIST)
		if doc:
			if not self.isEnigma:
				timersList = self.getTimersOld(doc)
			else:
				timersList = self.getTimersEnigma(doc)
			debug("Count of timers found=%s" % len(timersList))

		dialogProgress.close()
		debug("< SaveProgramme().getTimers()")
		return timersList	# None is error, [] is empty, otherwise contains data

	############################################################################################################
	def getTimersOld(self, doc):
		debug("> getTimersOld()")
		timersList = []

		regex = "editTimerEvent\(\"ref=(.*?)start=(\d+)duration=(\d+)channel=(.*?)&descr=(.*?)&type=(\d+)\".*?(off|on|trans)"
		startStopStrList = [
							['Recurring Timer Events', 'One-time Timer Events'],
							['One-time Timer Events','</table']
							]
		for startStr, endStr in startStopStrList:
			matches = parseDocList(doc, regex, startStr, endStr)
			# found, extract details
			for match in matches:
				try:
					if len(match) != 7:
						debug("rec too short %s " % match)
						continue

					# ignore OFF entries (red cross)
					state = match[6]
					if state == 'off':
						continue

					pid = match[0]
					chID = self.lookupCHID(ref)
					if not chID:
						continue
					startTimeSecs = int(match[1])
					durSecs = int(match[2])
					chName = decodeEntities(match[3]).strip()
					title = decodeEntities(match[4]).strip()
					type = match[5].strip()
					delURL = self.URL_TIMER_DELETE.replace('$REF', pid) \
								.replace('$STIME',str(startTimeSecs)) \
								.replace('$TYPE',type)

					timersList.append([startTimeSecs, chID, durSecs, chName, title, delURL, pid])
					if DEBUG:
						print timersList[-1]
				except:
					handleException("getTimersOld()")

		debug("< getTimersOld()")
		return timersList


	############################################################################################################
	def getTimersEnigma(self, doc):
		debug("> getTimersEnigma()")
		timersList = []

		regex = '<font color="#000000">(.*?)<.*?timeredit.html.*?sRef=(.*?)&.*?begin=(\d+).*?end=(\d+).*?name=(.*?)&'
		matches = findAllRegEx(doc, regex)
		# found, extract details
		for match in matches:
			try:
				if len(match) != 5:
					debug("rec too short %s " % match)
					continue

				chName = match[0]
				pid = match[1]
				chID = self.lookupCHID(ref)
				if not chID:
					continue
				startTimeSecs = int(match[2])
				endTimeSecs = int(match[3])
				durSecs = endTimeSecs - startTimeSecs
				title = decodeEntities(match[4]).strip()
				delURL = self.URL_TIMER_DELETE.replace('$REF', pid) \
							.replace('$STIME', str(startTimeSecs)) \
							.replace('$ETIME', str(endTimeSecs))

				timersList.append([startTimeSecs, chID, durSecs, chName, title, delURL, pid])
				if DEBUG:
					print timersList[-1]
			except:
				handleException("getTimersEnigma()")

		debug("< getTimersEnigma()")
		return timersList


	# lookup REF from CHID
	def lookupREF(self, chid):
		try:
			value = REF_CODES[chid]
		except:
			value = ''
		debug("lookupREF() chid=%s ref=%s"% (chid, value))
		return value

	# find CHID from REF
	def lookupCHID(self, ref):
		# cant search a dict by value, so extract values as list then find it
		try:
			refList = REF_CODES.values()
			chidIDX = refList.index(ref)
			chidList = REF_CODES.keys()
			value = chidList[chidIDX]
		except:	# not found
			value = ''
		debug("lookupCHID() ref=%s chid=%s" % (ref, value))
		return value

	# check on returning html for errors
	def checkServerResult(self, result):
		debug("> checkServerResult()")
		success = False
		if not result or result == -1:
			messageOK("Failed.","No result returned from server.")
		elif result.find("success") <= 0:
			messageOK("Failed.","Unsuccessful message returned from server.")
		else:
			success = True
		debug("< checkServerResult() success=%s " % success)
		return success


############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_DREAMBOX'

		# CONFIG KEYS
		self.KEY_USER = 'user'
		self.KEY_PASS = 'pwd'
		self.KEY_PRE_REC = 'pre_rec'
		self.KEY_POST_REC = 'post_rec'
		self.KEY_IS_ENIGMA = 'isEnigma'
		self.KEY_PLAYBACK_SMB = 'playback_smb'

		self._makeDefaultConfigData()

		debug("< ConfigSaveProgramme().init()")

	def _makeDefaultConfigData(self):
		# try and make PLAYBACK_SMB default based on SMB_IP
		defaultUser = 'root'
		defaultPwd = 'dreambox'
		defaultIP = mytvGlobals.config.getSMB(mytvGlobals.config.KEY_SMB_IP)
		if not defaultIP:
			defaultIP = '192.168.1.100'
		defaultPlayback = 'smb://%s:%s@%s/media/hdd/movie/' % (defaultUser, defaultPwd, defaultIP)
	
		self.configData = [
			[mytvGlobals.config.KEY_SMB_IP, __language__(812), defaultIP, KBTYPE_IP],
			[self.KEY_USER,__language__(805), defaultUser, KBTYPE_ALPHA],
			[self.KEY_PASS,  __language__(806), defaultPwd, KBTYPE_ALPHA],
			[self.KEY_PRE_REC, __language__(835), '1', KBTYPE_NUMERIC],
			[self.KEY_POST_REC, __language__(836), '1', KBTYPE_NUMERIC],
			[self.KEY_IS_ENIGMA, "Is Model Enigma2?", False, KBTYPE_YESNO],
			[self.KEY_PLAYBACK_SMB, 'LiveTV SMB Path:', defaultPlayback, KBTYPE_ALPHA]
			]

	def reset(self):
		debug("ConfigSaveProgramme().reset()")
		self._makeDefaultConfigData()
		configOptionsMenu(self.CONFIG_SECTION, self.configData, __language__(534))

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		for data in self.configData:
			key = data[0]
			value = self.getValue(key)			# key
			if key == self.KEY_PASS or key == self.KEY_USER:			# user/pwd not reqd
				continue
			if value in (None,""):
				debug("missing value for mandatory key=%s" % key)
				success = False
				break

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getValue(self, key):
		if key in(mytvGlobals.config.KEY_SMB_PATH, mytvGlobals.config.KEY_SMB_IP, mytvGlobals.config.KEY_SMB_FILE):
			return mytvGlobals.config.getSMB(key)
		else:
			return mytvGlobals.config.action(self.CONFIG_SECTION, key)
