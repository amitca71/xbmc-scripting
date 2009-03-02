############################################################################################################
# TV Data source: PC
# Notes:
# Listing files are created on your PC, from wherever you like, this datasource simply fetches them from PC.
#
# Filenames required:
# AVAILABLE CHANNELS FILE:
#   Filename should be called: Channels_PC.dat
#   Each line in this file should be comma delimited consisting of 2 fields:
#       chid,ch name   EG. 104,SomeChannelName
#
# INDIVIDUAL CHANNEL LISTING FILES:
#   Each filename should be named using this format: <chid>_<yyyymmdd>.dat
#   Each record is in the form of a python 'dict' element.
#   It can contain some or all the fields, but must contain 'start' 'end' 'title'
#
# eg.
# {'end': 1218411000.0, 'title': 'In The Night Garden', 'start': 1218409200.0, 'schedurl': 'my_url', 'genre': 'Family', 'subtitle': 'Igglepiggle Looks For Upsy Daisy And Follows Her Bed', 'desc': 'In The Night Garden'}
#
# Each file should contain a single days worth of programming per single channel.
#
# REVISION HISTORY:
# 03/02/06 Created
# 11/08/08 Updated for myTV - added setup via GUI - required record format has changed. see above
############################################################################################################

from mytvLib import *
import xbmcgui, re, time, os, smb
from string import split
from smbLib import ConfigSMB, smbConnect, smbFetchFile, parseSMBPath, isNewSMBFile
import mytvGlobals

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

SAMBA_FILENAME = '$CHID_$DATE.dat'		# DONT CHANGE THIS !

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache, "Channels_"+ self.name + ".dat")
		self.remote = None
		self.isConfigured = False

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channelList = []
		if self.isConfigured:
			# fetch file if not exists
			if not fileExist(self.CHANNELS_FILENAME):
				if self.getRemoteFile(os.path.basename(self.CHANNELS_FILENAME)):
					channelList = readChannelsList(self.CHANNELS_FILENAME)
			else:
				# read in [channel id, channel name]
				channelList = readChannelsList(self.CHANNELS_FILENAME)

		debug("< ListingData.getChannels()")
		return channelList

	# download channel data file, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		progList = []

		# create Channel from data file
		if self.isConfigured:
			if self.getRemoteFile(os.path.basename(filename)):
				progList = loadChannelFromFile(filename)

		return progList

	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)
		CONFIG_SECTION = 'DATASOURCE_' + self.getName()
		self.remote = None
		self.remoteInfo = None
		self.smbIP = None
		self.smbPath = None
		self.smbRemoteFile = None
		self.connectionError = False

		configSMB = ConfigSMB(mytvGlobals.config, CONFIG_SECTION, self.name, fnDefaultValue=SAMBA_FILENAME)
		if reset:
			configSMB.ask()

		smbDetails = configSMB.checkAll(silent=True)
		if smbDetails:
			self.smbIP, self.smbPath, self.smbRemoteFile = smbDetails
			self.isConfigured = True

		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
		

	############################################################################################################
	# create a SMB connection and fetch remote file
	def getRemoteFile(self, remoteFilename, localFilename='', fetchAlways=True):
		debug("> ListingData().getRemoteFile() fetchAlways=%s" % fetchAlways)
		downloaded = False

		if not self.connectionError:
			if not self.remote:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			if self.remote and self.remoteInfo:
				if not localFilename:
					localFilename = os.path.join(self.cache, remoteFilename)

				if fetchAlways or isNewSMBFile(self.remote, self.remoteInfo, localFilename, remoteFilename):
					downloaded = smbFetchFile(self.remote, self.remoteInfo, localFilename, remoteFilename, silent=False)
					if not downloaded:
						self.connectionError = True
			else:
				self.connectionError = True

		debug("< ListingData.getRemoteFile() downloaded=%s connectionError=%s" % (downloaded, self.connectionError))
		return downloaded
