############################################################################################################
#
# Save Programme - Custom script called from myTV 'Save Programme' menu option.
#
# Creates a Windows XP 'Scheduled Task' command line suitable for a myTheater TV card.
# myTheater channel codes are translated from myTV channelID.
#
# NOTES:
# The class must be called 'SaveProgramme' that accepts Channel and Programme classes.
# Must have a run() function that returns success as True or False.
#
# 03/05/06 - Updated to only pass Channel/Programme to run().
# 11/05/06 - Updated. Config now done throu GUI.
# 22/08/06 - Updated: Uses new Config.
# 14/10/06 - Updated: CHANNEL_CODES changed from list to dict
############################################################################################################

import xbmcgui,xbmc,time, re
from mytvLib import *
import mytvGlobals
from string import replace

__language__ = sys.modules["__main__"].__language__


# NOTE: SETTINGS NOW SET VIA myTV AT FIRST RUN & CONFIG MENU

# These are the channel codes from the channel file.
# Add/Change/Remove as required.
# datasource chID  -> myTheater tv card channel code

#FRANCE datasource
CHANNEL_CODES = {
	'1' : '118', 	# TF1
	'2' : '53', 	# FRANCE 2
	'3' : '55', 	# FRANCE 3
	'4' : '1731', 	# CANAL PLUS
	'5' : '271', 	# ARTE
	'6' : '115', 	# M6
	'7' : '77', 	# FRANCE 5
	'8' : '632', 	# RTL9
	'9' : '1506', 	# TMC
	'10' : '74',	# FRANCE 4
#	'11' : '',	# DIRECT 8
	'12' : '2072', 	# LCP
#	'13' : '', 	# NRK 12
	'14' : '624', 	# NT1
	'15' : '172', 	# W9
	'16' : '3505', 	# bfm tv
	'17' : '2714', 	# EUROPE 2 TV
	'18' : '1061', 	# GULLI
	'19' : '3524' 	# I-TELE
}

# zap2it
"""
CHANNEL_CODES = {
"HIST":"2805",
"FUSE":"2808",
"G4":"2810",
"COURT":"2811",
"HBO-E":"2812",
"GLVSN":"2814",
"BET":"2815",
"BRAVO":"2816",
"ANIML":"2817",
"1F40":"2818",
"FOOD":"2819",
"GAME":"2820",
"ESNWS":"2821",
"ESPN2":"2822",
"MTV2":"2824",
"FLIX":"2825",
"TEN":"2826",
"PLBY":"2827",
"RAI":"2828",
"SITV":"2829",
"iWTHR":"2846",
"ITVG":"3108",
"ITVGV":"3109",
"NICK":"3110",
"FOXMW":"3112",
"CSNMA":"3113",
"FOXCN":"3114",
"FOXN":"3115",
"ALT1":"3116",
"PPV":"3117",
"NHL":"3118",
"NHL":"3119",
"NHL":"3120",
"NBA":"3121",
"MLB":"3122",
"WGN":"3123",
"RDRCT":"3142",
"A&E":"3143",
"CRDEX":"3144",
"CNN":"3145",
"HNN":"3146",
"HBO-W":"3147",
"SHOTO":"3148",
"FIESM":"3149",
"LATNS":"3150",
"WCIU":"2854",
"KDNL":"2855",
"KMOV":"2856",
"KSDK":"2857",
"KTVI":"2858",
"KPLR":"2859",
"KETC":"2860",
"WZZM":"2861",
"WWMT":"2862",
"WOOD":"2863",
"WXMI":"2864",
"WGVU":"2865",
"IFC":"2866",
"ESPCL":"2867",
"FXNWS":"2870",
"NASA":"2871",
"TWC":"2872",
"TRAV":"2873",
"QVC":"2874",
"HBO2E":"2875",
"HBOSG":"2876",
"SHO-E":"2877",
"TDISN":"2878",
"DHLTH":"2879",
"WRTV":"2882",
"WISH":"2883",
"WTHR":"2884",
"WXIN":"2885",
"WTTV":"2886",
"WNDY":"2887",
"WFYI":"2888",
"WGN9":"2889",
"WPWR":"2890",
"WTTW":"2891",
"WTLJ":"2892",
"WOTV":"2893",
"SCIFI":"2894",
"AMC":"2895",
"TNT":"2896",
"ESPN":"2897",
"CMT":"2898",
"DISC":"2899",
"TLC":"2900",
"PBS":"2901",
"HBOFM":"2902",
"SHO-W":"2903",
"ENVOE":"2912",
"FMONE":"2913",
"ESP2A":"2920",
"OTDCH":"2921",
"SHOEX":"2922",
"TMC-E":"2923",
"TMCXE":"2924",
"FOXNY":"2925",
"FOXBA":"2926",
"FOXS":"2927",
"FOXNW":"2928",
"NHL":"2929",
"NHL":"2930",
"NHL":"2931",
"NHL":"2932",
"NBA":"2933",
"MLB":"2934",
"MLB":"2935",
"MLB":"2936",
"MLB":"2937",
"DISNE":"2938",
"CSPAN":"2939",
"CSPN2":"2940",
"HSN":"2941",
"TBFC":"2942",
"SHNBC":"2943",
"TBN":"2944",
"EWTN":"2945",
"SUND":"2946",
"UNVSN":"2947",
"UCTV":"2948",
"BTV":"2949",
"WE":"2950",
"FX":"2952",
"NOG/N":"2953",
"SUN":"2954",
"FOXPT":"2955",
"FOXD":"2956",
"FOXP2":"2957",
"FOXNE":"2958",
"ALT2":"2959",
"ORDER":"2960",
"PPV":"2961",
"NHL":"2962",
"NHL":"2963",
"NBA":"2964",
"MLB":"2965",
"MLB":"2966",
"FX":"2969",
"BBC":"2970",
"LATNP":"2983",
"VMARI":"2984",
"DEST":"2986",
"MUZK2":"2987",
"TVLND":"2988",
"CMDY":"2989",
"LIFE":"2990",
"ESPNA":"2991",
"VH1":"2992",
"CNBC":"2993",
"MSNBC":"2994",
"TBS":"2995",
"HBO2W":"2996",
"MAX-W":"2997",
"SPORT":"2998",
"ENCOR":"3018",
"EWSTN":"3019",
"STARZ":"3020",
"SEDGE":"3021",
"SCINE":"3022",
"SBLCK":"3023",
"SK&FM":"3024",
"TXTSY":"3025",
"PAX":"3026",
"LMN":"3027",
"RFDTV":"3028",
"KWGN":"3030",
"NBC-W":"3032",
"CBS-W":"3033",
"ABC-W":"3034",
"FOX-W":"3035",
"ANGEL":"3036",
"KTNC":"3037",
"TEMP5":"3044",
"KABC":"3045",
"KCBS":"3046",
"KNBC":"3047",
"KTTV":"3048",
"KTLA":"3049",
"WSBK":"3051",
"WBSTR":"3059",
"USA":"3060",
"HGTV":"3061",
"E!":"3062",
"TCM":"3063",
"MTV":"3064",
"SPIKE":"3065",
"NICKW":"3066",
"DISNW":"3067",
"TOON":"3068",
"ABCFM":"3069",
"DNFYI":"3083",
"MAX-E":"3085",
"MOMAX":"3086",
"TVGAM":"3087",
"FOXRM":"3088",
"FOXSW":"3089",
"CSNCH":"3090",
"ALOCK":"3091",
"PPV":"3093",
"NHL":"3094",
"MLB":"3095",
"MLB":"3096",
"SPEED":"3097",
"1FA4":"3106",
"CH101":"3107",
"METRO":"3195",
"TEMP6":"3202",
"WABC":"3203",
"WCBS":"3204",
"WNBC":"3205",
"WNYW":"3206",
"WXTV":"3210",
"NAUHS":"3211",
"METRO":"3219",
"ALTUD":"3226",
"MSG":"3227",
"FOXAZ":"3228",
"FOXW":"3229",
"FOXFL":"3230",
"FOXOH":"3231",
"NESN":"3232",
"PPV":"3233",
"NHL":"3234",
"NHL":"3235",
"NHL":"3236",
"NHL":"3237",
"NHL":"3238",
"NHL":"3239",
"MLB":"3240",
"MLB":"3241",
"MLB":"3242",
"MLB":"3243",
"REFL":"3244",
"REFL":"3265",
"VOD":"3267",
"TST_5":"3157",
"TST_6":"3158",
"CNNAP":"3165",
"CNNAV":"3166",
"HNNAV":"3167",
"WB200":"3168",
"DNL8":"3169",
"DNL9":"3170",
"DNL10":"3171",
"DNL7":"3172",
"DNL5":"3173",
"DNL6":"3174",
"DNL4":"3175",
"DNL3":"3176",
"SSD":"3177",
"DNL":"3178",
"WPIX":"3179",
"WNET":"3180",
"WWOR":"3181",
"NBC":"3182",
"CBS":"3183",
"ABC":"3184",
"FOX":"3185",
"MIMIX":"3186",
"TEJNO":"3187"
}
"""
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

	############################################################################################################
	def config(self, reset=True):
		debug("> config() reset=%s" % reset)
		try:
			if reset:
				success = self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				pathEXE = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PATH_EXE)
				self.preRecMins = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PRE_REC)
				self.postRecMins = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_POST_REC)

				# EG "C:\Program Files\MyTheatre\MTStart.exe" /RECORD /DUR 123 /CHID 3316 /EVENT "Days and Passions"
				# This is the windows XP cmd line to create a Schedule Task
				self.SCHTASKS = 'schtasks /create /TN "$TITLE" /RU SYSTEM /SC ONCE /SD $DATE /ST $TIME ' \
								'/TR "\\"'+pathEXE+'\\" /RECORD /DUR $DURATION /CHID $CODE \\"$TITLE\\"'
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success

	############################################################################################################
	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme.run()")
		returnStr = ''

		# get programme information
		chName = channelInfo[TVChannels.CHAN_NAME]
		title = programme[TVData.PROG_TITLE]

		# search for tv card channel code.
		# this search can be done using either channel Name or ID or Alt. ID, but that depends on the KEY
		# used in the defined dictionary at top of script.
		# uncomment as appropiate
#		chIDAlt = channelInfo[TVChannels.CHAN_IDALT]
		chid = channelInfo[TVChannels.CHAN_ID]
		if not chid:
			messageOK(self.name, "Programme ID missing!", title, chName)
			debug("< SaveProgramme.run() failed")
			return False

		# uncomment as appropiate
		cardCode = self.lookupCode(chid)
#			cardCode = self.lookupCode(chName)
#			cardCode = self.lookupCode(chIDAlt)
		if cardCode:
			# Now time in secs
			currentTime = time.mktime(time.localtime(time.time()))
			startTimeSecs = int(self.programme[TVData.PROG_STARTTIME]) - (self.preRecMins * 60)
			endTimeSecs = int(self.programme[TVData.PROG_ENDTIME])+ (self.postRecMins * 60)

			if endTimeSecs <= currentTime:
				messageOK(__language__(801),__language__(802))			# prog already finished
			else:
				# Schedule Task wont run if time already passed. so make startTime a future timecurrent time.
				if startTimeSecs <= (currentTime + 60):
					startTimeSecs = currentTime	+120		# delay tobe 2 mins from currenttime

				startDate = time.strftime('%d/%m/%Y', time.localtime(startTimeSecs))
				startTime = time.strftime('%H:%M:%S', time.localtime(startTimeSecs))
				endTimeSecs + (self.postRecMins * 60)
				duration = int((endTimeSecs - startTimeSecs) /60)

				# dont bother recording anything too short
				if duration < 3:
					messageOK("Schedule Failure","Programme duration too short")
				else:
					# create return string
					returnStr = self.SCHTASKS.replace('$TITLE', title)
					returnStr = returnStr.replace('$DATE', startDate)
					returnStr = returnStr.replace('$TIME', startTime)
					returnStr = returnStr.replace('$DURATION', str(duration))
					returnStr = returnStr.replace('$CODE', cardCode)

		debug("< SaveProgramme().run()")
		return returnStr


	# Lookup tv card channel code number
	def lookupCode(self, searchCode):
		try:
			code = CHANNEL_CODES[searchCode]
		except:
			code = ''
		debug("lookupCode() searchCode=%s code=%s" % (searchCode, code))
		return code


	# scheduled tasks names cannot contain certain character.
	def cleanData(self, data):
		return re.sub(r'[\'\";:?*<>|\\/,=!\.]', '-', data)

############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_MYTHEATER'

		# CONFIG KEYS
		self.KEY_PATH_EXE = 'path_exe'
		self.KEY_PRE_REC = 'pre_rec'
		self.KEY_POST_REC = 'post_rec'

		self.configData = [
			[self.KEY_PATH_EXE,__language__(832), os.path.join( 'C:','Program Files','MyTheatre','MTStart.exe' ),KBTYPE_ALPHA],
			[self.KEY_PRE_REC,__language__(835),'2',KBTYPE_NUMERIC],
			[self.KEY_POST_REC,__language__(836),'2',KBTYPE_NUMERIC]
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
			value = self.getValue(key)
			if not value:
				debug("missing value for mandatory key=%s" % key)
				success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getValue(self, key):
		return mytvGlobals.config.action(self.CONFIG_SECTION, key)
