############################################################################################################
# Save Programme - Custom script called from myTV 'Save Programme' menu option.
#
# Creates and sends commands to SageTV webserver
# Fetches scheduled timers at startup and manages its own timers list.
#
# 25/07/2007 - First attempt
# 07/09/2007 - Second attempt
#############################################################################################################

import sys, urllib, xbmc, xbmcgui, os, string, re, time
from mytvLib import *
from bbbGUILib import *
from string import replace

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

################################################################################################
#                                                                                              #
#                                                                                              #
################################################################################################
class SaveProgramme:
	def __init__(self, cachePath=""):
		debug("> SaveProgramme().__init__")

		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.configSaveProgramme = ConfigSaveProgramme()

		debug("< SaveProgramme().__init__")

	def getName(self):
		return self.name

	def isConfigured(self):
		return self.configSaveProgramme.checkValues()

	def saveMethod(self):
		return SAVE_METHOD_CUSTOM

	############################################################################################################
	def config(self, reset=True):
		debug("> config() reset=%s" % reset)
		try:
			if reset:
				success = self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				IP = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_IP)
				PORT = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PORT)
				USER = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_USER)
				PASS = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PASS)
				PRE_REC = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PRE_REC)
				POST_REC = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_POST_REC)

				self.BASE_URL = 'http://%s:%s@%s:%s/sage/' % (USER,PASS,IP,PORT)
				self.CHECK_URL = self.BASE_URL + 'DetailedInfo?AiringId=$PID'
				self.CANCEL_URL = self.BASE_URL + 'ManualRecord?command=CancelRecord&AiringId=$PID'
				self.RECORD_URL = self.BASE_URL + 'Manualrecord?command=Record&AiringId=$PID' + \
										'&startpad=' + PRE_REC + \
										'&StartPadOffsetType=earlier&endpad=' + POST_REC + \
										'&EndPadOffsetType=later'
				self.SCHEDULES_URL = self.BASE_URL + 'RecordingSchedule'
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success


	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme().run()")
		success = False

		pid = programme[TVData.PROG_SCHEDLINK]
		if not pid:
			messageOK(self.name, "Programme PID missing!", title, chName)
		else:
			chName = channelInfo[TVChannels.CHAN_NAME]
			title = programme[TVData.PROG_TITLE]
			startTimeSecs = programme[TVData.PROG_STARTTIME]
			actionURL = self.CHECK_URL.replace('$PID',pid)
			doc = fetchURL(actionURL)
			if doc:
				doRecord = True
				if searchRegEx(doc, '(img src="record)'):			# schedule found
					if xbmcgui.Dialog().yesno(__language__(834) , __language__(822)):	# Already Sched., stop rec?
						actionURL = self.CANCEL_URL.replace('$PID',pid)
						doc = fetchURL(actionURL)
						if not doc:
							doRecord = False
					else:
						doRecord = False

				if doRecord:
					endTimeSecs = programme[TVData.PROG_ENDTIME]
					progDateLong = time.strftime('%a %d/%m/%y %H:%M %p', time.localtime(startTimeSecs))
					progEndTimeLong = time.strftime('%H:%M %p', time.localtime(endTimeSecs))
					durSecs = int(endTimeSecs - startTimeSecs)
					durMins = int(durSecs /60)

					# SET RECORDING
					dialogProgress.update(0, __language__(819))					# setting rec
					doc = fetchURL(self.RECORD_URL.replace('$PID',pid))
					if doc:
						success = True

		debug("< SaveProgramme.run() success=%s" % success)
		return success

	############################################################################################################
	# return: None is error, [] is empty, otherwise contains data
	def getTimers(self):
		debug("> SaveProgramme().getTimers()")
		timersList = None

		dialogProgress.create(self.name, __language__(824))
		doc = fetchURL(self.SCHEDULES_URL)
		if doc:	
			timersList = []
			regex = 'DetailedInfo.*?=(\d+)">(.*?)<.*?datecell.*?crop">(.*?)<br/>(\d+:\d+ .M).*?(\d+:\d+ .M).*?ChannelID=(\d+).*?title="(.*?)"'
			matches = parseDocList(doc, regex, 'epgcell','[Show Options]')
			if matches:
				currentTimeSecs = time.mktime(time.localtime())
				year = time.strftime("%Y", time.localtime())
				MATCHES_SZ = len(matches)
				for matchCount, match in enumerate(matches):
#					print match
					try:
						pid = match[0]
						title = cleanHTML(decodeEntities(match[1]))
						startDate = match[2]
						startTime = match[3]
						endTime = match[4]
						chID = match[5]
						chName = cleanHTML(decodeEntities(match[6]))
					except:
						debug("bad sized rec %s" % match)
						continue

					# manadatory values
					if not pid or not chID or not startDate or not startTime or not endTime or not chName:
						continue

					delURL = self.CANCEL_URL.replace('$PID',pid)
					# format startTime 
					startDateTime = "%s %s %s" % (startDate, year, startTime)
					fmtStartDateTime = time.strptime(startDateTime,"%a, %b %d %Y %I:%M %p")	# Fri, Sep 7 04:20 PM
					startTimeSecs = time.mktime(fmtStartDateTime)

					# format endTime
					endDateTime = "%s %s %s" % (startDate, year, endTime)
					fmtEndDateTime = time.strptime(endDateTime,"%a, %b %d %Y %I:%M %p")		# Fri, Sep 7 05:20 PM
					endTimeSecs = time.mktime(fmtEndDateTime)

					# ensure prog ends after start. eg 11:50 PM to 12:10 AM
					if endTimeSecs < startTimeSecs:
						endTimeSecs += 86400		# add 24 hours

					durSecs = int(endTimeSecs - startTimeSecs)

					# only save if not timer not finished
					if endTimeSecs > currentTimeSecs:
						timersList.append([startTimeSecs, chID, durSecs, chName, title, delURL, pid])
					if DEBUG:
						print timersList[-1]

					dialogProgress.update(int(matchCount*100/MATCHES_SZ), title)

		dialogProgress.close()
		debug("< SaveProgramme().getTimers()")
		return timersList


	############################################################################################################
	# method that can be called from myTV directly to fetch remote Timers files.
	############################################################################################################
	def getRemoteTimers(self):
		debug("> SaveProgramme().getRemoteTimers()")

		timers = self.getTimers()

		debug("< SaveProgramme().getRemoteTimers()")
		return timers

	############################################################################################################
	# Called from myTV: Delete given timer
	############################################################################################################
	def deleteTimer(self, timer):
		debug("> SaveProgramme().deleteTimer()")
		success = False

		msgTitle = "%s: %s" % (__language__(511), self.name)
		progID = timer[ManageTimers.REC_PROG_ID]
		if not self.isConfigured():
			messageOK(msgTitle, __language__(828))	# failed
		elif not progID:
			messageOK(msgTitle, "progID missing from timer!")
		else:
			# DELETE TIME ON SERVER
			dialogProgress.create(msgTitle, __language__(821))	# deleting timer

			deleteURL = self.CANCEL_URL.replace('$PID',progID)
			doc = fetchURL(deleteURL)

			dialogProgress.close()
			if doc:
				success = True
			else:
				messageOK(msgTitle, __language__(828),  __language__(829))	# failed, check server

		debug("< SaveProgramme().deleteTimer() success=%s" % success)
		return success


############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_SAGETV'

		# CONFIG KEYS
		self.KEY_IP = 'ip'
		self.KEY_PORT = 'port'
		self.KEY_USER = 'user'
		self.KEY_PASS = 'pass'
		self.KEY_PRE_REC = 'pre_rec'
		self.KEY_POST_REC = 'post_rec'

		self.configData = [
			[self.KEY_IP,__language__(812),'192.168.2.4',KBTYPE_IP],
			[self.KEY_PORT, __language__(813), '2880', KBTYPE_NUMERIC],
			[self.KEY_USER, __language__(805), 'sage', KBTYPE_ALPHA],
			[self.KEY_PASS, __language__(806), 'freypwd', KBTYPE_ALPHA],
			[self.KEY_PRE_REC,__language__(835),'2',KBTYPE_NUMERIC],
			[self.KEY_POST_REC,__language__(836),'2',KBTYPE_NUMERIC]
			]

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("ConfigSaveProgramme().reset()")
		configOptionsMenu(self.CONFIG_SECTION, self.configData, __language__(534),400)

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		# check mandatory keys have values
		for data in self.configData:
			key = data[0]
			value = self.getValue(key)
			if not value:
				debug("missing value for mandatory key=%s" % key)
				success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getValue(self, key):
		return config.action(self.CONFIG_SECTION, key)
