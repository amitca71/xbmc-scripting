############################################################################################################
# TV Data source: 
# Notes:
# Pulls DM created day files from Dreambox Enigma2.
#
# Setup your DM to create the individual Day Filesusing a filename that matches that you specify in this
# datasource setup. (Setup on first run or throu Config menu)
#
# REVISION HISTORY:
# 20/02/09 - Created
############################################################################################################

import re, time, os, smb
from string import split
from mytvLib import *
from smbLib import ConfigSMB, smbConnect, smbFetchFile, listDirSMB
import mytvGlobals
from pprint import pprint

__language__ = sys.modules["__main__"].__language__

# DON'T CHANGE THESE UNLESS THEY NO LONGER MATCH
CHANNELS_REGEX = '^(\d+)=[1|2|3],(.*?)[,\n]'		# chID, chName
CHANNEL_REGEX = '^(\d+)###(.*?)###(.*?)###(.*?)$'	# starttimesecs (not used), display time, title, desc

class ListingData:
	def __init__(self, cache):
		debug("ListingData().__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.isConfigured = False
		self.checkedRemoteFileToday = False
		self.connectionError = False

		# smb vars
		self.remote = None
		self.remoteInfo = None
		self.smbPath = ""

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
				# fetch from SMB
				remoteFN = "/".join( [self.smbPath, self.DM_CONF_FILENAME] )
				localFN = os.path.join(self.cache, self.DM_CONF_FILENAME)
				response = xbmc.executehttpapi("FileCopy(%s,%s)" % (remoteFN, localFN))
				debug("httpapi response=%s" % response)

				# extract data from file using regex - this is specific to this file format
				data = readFile(localFN)
				if data:
					matches = parseDocList(data, CHANNELS_REGEX, "[channel_list]")
					if matches:
						matches.sort()
						channelList = writeChannelsList(self.CHANNELS_FILENAME, matches)
				deleteFile(localFN)
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

		if self.isConfigured and not self.connectionError and not self.checkedRemoteFileToday:

			# fetch all DM day files for chID
			dialogProgress.update(0, "Querying Dreambox ...", " ", " ")
			time.sleep(.2)
			remoteFileList = []
			response = xbmc.executehttpapi("GetDirectory(%s)" % self.smbPath)
			debug("httpapi response=%s" % response)
			if find(response,'Error') < 0:
				remoteFileList = response.split('<li>')
				MAX_COUNT = len(remoteFileList)
				debug("remoteFileList sz=%d" % MAX_COUNT)
#				if DEBUG:
#					pprint (remoteFileList)
			else:
				messageOK(self.name, __language__(138), self.smbPath)

			if remoteFileList:
				# fetch all DM data files we dont have mytv data files for
				fetchedDMDict = {}
				for count, remoteBMFilename in enumerate(remoteFileList):
					try:
						match = re.search(self.DM_FILENAME_REGEX, remoteBMFilename)
						if not match: continue
						fnChID = match.group(1)
						fnDate = match.group(2)

						channelFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, "%s_%s.dat" % (fnChID,fnDate)))
						if not fileExist(channelFN):
							remoteBMBasename = os.path.basename(remoteBMFilename.strip()) #.replace('+','%2B')
							localBMFilename = xbmc.makeLegalFilename(os.path.join(self.cache, "DM_%s_%s.dat" % (fnChID,fnDate)))
							percent = int( (count * 100.0) / MAX_COUNT )
							dialogProgress.update(percent, __language__(962), remoteBMBasename)

							response = xbmc.executehttpapi("FileCopy(%s,%s)" % (remoteBMFilename, localBMFilename))
							debug("httpapi response=%s" % response)
							if (response and find(response,"OK") >= 0):
								fetchedDMDict[channelFN] = localBMFilename
								self.createChannelFiles(localBMFilename, channelFN, fnDate)
								deleteFile(localBMFilename)
						else:
							debug("not downloaded, file already exists=" + channelFN)
					except:
						print str( sys.exc_info()[ 1 ] )
						print "except during remoteFilename=" + localBMFilename

				if fileExist(filename):
					progList = loadChannelFromFile(filename)

			self.checkedRemoteFileToday = True
		debug("< ListingData.getChannel() prog count=%d" % len(progList))
		return progList


	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	############################################################################################################
	def createChannelFiles(self, dataFN, channelFN, dataDate=""):
		debug("> ListingData.createChannelFiles() dataFN=%s dataDate=%s" % (dataFN, dataDate))

		progList = []
		data = readFile(dataFN)
		if data:
			# parse data records and save
			matches = findAllRegEx(data, CHANNEL_REGEX)
			for prog in matches:
#				print "rec secs=%s = %s" % (prog[0], time.localtime(int(prog[0])))

				dateTime = "%s %s" % (dataDate, prog[1])	# display time
				dateTime_t = time.strptime(dateTime, "%Y%m%d %H:%M:%S")
				startTimeSecs = float(time.mktime(dateTime_t))
#				print "filedate+displaysecs=%s = %s = %s" % (dateTime, dateTime_t, startTimeSecs)
				
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : decodeEntities(prog[2]),
						TVData.PROG_DESC : decodeEntities(prog[3])
					} )

			if progList:
				progList = setChannelEndTimes(progList)		# update endtimes
				saveChannelToFile(progList, channelFN)

		del data
		debug("< ListingData.createChannelFiles() progs count=%s" % len(progList))
		return progList

	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.getName()

		# CONFIG KEYS
		KEY_CHANNELS_FN = 'dm_channels_fn'
		KEY_DM_FN = 'dm_channel_fn'

		# Uncomment the ONE that works for your web server interface
		configData = [
			[KEY_CHANNELS_FN,"DM Channels Filename:", "australiasat-channel_list.conf", KBTYPE_ALPHA],
			[KEY_DM_FN,"DM Channel Day Filename:", "australiasat###(\d+).*?###(\d+)", KBTYPE_ALPHA],
			[mytvGlobals.config.KEY_SMB_PATH, __language__(969), '', KBTYPE_SMB]
			]

		def _check():
			self.DM_CONF_FILENAME = mytvGlobals.config.action(CONFIG_SECTION, KEY_CHANNELS_FN)
			self.DM_FILENAME_REGEX = mytvGlobals.config.action(CONFIG_SECTION, KEY_DM_FN)
			self.smbPath = mytvGlobals.config.getSMB(mytvGlobals.config.KEY_SMB_PATH)
			
			success = bool( self.smbPath and self.DM_CONF_FILENAME and self.DM_FILENAME_REGEX )
			debug("_check() success=%s" % success)
			return success

		if reset:
			title = "%s - %s" % (self.name, __language__(976)) # __language__(534)
			configOptionsMenu(CONFIG_SECTION, configData, title)
		self.isConfigured = _check()

		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured

