############################################################################################################
# TV Data source: XMLTV
# Notes:
# On the remote PC use xmltv.exe 'tv_grab_<country_code>.txt' to create an xmltv file (eg xmltv.xml)
#
# REVISION HISTORY:
# 10/09/07 - Created (from pc_tsreader)
# 11/08/08 - Updated for myTV v1.18
# 07/01/09 - Fix. channels regex error
############################################################################################################

import time, os, smb
from mytvLib import *
from smbLib import smbConnect, smbFetchFile, isNewSMBFile, parseSMBPath
import mytvGlobals

__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("ListingData().__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.localSMBFile = os.path.join(cache, 'xmltv.xml')
		self.isConfigured = False
		self.checkedRemoteFileToday = False
		self.connectionError = False

		# smb vars
		self.remote = None
		self.remoteInfo = None
		self.smbIP = None
		self.CHANNELS_RE = ''
		self.PROGS_RE = ''
		self.smbPath = None
		self.smbRemoteFile = None

	def getName(self):
		return self.name

	############################################################################################################
	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	############################################################################################################
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channelList = []
		if self.isConfigured:
			# fetch file if not exists
			if not fileExist(self.CHANNELS_FILENAME):
				# if no local XML file, fetch from SMB
				if not fileExist(self.localSMBFile):
					self.getRemoteFile()

				# extract data from file using regex - this is specific to this file format
				data = readFile(self.localSMBFile)
				if data:
					matches = findAllRegEx(data, self.CHANNELS_RE)
					channelList = writeChannelsList(self.CHANNELS_FILENAME, matches)
			else:
				# read in [channel id, channel name]
				channelList = readChannelsList(self.CHANNELS_FILENAME)

		debug("< ListingData.getChannels()")
		return channelList


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("> ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		progList = []
		if self.isConfigured:
			if not self.checkedRemoteFileToday:
				self.getRemoteFile(False) # fetch only if newer
				self.checkedRemoteFileToday = True

			if fileExist(self.localSMBFile):
				progList = self.createChannelFiles(chID, fileDate)
			else:
				debug("file missing " + self.localSMBFile)

		debug("< ListingData.getChannel()")
		return progList

	############################################################################################################
	# create a SMB connection and fetch remote file
	############################################################################################################
	def getRemoteFile(self, fetchAlways=True):
		debug("> ListingData().getRemoteFile() fetchAlways=%s" % fetchAlways)
		downloaded = False

		if not self.connectionError:
			if not self.remote or not self.remoteInfo:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			if self.remote and self.remoteInfo:
				if fetchAlways or isNewSMBFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile):
					downloaded = smbFetchFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile, silent=False)
					if downloaded == None:
						self.connectionError = True
			else:
				self.connectionError = True

		debug("< ListingData.getRemoteFile() downloaded=%s connectionError=%s" % (downloaded, self.connectionError))
		return downloaded


	# determine highest start date for any channel.
	# this will help prevent unnwanted processing when curr. date nearing end of
	# dates contained with XML
#	def findHeighestStartDate(self, data):
#		debug("> findHeighestStartDate() current self.highestDate="+str(self.highestDate))
#		regex = 'start=\"(\d\d\d\d\d\d\d\d)'
#		matches = findAllRegEx(data, regex)
#		if matches:
#			matches.sort()
#			lastMatch = int(matches[-1])			# get last in list
#			if lastMatch > self.highestDate:
#				self.highestDate = lastMatch
#		debug("< findHeighestStartDate() new self.highestDate="+str(self.highestDate))

		
	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	############################################################################################################
	def createChannelFiles(self, chID, searchDate):
		debug("> ListingData.createChannelFiles() chID=%s  searchDate=%s" % (chID, searchDate))

		progList = []
		dialogProgress.update(0, __language__(312))
		data = readFile(self.localSMBFile)
		if data:
			regex = self.PROGS_RE.replace('$DATE',searchDate).replace('$CHID',chID)
			matches = findAllRegEx(data, regex)
			for prog in matches:
				startDateTime = prog[0]
				title = decodeEntities(prog[1])

				# calc programme start time in secs since epoch based on programme date
				startTimeSecs = time.mktime(time.strptime(startDateTime,"%Y%m%d%H%M%S"))
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title
					} )

			if progList:
				progList = setChannelEndTimes(progList)		# update endtimes

		del data
		debug("< ListingData.createChannelFiles() progs count=%s" % len(progList))
		return progList

	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.getName()

		# CONFIG KEYS
		KEY_CHANNELS_RE = 'channels_re'
		KEY_PROGS_RE = 'progs_re'

		# Uncomment the ONE that works for your web server interface
		configData = [
			[KEY_CHANNELS_RE,"Channels Regex:", 'channel id="(.*?)".*?display-name.*?>(.*?)<', KBTYPE_ALPHA],
			[KEY_PROGS_RE,"Programme Regex:", 'start="($DATE\d\d\d\d\d\d).*?channel="$CHID".*?title.*?>(.*?)<', KBTYPE_ALPHA],
			[mytvGlobals.config.KEY_SMB_PATH, __language__(969), 'smb://user:pass@pcname/share/folder/', KBTYPE_SMB],	# remote path
			[mytvGlobals.config.KEY_SMB_FILE, __language__(977), 'xmltv.xml', KBTYPE_ALPHA]
			]

		def _check():
			self.CHANNELS_RE = mytvGlobals.config.action(CONFIG_SECTION, KEY_CHANNELS_RE)
			self.PROGS_RE = mytvGlobals.config.action(CONFIG_SECTION, KEY_PROGS_RE)
			self.smbPath = mytvGlobals.config.getSMB(mytvGlobals.config.KEY_SMB_PATH)
			self.smbIP = mytvGlobals.config.getSMB(mytvGlobals.config.KEY_SMB_IP)
			self.smbRemoteFile = mytvGlobals.config.getSMB(mytvGlobals.config.KEY_SMB_FILE)
			
			if self.CHANNELS_RE and self.PROGS_RE and self.smbPath and self.smbIP and self.smbRemoteFile:
				success = True
			else:
				success = False
			debug("_check() success=%s" % success)
			return success

		if reset:
			title = "%s - %s" % (self.name, __language__(976)) # __language__(534)
			configOptionsMenu(CONFIG_SECTION, configData, title)
		self.isConfigured = _check()

		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
