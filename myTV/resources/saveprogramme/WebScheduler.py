############################################################################################################
#
# Save Programme - Custom script called from myTV 'Save Programme' menu option.
#
# Creates and sends commands to DVB Web Scheduler  (http://dvb-ws.sourceforge.net/)
# And lets you watch live TV recordings
# 
#   DVB Web Scheduler will record to its default path.
#
# 1.0 Original Idea/Code By Alfiegerner, with futher code modifications by BigBellyBilly
# 03/05/06 - Updated to only pass Channel/Programme to run().
# 18/12/06 - Fix: a couple of bugs
# 03/05/07 - GUI configurable
# 27/05/07 - Completly re-written - Thanks to ozNick for invaluable assistance with this..
# 24/08/07 - Removed ReplaceWindow() after playback finished
# 11/09/07 - Replaced fetchFancyURL() with fetchCookieURL() (which itself now uses urllib.FancyURLopener())
# 12/05/08 - Updated for myTv v1.18
#############################################################################################################

import sys, urllib, xbmc, xbmcgui, os, string, datetime, time, re
from string import replace, lower
from mytvLib import *
from bbbGUILib import *
import mytvGlobals
from smbLib import parseSMBPath, getSMBFileSize, smbConnect

__language__ = sys.modules["__main__"].__language__

################################################################################################
class SaveProgramme:

	NAME = 	os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
	
	def __init__(self, cachePath=""):
		debug("SaveProgramme().__init__")

		self.cache = cachePath
		self.channelList = []
		self.EPG_FILENAME = cachePath + 'WebScheduler_schedules_$DATE.xml'
		self.BASE_URL = '/servlet/EpgDataRes'
#		self.SCHEDULE_URL = self.BASE_URL + '?action=12&xml=1'					# get ALL schedules
		self.NOWNEXT_URL = '/?&xml=1'
		self.SCHEDULE_URL = '/servlet/KBScheduleDataRes?start=0&show=1000&filter=0&xml=1'
		self.SCHEDULE_HTML_URL = '/servlet/ScheduleDataRes'						# HTML scrape
		self.SCHEDULE_LOG_URL = '/servlet/KBScheduleDataRes?action=09&xml=1&id='
		self.ACTION_URL = '/servlet/KBScheduleDataRes?action=%s&id=%s'
		self.SYSTEM_URL = '/servlet/SystemDataRes?action=02'
		self.rssparser = RSSParser2()
		self.preRecSecs = None
		self.postRecSecs = None
		self.ACTION_QUERY = '04'
		self.ACTION_STOP = '06'
		self.ACTION_DELETE = '05'
		self.ACTION_SYSTEM = '02'
		self.configSaveProgramme = ConfigSaveProgramme()

	def getName(self):
		return self.NAME

	def isConfigured(self):
		return self.configSaveProgramme.checkValues()

	def saveMethod(self):
		return SAVE_METHOD_CUSTOM
		
	############################################################################################################
	def config(self, reset=True):
		debug("> config() reset=%s" % reset)
		try:
			if reset:
				self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				self.SMB = self.configSaveProgramme.getValue(mytvGlobals.config.KEY_SMB_PATH)
				self.IP = self.configSaveProgramme.getValue(mytvGlobals.config.KEY_SMB_IP)
				self.PORT = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PORT)
				self.SERVER = "http://%s:%s" % (self.IP, self.PORT)
				self.USE_LIVE_TV = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_USE_LIVE_TV)
				self.LIVE_TITLE_FLAG = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_LIVE_TITLE_FLAG)
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success

	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme().run()")
		success = False
		title = ''
		filename = ''

		# get programme information
		chName = channelInfo[TVChannels.CHAN_NAME]
		title = programme[TVData.PROG_TITLE]
		schedLink = programme.get(TVData.PROG_SCHEDLINK,'')
		if not schedLink:
			messageOK(self.NAME, "Programme Add Link missing!", title, chName)
			debug("< SaveProgramme.run() failed")
			return False

		# prog start/end time in secs
		currentTime = time.mktime(time.localtime())
		startTimeSecs = programme[TVData.PROG_STARTTIME]
		endTimeSecs = programme[TVData.PROG_ENDTIME]

		# If we are recording a program thats already started, we
		# want to check if a recording is currently running and offer
		# the chance to stop it.
		self.stopAllRecordings()
		if startTimeSecs <= currentTime and self.USE_LIVE_TV:
			playProg = True
		else:
			playProg = False

		# record prog
		debug("do record prog")
		logTitle = ''
		schedID = ''
		url = self.SERVER + schedLink
		dialogProgress.update(0, __language__(819))					# setting rec
		logTitle = searchRegEx(schedLink, '&name=(.*?)&')			# get log title
		if logTitle:
			debug("OLD WS, have a logtitle, modify title with live flag")
			# replace &name=<title> with modified title containing LIVE_TITLE_FLAG
			if self.LIVE_TITLE_FLAG:									# append title tag
				logTitle = logTitle + self.LIVE_TITLE_FLAG
				reobj = re.compile('&name=.+?&', re.IGNORECASE+re.DOTALL)
				url = re.sub(reobj, "&name="+logTitle+'&', url)			# replace with new log title
		else:
			debug("NEW WS - no logtitle")
#					schedID = self.parseURLSchedID(schedLink)
			logTitle = title

		# SEND REC URL
		debug("send rec url...")
		if fetchCookieURL(url, encodeURL=False):
			success = True
		else:
			messageOK(self.NAME, __language__(809))
			schedID = ''

		# play prog
		if success and playProg:
			if xbmcgui.Dialog().yesno(self.NAME, __language__(807)):
				debug("do playProg")
				schedID,status = self.getXMLSchedIDByTitle(title)			# using orig title name
#				schedID = self.getLogSchedID(logTitle)						# using url parsed title name
				if schedID:
					filename = self.getPlaybackFilename(schedID)
					if filename:
						self.playFile(filename)

		debug("< SaveProgramme.run() success=%s" % success)
		return success


	############################################################################################################
	def parseURLSchedID(self, url):
		schedID = searchRegEx(url, 'id=([-]*\d+)')
		debug("parseURLSchedID() " + schedID)
		return schedID

	############################################################################################################
	# use xbmc built in cmd to playback a file
	############################################################################################################
	def playFile(self, filename):
		debug("> playFile() filename=" + filename)
		success = False

		remote, remoteInfo = smbConnect(self.IP, self.SMB)
		if remote:
			domain,user,password,pcname,share,dirPath = remoteInfo

			MIN_FILE_SZ = 3072		# 1024 - 1mb, 4096 - 4mb ...
			file_size = 0
			retryCount = 1
			MAX_RETRYS = 50			# failsafe to ensure loop quits if filesize doesn't increase
			dialogProgress.update(0, __language__(820))					# playback
			while file_size < MIN_FILE_SZ and retryCount < MAX_RETRYS:
				retryCount += 1
				file_size = getSMBFileSize(remote, remoteInfo, filename)
				if file_size < MIN_FILE_SZ:
					if file_size == 0: file_size = 0
					dialogProgress.update(int(retryCount*100/MAX_RETRYS), \
										"Waiting for file creation ...", filename, \
										"%sKb / %sKb" % (file_size, MIN_FILE_SZ) )
					time.sleep(2)

			dialogProgress.close()
			if file_size > 0:
				play_command = "%s%s" % (self.SMB, filename)
				if playMedia(play_command):
					xbmc.executebuiltin('XBMC.ActivateWindow(2005)')	# WINDOW_FULLSCREEN_VIDEO, 2005
					success = True
			else:
				messageOK(self.NAME, __language__(811), filename)
		debug("< playFile() success=%s" % success)
		return success


	############################################################################################################
	# stop the current recording on server
	############################################################################################################
	def stopAllRecordings(self):
		debug("> stopAllRecordings()")
		success = True

		rssItems = self.getSchedulesXML()
		for rssItem in rssItems:
			# look for running or waiting items
			status = rssItem.getElement("schStatus")
			status2 = rssItem.getElement("itemStatus")
			if self.isRunning(status) or self.isRunning(status2):
				# is running, attempt to STOP
				id = rssItem.getElement("id")	# no ID item
				if not id:
					id = rssItem.getElement("schedule")["id"]
				if not id:
					continue
				name = rssItem.getElement("schName")
				ch = rssItem.getElement("schChannel")
				if xbmcgui.Dialog().yesno(__language__(822), name, ch, status):
					try:
						# if a multi item ID, append index=0, otherwise they all get deleted
						if searchRegEx(name,'(\(.\d+\))'):
							param = "&index=0"
						else:
							param = ""
						self.sendAction(self.ACTION_STOP, id, param, waitsecs=2)
						self.sendAction(self.ACTION_DELETE, id, param, waitsecs=2)
					except:
						messageOK("Stop Recording Exception!","Unable to stop recording", name, ch)
						break

		debug("< stopAllRecordings() success: %s" % success)
		return success

	############################################################################################################
	def isRunning(self, text):
		if text:
			return (find(text,'Running') != -1 or find(text,'Starting') != -1 or find(text,'retry') != -1)
		else:
			return False

#	############################################################################################################
#	def getLogSchedID(self, title=''):
#		debug("> getLogSchedID() %s " % title)
#		schedID = ''
#
#		# sub all no-alpha chars for '-'
#		findTitle = ''
#		for ch in title:
#			if not ch.isalpha():
#				findTitle += '-'
#			else:
#				findTitle += ch
#
#		debug("findTitle=%s" % findTitle)
#		# get new schedule
#		dialogProgress.update(0, "Finding Schedule ID (LogFile) ...", findTitle)
#		MAX_RETRYS = 3
#		retryCount = 0
#		regex = '<schName>%s.*?</.*?id=([-]\d+)' % findTitle
#		while not schedID and retryCount < MAX_RETRYS:
#			debug("asking server for schedules... retry=%s" % retryCount)
#			time.sleep(2)
#			retryCount += 1
#			doc = fetchCookieURL(self.SERVER + self.SCHEDULE_URL)
#			if doc:
#				schedID = searchRegEx(doc, regex ,re.MULTILINE+re.IGNORECASE+re.DOTALL)
#				if not schedID:
#					dialogProgress.update(int((retryCount*100)/MAX_RETRYS))
#				else:
#					debug("XML found schedID=%s" % schedID)
#
#		# if still no schedID, examine ScheduleDataRes for it.
#		if not schedID:
#			debug("no schedID, examine ScheduleDataRes for it")
#			schedules = self.getSchedulesHTML()
#			for schedule in schedules:
#				try:
#					startTimeSecs, chID, durSecs, chName, progName, delURL = schedule
#					if find(progName, findTitle) != -1:
#						schedID = self.parseURLSchedID(delURL)
#						break
#				except:
#					print "bad schedule unpack", schedule
#
#		else:
#			messageOK(self.NAME, 'Schedule ID not found!', findTitle)
#
#		dialogProgress.close()
#		debug("< getLogSchedID() schedID=%s" % schedID)
#		return schedID


	############################################################################################################
	def getPlaybackFilename(self, schedID):
		debug("> getPlaybackFilename() schedID=%s" % schedID)

		filename = ""
		if schedID:
			# need a loop to wait for log file to be created - WS seems a bit slow in creating it
			# get File Name from WS LOG FILE using schedID in url
			MAX_RETRYS = 25
			retryCount = 0
			msg = "Waiting for Playback filename ..."
			dialogProgress.update(0, msg)
			url = self.SERVER+self.SCHEDULE_LOG_URL+schedID
			while not filename and retryCount < MAX_RETRYS:
				retryCount += 1
				doc = fetchCookieURL(url)
				if doc:
					filename = searchRegEx(doc, 'File Name : (.*?)<',re.MULTILINE+re.IGNORECASE+re.DOTALL)
					if not filename:
						debug("filename not found")
						time.sleep(2)
						dialogProgress.update(int((retryCount*100)/MAX_RETRYS), msg)

			if not filename:
				messageOK(self.NAME,'Playback file not found!', filename)

		debug("< getPlaybackFilename() filename=%s" % filename)
		return filename.strip()

	############################################################################################################
	def setFilename(self, startTimeSecs, title):
		date = time.strftime("%Y%m%d%H%M",time.localtime(startTimeSecs))
		filename = "%s_%s" % (title,date)
		debug("setFilename() filename="+filename)
		return filename

	############################################################################################################
	def setChannelList(self, channelList):
		self.channelList = channelList

	############################################################################################################
	# find CHID from Channel Name
	# search in supplied datasource channellist [chID, name, other]
	############################################################################################################
	def lookupCHID(self, chName):
		chID = ''
		searchChName = chName.upper()
		for ch in self.channelList:
			listChName = ch[1].upper()
			if listChName[0] == '*':			# hidden channel indicator, do compare not including that
				listChName = listChName[1:]
			if listChName == searchChName:
				chID = ch[0]
				break

#		if not chID:
#			messageOK("Channel Name to ID Failed!",chName)
		return chID

	############################################################################################################
	def getSchedulesXML(self):
		debug("> getSchedulesXML()")

		rssItems = []
		dialogProgress.update(0, "Fetching Schedules XML ...")
		if self.rssparser.feed(url=self.SERVER+self.SCHEDULE_URL):
			feedElementDict = { "schedule" : ["id"],
							"schName" : [],
							"schStatus" : [],
							"schChannel" : [],
							"schDur" : [],
							"itemStatus" : [],
							"id" : [],
							"action" : []
						}

			rssItems = self.rssparser.parse("schedule", feedElementDict)

		debug("< getSchedulesXML()")
		return rssItems

	############################################################################################################
	# FOR GIVEN ID FIND STATUS
	# return None  - ID not found
	# return True  - Found and running
	# return False - Found and NOT running
	############################################################################################################
	def getSchedulesXMLByID(self, schedID):
		debug("> getSchedulesXMLByID() schedID=%s" % schedID)
		isRunning = None
		if schedID:
			doc = self.sendAction(self.ACTION_QUERY, schedID, '&xml=1')
			isRunning = self.isRunning(doc)
		debug("< getSchedulesXMLByID() isRunning=%s" % isRunning)
		return isRunning

	############################################################################################################
	# FOR GIVEN TITLE, FIND ID and STATUS using NOWNEXT XML
	############################################################################################################
	def getXMLSchedIDByTitle(self, title):
		debug("> getXMLSchedIDByTitle()")
		schedID = ''
		status = ''

		dialogProgress.update(0, "Finding Schedule ID (XML) ...", title)
		MAX_RETRYS = 3
		retryCount = 0
		regex = '<name>%s.*?<id>(.*?)</.*?<status>(.*?)<' % title
		while not schedID and retryCount < MAX_RETRYS:
			debug("asking server for Now / next schedules... retry=%s" % retryCount)
			retryCount += 1
			doc = fetchCookieURL(self.SERVER+self.NOWNEXT_URL)
			if doc:
				matches = findAllRegEx(doc, regex)
				if matches:
					schedID = matches[0][0]
					status = matches[0][1]
				else:
					debug("no matches to title found")
					time.sleep(2)

			if not schedID:
				dialogProgress.update(int((retryCount*100)/MAX_RETRYS))
				time.sleep(1)

		debug("< getXMLSchedIDByTitle() schedID=%s status=%s" % (schedID, status))
		return schedID, status

	############################################################################################################
	# fetch schedules from remote PC adjusting start/end times according to preset time padding
	############################################################################################################
	def getSchedulesHTML(self, preRecSecs=0, postRecSecs=0):
		debug("> getSchedulesHTML() preRecSecs=%s postRecSecs=%s" % (preRecSecs, postRecSecs))

		timersList = []
		dialogProgress.create(self.NAME, __language__(824))
		doc = fetchCookieURL(self.SERVER + self.SCHEDULE_HTML_URL)
		if doc:
			debug("process schedules")
			currentTimeSecs = time.mktime(time.localtime())
			year = time.strftime("%Y", time.localtime())
			rows = parseDocList(doc, '(<tr.*?</tr)', '>Pending Schedules<', '</table')
			if not rows:
				debug("no pending schedules found")
			else:
				regexSingle = "</td>.*?['\"]>(.*?)<.*?<td.*?['\"]>(.*?)</td.*?<td.*?['\"]>(.*?)</td.*?<td.*?['\"]>(\d+)min</td.*?<td.*?['\"]>(.*?)</td.*?href=['\"].*?(/servlet/ScheduleDataRes\?action=0[49].*?id=.*?)['\"]"
				regexParent = ".*?\(M\d+\)<.*?<td.*?['\"]>.*?<.*?<td.*?['\"]>(.*?)<"
				startDate = ''
				for row in rows:
					title = ''
					startDateTime = ''
					durMins = ''
					chName = ''
					delURL = ''
					
					# check for PARENT
					match = searchRegEx(row, regexParent,re.MULTILINE+re.IGNORECASE+re.DOTALL)
					if match:
						startDate = match
						continue

					# find CHILDREN or SINGLE
					matches = findAllRegEx(row, regexSingle)
					if not matches:
						debug("no CHILDREN or SINGLES found for PARENT")
					else:
						for match in matches:
							try:
								progName = cleanHTML(match[0])
								if match[2] != '&nbsp;':	# single
									startDate = match[2]

								startDateTime = "%s %s %s" % (startDate, year, cleanHTML(match[1]))
								durMins = match[3]
								chName = match[4]
								delURL = match[5]
								chID = self.lookupCHID(chName)
							except:
								debug("bad single rec %s" % match)
								continue

						if chID and progName and startDateTime and durMins and chName and delURL:
							ftmDate = time.strptime(startDateTime,"%a, %d %b %Y %I:%M %p")
							# remove timer pre/post padding to give actual prog duration
							durSecs = (60 * int(durMins)) - preRecSecs - postRecSecs
							startTimeSecs = time.mktime(ftmDate) + preRecSecs	# remove pre padding
							endTimeSecs = startTimeSecs + durSecs				# actual end time w/o padding
#							print chID, chName, startDateTime, startTimeSecs, endTimeSecs, durSecs, progName, delURL
							# only save if timer not finished
							if endTimeSecs > currentTimeSecs:
								timersList.append([startTimeSecs, chID, durSecs, chName, progName, delURL])

		dialogProgress.close()
		debug("< getSchedulesHTML() timersList sz=%s" % len(timersList))
		return timersList

	############################################################################################################
	# method that can be called from myTV directly to fetch remote Timers files.
	############################################################################################################
	def getRemoteTimers(self):
		debug("> SaveProgramme().getRemoteTimers()")

#		timers = self.getTimersWithPadding()			# will get padding first, then call getSchedules
		timers = self.getSchedulesHTML()				# timers without padding removed

		debug("< SaveProgramme().getRemoteTimers()")
		return timers

	############################################################################################################
	# Find preset time padding, then get schedules
	############################################################################################################
#	def getTimersWithPadding(self):
#		debug("> SaveProgramme().getTimersWithPadding()")
#		timersList = None
#
#		dialogProgress.create(self.NAME, "")
#		if self.preRecSecs == None or self.postRecSecs == None:
#			# fetch PRE & POST recording buffer mins
#			dialogProgress.update(0, "Finding Timer Padding Mins ...")
#			debug("download pre & post rec mins")
#			doc = fetchCookieURL(self.SERVER + self.SYSTEM_URL)
#			if doc:
#				# find padding using one of two possible re matches
#				reList = ("Schedule.buffer.end[\"'] value=[\"'](\d+).*?Schedule.buffer.start[\"'] value=[\"'](\d+)",
#						  "Schedule.buffer.start[\"'] value=[\"'](\d+).*?Schedule.buffer.end[\"'] value=[\"'](\d+)")
#				for regex in reList:
#					matches = findAllRegEx(doc, regex)
#					try:
#						self.postRecSecs = int(matches[0][0]) * 60
#						self.preRecSecs = int(matches[0][1]) * 60
#						break
#					except: pass
#
#				if self.preRecSecs == None or self.postRecSecs == None:
#					messageOK(self.NAME,"Could not get Timer Padding Mins.","Unable to calculate true schedule times.")
#
#		if self.preRecSecs != None and self.postRecSecs != None:
#			timersList = self.getSchedulesHTML(self.preRecSecs, self.postRecSecs)
#
#		dialogProgress.close()
#		debug("< SaveProgramme().getTimersWithPadding()")
#		return timersList


	############################################################################################################
	# Called from myTV: Delete given timer
	############################################################################################################
	def deleteTimer(self, timer):
		debug("> SaveProgramme().deleteTimer()")
		success = False

		msgTitle = "%s: %s" % (__language__(511), self.NAME)
		# check its status
		progName = timer[ManageTimers.REC_PROGNAME]
#		schedID,status = self.getXMLSchedIDByTitle(progName)					# using orig title name
		delURL = timer[ManageTimers.REC_DEL_URL]
		schedID = self.parseURLSchedID(delURL)									# find using id from delURL
		if not schedID:
			messageOK(self.NAME, "Required SchedID not found!", progName, delURL)
			debug("< SaveProgramme().deleteTimer()")
			return False

		# DO STOP IF RUNNING, LOOP UNTIL STOPPED
		# loop while running, to resend STOP
		canDelete = True
		dialogProgress.create(self.NAME)
		while self.getSchedulesXMLByID(schedID):
			if xbmcgui.Dialog().yesno(self.NAME, __language__(822)):				# stop recording ?
				self.sendAction(self.ACTION_STOP, schedID, waitsecs=2)
			else:
				canDelete = False

		# DELETE TIMER ON SERVER
#		if canDelete and xbmcgui.Dialog().yesno(self.NAME, __language__(823)):		# delete timer ?
		if canDelete:		# delete timer ?
			self.sendAction(self.ACTION_DELETE, schedID, waitsecs=2)
			success = True
		dialogProgress.close()
		debug("< SaveProgramme().deleteTimer() success=%s" % success)
		return success


	############################################################################################################
	def sendAction(self, action, schedID, param='', waitsecs=0):
		debug("> sendDeleteAction() action=%s schedID=%s" % (action, schedID))
		dialogProgress.update(0, "Sending action %s" % action)
		url = self.SERVER + (self.ACTION_URL % (action, schedID)) + param
		doc = fetchCookieURL(url, encodeURL=False)
		if waitsecs:
			time.sleep(waitsecs)
		debug("< sendDeleteAction()")
		return doc

	############################################################################################################
	def playbackFromFile(self, id=''):
		debug("> playbackFromFile() id=%s" % id)
		filename = ''
		menuList = [xbmcgui.ListItem(__language__(500), "")]			# exit
		# get list of running progs 
		rssItems = self.getSchedulesXML()
		for rssItem in rssItems:
			# look for running items
			status = rssItem.getElement("schStatus")
			status2 = rssItem.getElement("itemStatus")
			if self.isRunning(status) or self.isRunning(status2):
				name = rssItem.getElement("schName")
				ch = rssItem.getElement("schChannel")
				dur = rssItem.getElement("schDur")
				menuList.append(xbmcgui.ListItem(name, "%s, %smins" % (ch,dur)))

		if menuList > 1:
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(503), rows=len(menuList), width=670, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList)
			if selectedPos > 0:
				rssItem = rssItems[selectedPos-1]
				id = rssItem.getElement("id")	# no ID item
				if not id:
					id = rssItem.getElement("schedule")["id"]
				if id:
					dialogProgress.create(__language__(503))
					filename = self.getPlaybackFilename(id)
					if filename:
						self.playFile(filename)
					dialogProgress.close()
		debug("< playbackFromFile() filename=" + filename)
		return filename

	############################################################################################################
	# ask for recording repeat type. Selecting EXIT cancels setting recording
	############################################################################################################
	def getRepeatType(self):
		debug("> getRepeatType()")
		menuList = [__language__(500), 'Once','Daily','Weekly','Monthly','Week Day']
		selectDialog = DialogSelect()
		selectDialog.setup('Select Repeat Type', width=300, rows=len(menuList), panel=mytvGlobals.DIALOG_PANEL)
		selectedPos,action = selectDialog.ask(menuList)

		# selectedPos will match type value (eg Daily == 1)
		if selectedPos <= 0:
			type = None			# cancel
		else:
			type = str(selectedPos-1)
		debug("< getRepeatType() type=%s" % type)
		return type


############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_WEBSCHEDULER'

		# CONFIG KEYS
		self.KEY_PORT = 'port'
		self.KEY_USE_LIVE_TV = 'use_live_tv'
		self.KEY_LIVE_TITLE_FLAG = 'live_title_flag'

		self.configData = [
			[mytvGlobals.config.KEY_SMB_PATH, __language__(817), '', KBTYPE_SMB],
			[mytvGlobals.config.KEY_SMB_IP,__language__(812),'192.168.1.100',KBTYPE_IP],
			[self.KEY_PORT,__language__(813),'8429',KBTYPE_NUMERIC],
			[self.KEY_USE_LIVE_TV,__language__(814),False, KBTYPE_YESNO],
			[self.KEY_LIVE_TITLE_FLAG, __language__(816),'-XBMC-',KBTYPE_ALPHA]
			]

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("ConfigSaveProgramme.reset()")
		title = "%s - %s" % (SaveProgramme.NAME, __language__(534))
		configOptionsMenu(self.CONFIG_SECTION, self.configData,  title)

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")
		success = True

		# check mandatory keys have values
		mandatoryKeys = (mytvGlobals.config.KEY_SMB_IP,self.KEY_PORT,self.KEY_USE_LIVE_TV,self.KEY_LIVE_TITLE_FLAG)
		for key in mandatoryKeys:
			value = self.getValue(key)
			if value in (None, ''):
				debug("missing value for mandatory key=%s" % key)
				success = False

		# check special conditions
		if self.getValue(self.KEY_USE_LIVE_TV) and not self.getValue(mytvGlobals.config.KEY_SMB_PATH):
			debug("live tv requested but missing smb")
			success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getValue(self, key):
		if key in(mytvGlobals.config.KEY_SMB_PATH, mytvGlobals.config.KEY_SMB_IP, mytvGlobals.config.KEY_SMB_FILE):
			return mytvGlobals.config.getSMB(key)
		else:
			return mytvGlobals.config.action(self.CONFIG_SECTION, key)
