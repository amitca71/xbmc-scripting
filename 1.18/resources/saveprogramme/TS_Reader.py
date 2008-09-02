############################################################################################################
#
# Save Programme for TS_READER - Custom script called from myTV 'Save Programme' menu option.
#
#
# NOTES:
# The class must be called 'SaveProgramme' that accepts Channel and Programme classes.
# Must have a run() function that returns success as True or False.
#
#
# CHANGLOG:
# 14/02/07 - Created.
#
############################################################################################################

import xbmcgui,xbmc,time, re, telnetlib, time
from string import replace, split
from bbbGUILib import *
from mytvLib import *

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

DISEQC_91 = '91.0W'
DISEQC_82 = '82.0W'
TSREADER_DISEQC = { DISEQC_91 : '2',
					DISEQC_82 : '1' }
TSREADER_DP = { DISEQC_82 : '11250',
				DISEQC_91 : '14350' }

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
				success = self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				self.tsrControlIP = self.configSaveProgramme.getIP()
				self.tsrControlPort = self.configSaveProgramme.getPort()
				self.is22khz = self.configSaveProgramme.is22khz()
				self.playbackOutput = self.configSaveProgramme.getPlaybackOutput()
				self.streamFile = self.configSaveProgramme.getStreamFile()
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success
		
	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme.run()")
		success = False
		
		chid = channelInfo[TVChannels.CHAN_ID]
		chName = channelInfo[TVChannels.CHAN_NAME]
		title = programme[TVData.PROG_TITLE]
		desc = programme[TVData.PROG_DESC]

		# parse desc to extract tune options DIRECTION, DP, TPS, unknown value?
		matches = searchRegEx(desc, '.+?\|(.+?) (.+?) (.+?) ')
		if not matches:
			messageOK("TS READER Tune Error","Unable to parse tuning from description")
			debug("< SaveProgramme.run() failed")
			return False

		direction = matches.group(1)
		dp = matches.group(2).replace('.','')
		tps = matches.group(3)
		someValue = matches.group(4)

		diseqcPort = TSREADER_DISEQC[direction]
		if tps == 'L':
			lnbf = TSREADER_DP[direction]
		else:
			lnbf = TSREADER_DP[DISEQC_82]

		tuneCommand = "TUNE %s %s %s %s %s %s\r" % (dp, tps, someValue, lnbf, self.is22khz, diseqcPort)

		# send cmds to server via telnet
		serverResp = '200 TSReader version 2.7.44 Control Server'
		restartedResp = '308 Source restarted'
		decodeResp = '311 Table decoding complete'
		selectedResp = '300 Program selected'
		playbackResp = '302 Playback starting'
		
		programNumber = split(chid, '-')[0]
		programCommand = 'PROGRAM ' + str(programNumber) + '\r'
		playCommand = 'PLAY ' + self.playbackOutput + '\r'
		quitCommand = 'QUIT\r'
		stallCommand = 'STALL 300\r'

		tn = telnetlib.Telnet(self.tsrControlIP, self.tsrControlPort)
		if not tn:
			messageOK("Telnet Negotiation Failed","Failed to connect.","Check IP & Port")
			debug("< SaveProgramme.run() connection failed")
			return False

		dialogProgress.update(0, "Telnet Negotiation", __language__(500))	# wait...
		MAX_OPS = 6
		opCount = 1

		try:
			tn.read_until(serverResp, timeout=5)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Send Tune command ...")
			opCount += 1

			tn.write(tuneCommand)
			tn.read_until(restartedResp, timeout=5)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Send Stall command ...")
			opCount += 1

			tn.write(stallCommand)
			tn.read_until(decodeResp, timeout=60)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Send Program command ...")
			opCount += 1

			tn.write(programCommand)
			tn.read_until(selectedResp, timeout=5)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Send Play command ...")
			opCount += 1

			tn.write(playCommand)
			tn.read_until(playbackResp, timeout=5)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Send Quit command ...")
			opCount += 1

			tn.write(quitCommand)
			tn.close()
			time.sleep(2)
			dialogProgress.update(int(opCount*100.0/MAX_OPS), "Telnet Complete")
			success = True
		except:
			messageOK("Telnet Exception","Unexpected end of connection.")
		else:
			dialogProgress.close()
			if fileExist(self.streamFile):
				if playMedia(self.streamFile):
					xbmc.executebuiltin('XBMC.ActivateWindow(2005)')	# WINDOW_FULLSCREEN_VIDEO, 12005
			else:
				messageOK(self.name,"Playback stream file is missing.", self.streamFile)

		debug("< run() success=%s" % success)
		return success
		

############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_TSREADER'

		# CONFIG KEYS
		self.KEY_IP = 'ip'
		self.KEY_PORT = 'port'
		self.KEY_IS22KHZ = 'is22khz'
		self.KEY_PLAYBACK_OUTPUT = 'playback_output'
		self.KEY_STREAM_FILE = 'stream_file'

		self.configData = [
			[self.KEY_IP,__language__(812),'192.168.0.2',KBTYPE_IP],
			[self.KEY_PORT,__language__(813),'8429',KBTYPE_NUMERIC],
			[self.KEY_IS22KHZ,"22Khz?",False, KBTYPE_YESNO],
			[self.KEY_PLAYBACK_OUTPUT, "Playback Output Type:",'VLC2',KBTYPE_ALPHA],
			[self.KEY_STREAM_FILE, __language__(833), 'g:\\VideoLAN.strm', KBTYPE_ALPHA]
			]

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("ConfigSaveProgramme.reset()")
		configOptionsMenu(self.CONFIG_SECTION, self.configData, __language__(534))

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		# check mandatory keys have values
		for data in self.configData:
			key = data[0]
			value = self.getValue(key)		# key
			if value in (None,""):
				debug("missing value for mandatory key=%s" % key)
				success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getIP(self):
		return self.getValue(self.KEY_IP)
	def getPort(self):
		return self.getValue(self.KEY_PORT)
	def is22khz(self):
		return (self.getValue(self.KEY_IS22KHZ) == __language__(350))	# yes
	def getPlaybackOutput(self):
		return self.getValue(self.KEY_PLAYBACK_OUTPUT)
	def getStreamFile(self):
		return self.getValue(self.KEY_STREAM_FILE)

	def getValue(self, key):
		return config.action(self.CONFIG_SECTION, key)
