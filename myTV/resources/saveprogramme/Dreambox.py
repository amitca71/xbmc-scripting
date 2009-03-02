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
############################################################################################################

import xbmc, urllib, time
from mytvLib import *
from bbbGUILib import *
import mytvGlobals
from string import zfill, find

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

# CHANNELS - Translates Channel ID into Dreambox REF ID
REF_CODES = {

# USING RADIOTIMES DATASOURCE
# You will have to change the Channel Codes if your using a different DataSource
"92" : "1:0:1:283f:7fe:2:11a0000:0:0:0:",		# BBC 1 Yrks&Lin;BSkyB;282
"99" : "1:0:1:1af8:802:2:11a0000:0:0:0:",		# BBC 1 CI;BSkyB;282
"105" : "1:0:1:189e:7fd:2:11a0000:0:0:0:",		# BBC 2 England;BSkyB;282
"112" : "1:0:1:1920:7ff:2:11a0000:0:0:0:",		# BBC 2 NI;BSkyB;282
"32" : "1:0:1:27b0:805:2:11a0000:0:0:0:",		# ITV1 Yorks W;BSkyB;282
"132" : "1:0:1:23f1:7e8:2:11a0000:0:0:0:",		# Channel 4;BSkyB;282
"134" : "1:0:1:247e:7ef:2:11a0000:0:0:0:",		# five;BSkyB;282
"185" : "1:0:1:2756:7fc:2:11a0000:0:0:0:",		# ITV2;BSkyB;282
"231" : "1:0:1:2581:7fb:2:11a0000:0:0:0:",		# RTE One;BSkyB;282
"941" : "1:0:1:2585:7fb:2:11a0000:0:0:0:",		# TV3;BSkyB;282
"1870" : "1:0:1:2582:7fb:2:11a0000:0:0:0:",		# RTE TWO;BSkyB;282
"273" : "1:0:1:2583:7fb:2:11a0000:0:0:0:",		# TG4;BSkyB;282
"205" : "1:0:1:1b5b:7da:2:11a0000:0:0:0:",		#;MTV2;BSkyB;282
"158" : "1:0:1:2071:7fa:2:11a0000:0:0:0:",		# ;E4;BSkyB;282
"45" : "1:0:1:18af:7fd:2:11a0000:0:0:0:",		#BBC THREE;BSkyB;282
"47" : "1:0:1:18ac:7fd:2:11a0000:0:0:0:",		#BBC FOUR;BSkyB;282
"122" : "1:0:1:1774:7d2:2:11a0000:0:0:0:",		#Bravo;BSkyB;282
"1859" : "1:0:1:2814:806:2:11a0000:0:0:0:",		#ITV3;BSkyB;282
"248" : "1:0:1:125f:7ee:2:11a0000:0:0:0:",		#Sky One;BSkyB;282
"262" : "1:0:1:1076:7e5:2:11a0000:0:0:0:",		#Sky Sports 1;BSkyB;282
"149" : "1:0:1:1842:7d9:2:11a0000:0:0:0:",		#Disc H&H+1;BSkyB;282
"150" : "1:0:1:c353:7e7:2:11a0000:0:0:0:",		#Disc.RT+1;BSkyB;282
"151" : "1:0:1:1841:7d9:2:11a0000:0:0:0:",		#Disc. Kids;BSkyB;282
"155" : "1:0:1:184b:7d9:2:11a0000:0:0:0:",		#Disc. Wings;BSkyB;282
"147" : "1:0:1:1839:7d9:2:11a0000:0:0:0:",		#Discovery;BSkyB;282
"154" : "1:0:1:183d:7d9:2:11a0000:0:0:0:",		#Discovery T&L;BSkyB;282
"152" : "1:0:1:183c:7d9:2:11a0000:0:0:0:",		#Discovery+1hr;BSkyB;282
"158" : "1:0:1:2071:7fa:2:11a0000:0:0:0:",		#E4;BSkyB;282
"1161" : "1:0:1:206c:7fa:2:11a0000:0:0:0:",		#E4+1;BSkyB;282
"1461" : "1:0:1:158b:7e5:2:11a0000:0:0:0:",		#FX;BSkyB;282
"249" : "1:0:1:12c9:7ee:2:11a0000:0:0:0:",		#Sky Cinema 1;BSkyB;282
"250" : "1:0:1:12c2:7ee:2:11a0000:0:0:0:",		#Sky Cinema 2;BSkyB;282
"257" : "1:0:1:10cf:7d7:2:11a0000:0:0:0:",		#Sky Movies 1;BSkyB;282
"251" : "1:0:1:10ce:7d7:2:11a0000:0:0:0:",		#Sky Movies 2;BSkyB;282
"258" : "1:0:1:1133:7d7:2:11a0000:0:0:0:",		#Sky Movies 3;BSkyB;282
"252" : "1:0:1:1132:7db:2:11a0000:0:0:0:",		#Sky Movies 4;BSkyB;282
"259" : "1:0:1:1197:7db:2:11a0000:0:0:0:",		#Sky Movies 5;BSkyB;282
"253" : "1:0:1:1196:7db:2:11a0000:0:0:0:",		#Sky Movies 6;BSkyB;282
"260" : "1:0:1:11fb:7ee:2:11a0000:0:0:0:",		#Sky Movies 7;BSkyB;282
"255" : "1:0:1:157e:7d7:2:11a0000:0:0:0:",		#Sky Movies 8;BSkyB;282
"254" : "1:0:1:11fa:7ee:2:11a0000:0:0:0:",		#Sky Movies 9;BSkyB;282
"256" : "1:0:1:1266:7ea:2:11a0000:0:0:0:",		#Sky News UK (Cable);BSkyB;282
"262" : "1:0:1:1076:7e5:2:11a0000:0:0:0:",		#Sky Sports 1;BSkyB;282
"264" : "1:0:1:1070:7e5:2:11a0000:0:0:0:",		#Sky Sports 2;BSkyB;282
"265" : "1:0:1:107b:7e5:2:11a0000:0:0:0:",		#Sky Sports 3;BSkyB;282
"300" : "1:0:1:132b:7e7:2:11a0000:0:0:0:",		#Sky Spts News;BSkyB;282
"263" : "1:0:1:1519:7e7:2:11a0000:0:0:0:",		#Sky Spts Xtra;BSkyB;282
"276" : "1:0:1:113a:7d8:2:11a0000:0:0:0:",		#TV5;BSkyB;282
"922" : "1:0:1:13f0:7eb:2:11a0000:0:0:0:",		#Sky Two;BSkyB;282
"1856" : "1:0:1:2332:803:2:11a0000:0:0:0:"		#abc1;BSkyB;282

}

# THESE NEED CONVERTING INTO ABOVE DICT FORMAT
#1:0:1:1776:7d2:2:11a0000:0:0:0:;Bravo+1;BSkyB;282
#1:0:1:1647:7f0:2:11a0000:0:0:0:;Adventure One;BSkyB;282
#1:0:1:c495:964:2:11a0000:0:0:0:;Al Jazeera;BSkyB;282
#1:0:1:183a:7d9:2:11a0000:0:0:0:;Animal Planet;BSkyB;282
#1:0:1:c354:7e3:2:11a0000:0:0:0:;At The Races;BSkyB;282
#1:0:1:2841:7fe:2:11a0000:0:0:0:;BBC 1 E Mids;BSkyB;282
#1:0:1:2842:7fe:2:11a0000:0:0:0:;BBC 1 East (E);BSkyB;282
#1:0:1:283e:7fe:2:11a0000:0:0:0:;BBC 1 N West;BSkyB;282
#1:0:1:2873:800:2:11a0000:0:0:0:;BBC 1 NE & C;BSkyB;282
#1:0:1:2870:800:2:11a0000:0:0:0:;BBC 1 S East;BSkyB;282
#1:0:1:1915:7ff:2:11a0000:0:0:0:;BBC 1 Scotland;BSkyB;282
#1:0:1:2871:800:2:11a0000:0:0:0:;BBC 1 South;BSkyB;282
#1:0:1:283f:7fe:2:11a0000:0:0:0:;BBC 1 Yrks&Lin;BSkyB;282
#1:0:1:1916:7ff:2:11a0000:0:0:0:;BBC 2 Scotland;BSkyB;282
#1:0:1:190c:7ff:2:11a0000:0:0:0:;BBC 2W;BSkyB;282
#1:0:1:18a0:7fd:2:11a0000:0:0:0:;BBC NEWS 24;BSkyB;282
#1:0:1:1af6:802:2:11a0000:0:0:0:;BBC PARL'MNT;BSkyB;282
#1:0:1:16ab:7e9:2:11a0000:0:0:0:;Biography;BSkyB;282
#1:0:1:164d:7f0:2:11a0000:0:0:0:;Boomerang;BskyB;282
#1:0:1:1bbc:7e2:2:11a0000:0:0:0:;Cartoon Netwrk;BSkyB;282
#1:0:1:106f:7e5:2:11a0000:0:0:0:;Cartoon Nwk+;BSkyB;282
#1:0:1:18ae:7fd:2:11a0000:0:0:0:;CBeebies;BSkyB;282
#1:0:1:1772:7d2:2:11a0000:0:0:0:;Challenge;BSkyB;282
#1:0:1:cc08:8ff:2:11a0000:0:0:0:;Challenge+1;BSkyB;282
#1:0:1:cd19:902:2:11a0000:0:0:0:;Chart Show TV;BSkyB;282
#1:0:1:183f:7d9:2:11a0000:0:0:0:;Civilisation;BSkyB;282
#1:0:1:164a:7f0:2:11a0000:0:0:0:;CNBC;BSkyB;282
#1:0:1:1be4:7e2:2:11a0000:0:0:0:;CNN;BSkyB;282
#1:0:1:1cad:7e6:2:11a0000:0:0:0:;Create & Craft;BSkyB;282
#1:0:1:2329:803:2:11a0000:0:0:0:;Disney Chnl;BSkyB;282
#1:0:1:232a:803:2:11a0000:0:0:0:;Disney Chnl +1;BSkyB;282
#1:0:1:2586:7fb:2:11a0000:0:0:0:;DW-TV;BSkyB;282
#1:0:1:cb26:8fd:2:11a0000:0:0:0:;unnamed service;unnamed provider;282
#1:0:1:1134:7d7:2:11a0000:0:0:0:;Eurosport UK;BSkyB;282
#1:0:1:1391:7e7:2:11a0000:0:0:0:;Eurosport2 UK;BSkyB;282
#1:0:1:c79d:96c:2:11a0000:0:0:0:;Extreme Sports;BSkyB;282
#1:0:1:247e:7ef:2:11a0000:0:0:0:;five;BSkyB;282
#1:0:1:c357:7e3:2:11a0000:0:0:0:;FOX News;BSkyB;282
#1:0:1:cc07:8ff:2:11a0000:0:0:0:;Ftn;BSkyB;282
#1:0:1:2544:7f4:2:11a0000:0:0:0:;Babestation;BSkyB;282
#1:0:1:ccb8:901:2:11a0000:0:0:0:;Golf Channel;BSkyB;282
#1:0:1:1844:7d9:2:11a0000:0:0:0:;H&Li;BSkyB;282
#1:0:1:1392:7e7:2:11a0000:0:0:0:;Hallmark;BSkyB;282
#1:0:1:16ad:7e9:2:11a0000:0:0:0:;History;BSkyB;282
#1:0:1:170d:7e9:2:11a0000:0:0:0:;History +1 hour;BSkyB;282
#1:0:1:cb89:907:2:11a0000:0:0:0:;HorrorChannel;BSkyB;282
#1:0:1:27d8:806:2:11a0000:0:0:0:;ITV Channel Is;BSkyB;282
#1:0:1:27c5:7f9:2:11a0000:0:0:0:;ITV1 Anglia W;BSkyB;282
#1:0:1:279c:805:2:11a0000:0:0:0:;ITV1 Meridian S;BSkyB;282
#1:0:1:27ce:7f9:2:11a0000:0:0:0:;ITV1 TT N;BSkyB;282
#1:0:1:2738:801:2:11a0000:0:0:0:;ITV1 W Country;BSkyB;282
#1:0:1:1584:7ed:2:11a0000:0:0:0:;Jetix;BSkyB;282
#1:0:1:12c4:7e3:2:11a0000:0:0:0:;Kerrang!;BSkyB;282
#1:0:1:1771:7d2:2:11a0000:0:0:0:;LIVINGtv;BSkyB;282
#1:0:1:1775:7d2:2:11a0000:0:0:0:;LIVINGtv+1;BSkyB;282
#1:0:1:1777:7d2:2:11a0000:0:0:0:;LIVINGtv2;BSkyB;282
#1:0:1:1583:7e3:2:11a0000:0:0:0:;Magic;BSkyB;282
#1:0:1:d057:90a:2:11a0000:0:0:0:;Motors TV;BSkyB;282
#1:0:1:1b59:7da:2:11a0000:0:0:0:;MTV;BSkyB;282
#1:0:1:1b5f:7da:2:11a0000:0:0:0:;MTV Base;BSkyB;282
#1:0:1:1b66:7da:2:11a0000:0:0:0:;MTV Dance;BSkyB;282
#1:0:1:1b5e:7da:2:11a0000:0:0:0:;MTV Hits;BSkyB;282
#1:0:1:1b5b:7da:2:11a0000:0:0:0:;MTV2;BSkyB;282
#1:0:1:1135:7d7:2:11a0000:0:0:0:;Nat Geo;BSkyB;282
#1:0:1:1710:7e9:2:11a0000:0:0:0:;ParaComedy 1;BSkyB;282
#1:0:1:1198:7db:2:11a0000:0:0:0:;ParaComedy 2;BSkyB;282
#1:0:1:ccb2:901:2:11a0000:0:0:0:;Performance;BSkyB;282
#1:0:1:232c:803:2:11a0000:0:0:0:;Playhse Disney;BSkyB;282
#1:0:1:16ac:7eb:2:11a0000:0:0:0:;Q;BSkyB;282
#1:0:1:253c:7f4:2:11a0000:0:0:0:;Reality TV;BSkyB;282
#1:0:1:cb86:907:2:11a0000:0:0:0:;Reality TV +1;BSkyB;282
#1:0:1:1c85:7e6:2:11a0000:0:0:0:;S4C~ Digidol;BSkyB;282
#1:0:1:1c86:7e6:2:11a0000:0:0:0:;S4C~2;BSkyB;282
#1:0:1:1329:7e7:2:11a0000:0:0:0:;Sci-Fi;BSkyB;282
#1:0:1:183e:7d9:2:11a0000:0:0:0:;Science;BSkyB;282
#1:0:1:27ec:806:2:11a0000:0:0:0:;Scottish TV W;BSkyB;282
#1:0:1:cc56:900:2:11a0000:0:0:0:;Scuzz;BSkyB;282
#1:0:1:138d:804:2:11a0000:0:0:0:;Sky Travel;BSkyB;282
#1:0:1:f41:804:2:11a0000:0:0:0:;Sky Travel +1;BSkyB;282
#1:0:1:2460:804:2:11a0000:0:0:0:;Sky Trvl Extra;BSkyB;282
#1:0:1:c350:7e3:2:11a0000:0:0:0:;Smash Hits!;BSkyB;282
#1:0:1:1bbd:7e2:2:11a0000:0:0:0:;TCM;BSkyB;282
#1:0:1:2583:7fb:2:11a0000:0:0:0:;TG4;BSkyB;282
#1:0:1:cc51:900:2:11a0000:0:0:0:;The Amp;BSkyB;282
#1:0:1:1456:7eb:2:11a0000:0:0:0:;The Box;BSkyB;282
#1:0:1:cd23:902:2:11a0000:0:0:0:;The Vault;BSkyB;282
#1:0:1:cd32:902:2:11a0000:0:0:0:;Tiny Pop;BSkyB;282
#1:0:1:1b61:7da:2:11a0000:0:0:0:;TMF;BSkyB;282
#1:0:1:232b:803:2:11a0000:0:0:0:;Toon Disney;BSkyB;282
#1:0:1:1bbf:7e2:2:11a0000:0:0:0:;Toonami;BSkyB;282
#1:0:1:1bc4:7e2:2:11a0000:0:0:0:;Toonami I;BSkyB;282
#1:0:1:1bee:7e2:2:11a0000:0:0:0:;Travel Channel;BSkyB;282
#1:0:1:ccbc:901:2:11a0000:0:0:0:;Travel Ch +1;BSkyB;282
#1:0:1:1773:7d2:2:11a0000:0:0:0:;Trouble;BSkyB;282
#1:0:1:cc06:8ff:2:11a0000:0:0:0:;Trouble Reload;BSkyB;282
#1:0:1:1977:7d6:2:11a0000:0:0:0:;unnamed service;unnamed provider;282
#1:0:1:1966:7d6:2:11a0000:0:0:0:;UKTV Docs;BSkyB;282
#1:0:1:1dc4:7df:2:11a0000:0:0:0:;UKTV Docs+1;BSkyB;282
#1:0:1:1979:7d6:2:11a0000:0:0:0:;UKTV Drama;BSkyB;282
#1:0:1:196c:7d6:2:11a0000:0:0:0:;UKTV Food;BSkyB;282
#1:0:1:196b:7d6:2:11a0000:0:0:0:;UKTV Food +1;BSkyB;282
#1:0:1:196a:7d6:2:11a0000:0:0:0:;UKTV G2;BSkyB;282
#1:0:1:1dc9:7df:2:11a0000:0:0:0:;UKTV G2+1.;BSkyB;282
#1:0:1:1968:7d6:2:11a0000:0:0:0:;UKTV Gold;BSkyB;282
#1:0:1:1db5:7df:2:11a0000:0:0:0:;UKTV Gold +1;BSkyB;282
#1:0:1:1969:7d6:2:11a0000:0:0:0:;UKTV History;BSkyB;282
#1:0:1:1dbf:7df:2:11a0000:0:0:0:;UKTV H'tory+1;BSkyB;282
#1:0:1:1dbb:7df:2:11a0000:0:0:0:;UKTV People;BSkyB;282
#1:0:1:1978:7d6:2:11a0000:0:0:0:;UKTV S Garden;BSkyB;282
#1:0:1:1965:7d6:2:11a0000:0:0:0:;UKTV Style;BSkyB;282
#1:0:1:1db0:7df:2:11a0000:0:0:0:;UKTV Style +1;BSkyB;282
#1:0:1:1dce:7df:2:11a0000:0:0:0:;UKTVPeople+1;BSkyB;282
#1:0:1:27f6:806:2:11a0000:0:0:0:;UTV;BSkyB;282
#1:0:1:1b5a:7da:2:11a0000:0:0:0:;VH1;BSkyB;282
#1:0:1:1b60:7da:2:11a0000:0:0:0:;VH1 Classic;BSkyB;282
#1:0:1:1b5d:7da:2:11a0000:0:0:0:;VH2;BSkyB;282
#1:0:1:1267:7ea:2:11a0000:0:0:0:;Sky News Eire (Cable);BSkyB;282

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
				serverIP = self.configSaveProgramme.getServerIP()
				serverUser = self.configSaveProgramme.getServerUser()
				serverPwd = self.configSaveProgramme.getServerPwd()
				self.preRecMins = self.configSaveProgramme.getPreRecMins()
				self.postRecMins = self.configSaveProgramme.getPostRecMins()
				self.isEnigma = self.configSaveProgramme.getModel()

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
					self.URL_BASE += 'web/wap/'
# sampe 'Enigma 2' Dreambox  URL
# http://192.168.0.3/web/wap/timeradd?justplay=0&syear=2008&smonth=9&sday=16&shour=16&smin=25&eyear=2008&emonth=9&eday=16&ehour=18&emin=25
# &sRef=1%3A134%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM+BOUQUET+&name=Name+of++Prog&description=Description+of+Program&afterevent=0&disabled=0
# &deleteOldOnSave=0&command=add&save=Add%2FSave
					self.URL_TIMER_CREATE = self.URL_BASE + "timeradd?justplay=0" \
											"&sRef=$REFAFROM+BOUQUET" \
											"&syear=$SYEAR&smonth=$SMONTH&sday=$SDAY&shour=$SHOUR&smin=$SHOUR" \
											"&eyear=$EYEAR&emonth=$EMONTH&eday=$EDAY&ehour=$EHOUR&emin=$EHOUR" \
											"&name=$TITLE&description=" \
											"&afterevent=0&disabled=0&deleteOldOnSave=0&command=add&save=Add/Save"
					self.URL_TIMER_DELETE = self.URL_BASE + "timerdelete?&ref=$REF&begin=$STIME&end=$ETIME"
					self.URL_TIMER_LIST = self.URL_BASE + 'timerlist.html'

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
							.replace('$SMIN', str(startTime_tm.tm_min)) \
							.replace('$EYEAR', str(endTime_tm.tm_year)) \
							.replace('$EMONTH', str(endTime_tm.tm_mon)) \
							.replace('$EDAY', str(endTime_tm.tm_mday)) \
							.replace('$EHOUR', str(endTime_tm.tm_hour)) \
							.replace('$EMIN', str(endTime_tm.tm_min)) \
							.replace('$TITLE', title)

				doc = fetchURL(url)
				success = self.checkServerResult(doc)
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
		self.KEY_IP = 'ip'
		self.KEY_USER = 'user'
		self.KEY_PASS = 'pwd'
		self.KEY_PRE_REC = 'pre_rec'
		self.KEY_POST_REC = 'post_rec'
		self.KEY_IS_ENIGMA = 'isEnigma'

		# Uncomment the ONE that works for your web server interface
		self.configData = [
			[self.KEY_IP,__language__(812),'192.168.1.3',KBTYPE_IP],
			[self.KEY_USER,__language__(805),'root',KBTYPE_ALPHA],
			[self.KEY_PASS,__language__(806),'dreambox',KBTYPE_ALPHA],
			[self.KEY_PRE_REC,__language__(835),'1',KBTYPE_NUMERIC],
			[self.KEY_POST_REC,__language__(836),'1',KBTYPE_NUMERIC],
			[self.KEY_IS_ENIGMA,"Is Model Enigma2?", False, KBTYPE_YESNO]
			]

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("ConfigSaveProgramme().reset()")
		configOptionsMenu(self.CONFIG_SECTION, self.configData, __language__(534))

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		for data in self.configData:
			key = data[0]
			if key == self.KEY_PASS:			# pwd not reqd
				continue
			value = self.getValue(key)			# key
			if value in (None,""):
				debug("missing value for mandatory key=%s" % key)
				success = False
				break

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getServerIP(self):
		return self.getValue(self.KEY_IP)
	def getServerUser(self):
		return self.getValue(self.KEY_USER)
	def getServerPwd(self):
		return self.getValue(self.KEY_PASS)
	def getPreRecMins(self):
		return int(self.getValue(self.KEY_PRE_REC))
	def getPostRecMins(self):
		return int(self.getValue(self.KEY_POST_REC))
	def getModel(self):
		return self.getValue(self.KEY_IS_ENIGMA)

	def getValue(self, key):
		return mytvGlobals.config.action(self.CONFIG_SECTION, key)
