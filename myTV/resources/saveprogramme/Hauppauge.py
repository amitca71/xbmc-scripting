############################################################################################################
#
# Save Programme - Custom script called from myTV 'Save Programme' menu option.
#
# Creates a Windows XP 'Scheduled Task' command line suitable for a Hauppauge Nova-T PCI TV card.
# Channel codes are extracted from Hauppauge channel list file 'DigitalTV-t.lst'
# (file is usually found in "C:\Program Files\Hauppauge\WinTV NOVA\")
#
# NOTES:
# The class must be called 'SaveProgramme' that accepts Channel and Programme classes.
# Must have a run() function that returns success as True or False.
#
# Change the translation CHANNEL_CODE_NOVA to use the channel names -> haupp. card ID for your own
# datasource channel names. Haupp. IDs found in DigitalTV-t.lst
#
# CHANGLOG:
# 07/05/05	Changed - If programme scheduled within 1 min of start time, incr +2 mins
# 28/09/05	New. Support for Hauppauge WinTV200 - see comment below for setup instuctions
# 22/10/05	Updated Freeview channel ID numbers from 'DigitalTV-t.lst' for Nova-t FV card
# 11/05/06- Now configurable via GUI.
# 04/07/06 - Updated to use new config class
# 16/12/06 - Added new card type and changed config to cope.
# 29/05/08 - Updated for myTv v1.18
#
############################################################################################################

import xbmcgui, xbmc, time, re
from mytvLib import *
from bbbGUILib import *
from string import replace

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

# NOVA tv card
CHANNEL_CODES_NOVA = {
	'BBC1':'233A100A104A02580000', 
	'BBC 1':'233A100A104A02580000',
	'BBC2':'233A100A108A02620000',
	'BBC 2':'233A100A108A02620000',
	'ITV1':'233A2019205902000000',
	'ITV1 Yorkshire':'233A2019205902000000',
	'Channel 4':'233A201920C01FFE0000',
	'Five':'233A3002324217810000',
	'ITV2':'233A201920850B030000', 	
	'ITV 2':'233A201920850B030000',
	'BBC3':'233A100A10FF1FFF0000', 
	'BBC 3':'233A100A10FF1FFF0000',
	'BBC4':'233A400041C01FFF0000',
	'BBC 4':'233A400041C01FFF0000',
	'Sky Travel':'233A500056C0012D0000',
	'UKTV History':'233A5000570001910000',
	'E4':'233A201921001FFE0000',
	'More 4':'233A201920FA1FFE0000',
	'ABC1':'233A3002378018F10000',
	'The Hits':'233A6000644000650000',
	'TMF: The Music Factory':'233A6000648000C90000',
	'Cbeebies':'233A4000424000C90000',
	'ITV3':'233A2019207C0B860000',
	'ITV 3':'233A2019207C0B860000',
	'ITV4':'233A201920A10B540000',
	'ITV 4':'233A201920A10B540000',
	'Men & Motors':'233A600069C002590000',
	'E4 +1':'233A5000574001F50000',
	'E4+1':'233A5000574001F50000',
	'BBC News 24':'233A100A113F02800000',
	'Discovery Real Time':'233A30023B0019210000',
	'Discovery':'233A30023B4019310000',
	'Eurosport':'233A30023E8019D10000'
}

# WinTV2000 card
# this need completing - can anybody help with this ? NB the '-' is important
CHANNEL_CODES_WINTV2K = {
	'BBC1':'-c1',
	'BBC 1':'-c1',
	'BBC2':'-c2',
	'BBC 2':'-c2',
	'ITV1':'-c3',
	'ITV1 Yorkshire':'-c3',
	'Channel 4':'-c4',
	'Five':'-c5',
	'Een' : '-c1',                    # Skynet_BE
	'Ketnet_Canvas' : '-c2',          # Skynet_BE
	'VTM' : '-c3',                    # Skynet_BE
	'VT4' : '-c4',                    # Skynet_BE
	'Vijf TV' : '-c5',                # Skynet_BE
	'2BE' : '-c6',                    # Skynet_BE
	'Vitaya' : '-c7',                 # Skynet_BE
	'Nederland 1' : '-c9',            # Skynet_BE
	'Nederland 2' : '-c10',           # Skynet_BE
	'Nederland 3' : '-c11',           # Skynet_BE
	'Kanaal Z' : '-c1',               # Skynet_BE
	'JIM TV' : '-c13',                # Skynet_BE
	'TMF' : '-c14'                    # Skynet_BE

# an alternative Swedish TV channel to WinTV2000 tvcard code list
#	'SVT 1':'-c5',
#	'SVT 2':'-c7',
#	'TV3':'-c4',
#	'TV4':'-c3',
#	'Kanal 5':'-c9',
#	'TV8':'-c29',
#	'TV6':'-12',
#	'ZTV':'-c23',
#	'ViaSat Sport':'-c41',
#	'Eurosport':'-c11',
#	'discomix':'-Discovery MIX',
#	'Discovery':'-c32',
#	'ng':'-National',
#	'hallmark':'-Hallmark',
#	'tv1000':'-TV1000',
#	'tv1ka':'-Action',
#	'cplus':'-Canal +',
#	'cplusf1':'-C+ FILM1',
#	'cplusf2':'-C+ FILM2'
}

# DATE FORMAT
DATE_FORMAT = '%d/%m/%Y'			# normal(most countries)
#DATE_FORMAT = '%Y/%m/%d'			# required in Sweden

# These are the channel codes from the Hauppauge channel file 'DigitalTV-t.lst'
# Add/Change/Remove as required.
# There are multiple instances of some channel names as different DataSources use different channel names,

class SaveProgramme:
	def __init__(self, cachePath=""):
		debug("> SaveProgramme().__init__")

		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.configSaveProgramme = ConfigSaveProgramme()

		debug("< SaveProgramme().__init__")

	def getName(self):
		return self.name

	def saveMethod(self):
		return SAVE_METHOD_CUSTOM_SMB

	def isConfigured(self):
		return self.configSaveProgramme.checkValues()

	def config(self, reset=True):
		debug("> SaveProgramme.config() reset=%s" % reset)
		if reset:
			self.configSaveProgramme.reset()
		success = self.isConfigured()
		if success:
			self.isCardTypeNova = self.configSaveProgramme.isCardTypeNova()
			self.SCHTASKS = self.configSaveProgramme.getSchTaskCMD()
			self.channelCodes = self.configSaveProgramme.getChannelCodes()
			self.preRecMins = self.configSaveProgramme.getPreRecMins()
			self.postRecMins = self.configSaveProgramme.getPostRecMins()

		debug("< SaveProgramme.config() success=%s" % success)
		return success

	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme().run()")
		returnStr = False

		# get programme information
		chName = channelInfo[TVChannels.CHAN_NAME]
		title = cleanPunctuation(programme[TVData.PROG_TITLE]).encode('latin-1', 'replace')

		tvCode = self.lookupCode(chName)
		if tvCode:
			currentTimeSecs = time.mktime(time.localtime())
			startTimeSecs = programme[TVData.PROG_STARTTIME] - (self.preRecMins * 60)
			endTimeSecs = programme[TVData.PROG_ENDTIME]

			# Schedule Task wont run if prog already started. so make startTime current time.
			# Also ensure start time is not within 1 mins of current time.
			if startTimeSecs <= (currentTimeSecs + 60):
				startTimeSecs = currentTimeSecs	+120		# delay tobe 2 mins from currentTimeSecs

			startDate = time.strftime(DATE_FORMAT, time.localtime(startTimeSecs))
			startTime = time.strftime('%H:%M:%S', time.localtime(startTimeSecs))
			endTimeSecs += (self.postRecMins * 60)
			if self.isCardTypeNova:
				duration = int((endTimeSecs - startTimeSecs) /60)	# mins
				MIN_TIME = 3
			else:
				duration = int(endTimeSecs - startTimeSecs)			# secs
				MIN_TIME = 180

			# dont bother recording anything too short
			if duration < MIN_TIME:
				messageOK(__language__(801), __language__(803))
			else:
				# create return string
				fn = "%s_%s" % (title,startDate)
				returnStr = self.SCHTASKS.replace('$TITLE', title)
				returnStr = returnStr.replace('$DATE', startDate).replace('$TIME', startTime)
				returnStr = returnStr.replace('$DUR', str(duration)).replace('$TV', tvCode)
				returnStr = returnStr.replace('$FN', fn)

		debug("< SaveProgramme().run() %s" % returnStr)
		return returnStr


	# Lookup tv card channel code number based on channel name
	def lookupCode(self, chName):
		try:
			code = self.channelCodes[chName]
			debug("lookupCode() chName: %s -> Code: %s"  % (chName, code))
		except:
			messageOK("lookupCode() Channel Name to Record code Failed!", chName)
			code = ''
		return code


############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_HAUPPAUGE'

		self.CARD_TYPE_NOVA = 'NovaT'
		self.CARD_TYPE_WINTV2K = 'WinTV2K'
		self.CARD_TYPE_USB = 'Nova USB'

		self.KEY_CARD_TYPE = 'card_type'
		self.KEY_PATH_EXE = 'path_exe'
		self.KEY_PATH_REC = 'path_rec'
		self.KEY_USER = 'user'
		self.KEY_PASS = 'pwd'
		self.KEY_TR = 'tr'
		self.KEY_TR_PARMS = 'tr_parms'
		self.KEY_PRE_REC_MINS = 'pre_rec_mins'
		self.KEY_POST_REC_MINS = 'post_rec_mins'
		self.KEY_BASE_CMD = 'base_cmd'

		self.BASE_CMD = 'schtasks /create /TN "$TITLE" /SC ONCE /SD $DATE /ST $TIME '
		self.CARD_TR = {
				self.CARD_TYPE_NOVA : '/TR "\\"$EXE\\" /1 $TV \\"$REC$FN.mpg\\" $PARMS" /RU $USER /RP $PWD',
				self.CARD_TYPE_WINTV2K : '/TR "\\"$EXE\\" $TV -startr:\\"$REC$FN.mpg\\" $PARMS" /RU $USER /RP $PWD',
				self.CARD_TYPE_USB : '/TR "\\"$EXE\\" $TV -startr:\\"$REC$FN.mpg\\" $PARMS" /RU $USER /RP $PWD'
			}

		self.CARD_TR_PARMS = {
			self.CARD_TYPE_NOVA : 'MPG $DUR Stop 4000MB',
			self.CARD_TYPE_WINTV2K : '-ntod -qvcd -limit:$DUR -mute -exitr',
			self.CARD_TYPE_USB : '-ntod -qdef -limit:$DUR -mute -exitr'
			}

		self.CARD_TYPES = {
				self.CARD_TYPE_NOVA : "C:\\progra~1\\Hauppauge\\WinTV NOVA\\DVB-TV.exe",
				self.CARD_TYPE_WINTV2K : "C:\\progra~1\\WinTV\\WinTV2K.exe",
				self.CARD_TYPE_USB : "C:\\progra~1\\WinTV\\bgrecorder.exe"
				}

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("> ConfigSaveProgramme.reset()")

		origCardType = self.getValue(self.KEY_CARD_TYPE)
		options = self.CARD_TYPES.keys()
		dlg = DialogSelect()
		dlg.setup(__language__(831), rows=len(options), panel=DIALOG_PANEL, width=280)
		selectedPos, action = dlg.ask(options)
		if selectedPos < 0:
			return

		# reset other values that where dependant on cardtype
		cardType = options[selectedPos]
		if origCardType != cardType:
			config.action(self.CONFIG_SECTION, mode=ConfigHelper.MODE_REMOVE_SECTION)
			config.action(self.CONFIG_SECTION, self.KEY_CARD_TYPE, cardType, mode=ConfigHelper.MODE_WRITE)
		exePath = self.CARD_TYPES[cardType]
		tr = self.CARD_TR[cardType]
		tr_parms = self.CARD_TR_PARMS[cardType]

		configData = [
			[self.KEY_PATH_EXE,__language__(832), exePath, KBTYPE_ALPHA],
			[self.KEY_PATH_REC, __language__(833), "G:\\My Documents\\myTV\\", KBTYPE_ALPHA],
			[self.KEY_USER, __language__(805), "SYSTEM", KBTYPE_ALPHA],
			[self.KEY_PASS, __language__(806), "", KBTYPE_ALPHA],
			[self.KEY_BASE_CMD, __language__(837), self.BASE_CMD, KBTYPE_ALPHA],
			[self.KEY_TR, "TR:", tr, KBTYPE_ALPHA],
			[self.KEY_TR_PARMS, "TR Parms:", tr_parms, KBTYPE_ALPHA],
			[self.KEY_PRE_REC_MINS, __language__(835), "1", KBTYPE_NUMERIC],
			[self.KEY_POST_REC_MINS, __language__(836), "1", KBTYPE_NUMERIC]
			]

		configOptionsMenu(self.CONFIG_SECTION, configData, __language__(534), 700)
		debug("< ConfigSaveProgramme.reset()")


	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		# check mandatory keys have values
		mandatoryKeys = (self.KEY_CARD_TYPE, self.KEY_PATH_EXE, self.KEY_PATH_REC, \
						 self.KEY_PRE_REC_MINS, self.KEY_POST_REC_MINS, \
						 self.KEY_TR, self.KEY_TR_PARMS, self.KEY_BASE_CMD)
		for key in mandatoryKeys:
			value = self.getValue(key)
			if value in (None, ""):
				debug("missing value for mandatory key=%s" % key)
				success = False
				break

		# check special conditions
		if success:
			# CARD_TYPE_WINTV2K cardtype must have user/pass
			cardType = self.getValue(self.KEY_CARD_TYPE)
			if cardType == self.CARD_TYPE_WINTV2K:
				if not self.getValue(self.KEY_USER):
					success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getCardType(self):
		return self.getValue(self.KEY_CARD_TYPE)

	def getSchTaskCMD(self):
		debug("> getSchTaskCMD()")
		value = ""
		try:
			baseCMD = self.getValue(self.KEY_BASE_CMD) + ' '
			cardTYPE = self.getValue(self.KEY_CARD_TYPE)
			pathEXE = self.getValue(self.KEY_PATH_EXE)
			pathREC = self.getValue(self.KEY_PATH_REC)
			tr = self.getValue(self.KEY_TR)
			tr_parms = self.getValue(self.KEY_TR_PARMS)
			user = self.getValue(self.KEY_USER)
			pwd = self.getValue(self.KEY_PASS)

			value = baseCMD + tr.replace('$PARMS',tr_parms)
			value = value.replace('$EXE',pathEXE).replace('$REC',pathREC)
			value = value.replace('$USER',user).replace('$PWD',pwd)
		except:
			handleException("getSchTaskCMD()")
		debug("< getSchTaskCMD()")
		return value

	def isCardTypeNova(self):
		return (self.getValue(self.KEY_CARD_TYPE) == self.CARD_TYPE_NOVA)

	def getChannelCodes(self):
		if self.isCardTypeNova():
			return CHANNEL_CODES_NOVA
		else:
			return CHANNEL_CODES_WINTV2K

	def getPreRecMins(self):
		try:
			return int(self.getValue(self.KEY_PRE_REC_MINS))
		except:
			return 0

	def getPostRecMins(self):
		try:
			return int(self.getValue(self.KEY_POST_REC_MINS))
		except:
			return 0

	def getValue(self, key):
		value = config.action(self.CONFIG_SECTION, key)
		if value == None:
			value = ''
		return value

