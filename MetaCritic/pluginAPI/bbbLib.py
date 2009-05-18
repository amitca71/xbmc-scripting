"""
 Supporting shared functions for Plugin
"""

import os, sys, os.path, re
from urllib import quote_plus, unquote_plus, urlcleanup, FancyURLopener, urlretrieve
from string import find
import codecs
import xbmc, xbmcgui

from pluginAPI.xbmcplugin_const import *

__plugin__ = sys.modules[ "__main__" ].__plugin__
global dialogProgress
dialogProgress = xbmcgui.DialogProgress()

#################################################################################################################
def log(msg, loglevel=xbmc.LOGDEBUG):
	try:
		xbmc.log("[%s]: %s" % (__plugin__, msg), loglevel)
	except: pass

#################################################################################################################
def logError(msg=""):
	log("ERROR: %s %s" % (msg, sys.exc_info()[ 1 ]))

#################################################################################################################
def messageOK(title='', line1='', line2='',line3=''):
	xbmcgui.Dialog().ok(title ,line1,line2,line3)

#################################################################################################################
def handleException(msg=''):
	import traceback
	traceback.print_exc()
	messageOK(__plugin__ + " ERROR!", msg, str(sys.exc_info()[ 1 ]) )

#################################################################################################################
def loadFileObj( filename, dataType={} ):
	log( "loadFileObj() " + filename)
	try:
		file_handle = open( xbmc.translatePath(filename), "r" )
		loadObj = eval( file_handle.read() )
		file_handle.close()
	except:
		loadObj = None
	return loadObj

#################################################################################################################
def saveFileObj( filename, saveObj ):
	log( "saveFileObj() " + filename)
	try:
		file_handle = open( xbmc.translatePath(filename), "w" )
		file_handle.write( repr( saveObj ) )
		file_handle.close()
		return True
	except:
		handleException( "_save_file_obj()" )
		return False

#################################################################################################################
# delete a single file
def deleteFile(filename):
	try:
		os.remove(xbmc.translatePath(filename))
		log("deleteFile() deleted: " + filename)
	except: pass

#################################################################################################################
# look for html between < and > chars and remove it
def cleanHTML(data, breaksToNewline=True):
	if not data: return ""
	try:
		data = decodeText(data)
		if breaksToNewline:
			data = data.replace('<br>','\n').replace('<p>','\n').replace('<BR>','\n').replace('<P>','\n')
		reobj = re.compile('<.+?>', re.IGNORECASE+re.DOTALL+re.MULTILINE)
		return (re.sub(reobj, '', data).replace('\n\n','\n').replace('\r\n','\n').replace('&nbsp;','')).strip()
	except:
		logError()
		return data

#################################################################################################################
def encodeText(text):
	""" convert chars to make suitable for url """
#	return repr( quote_plus(text.replace("'", '"')) )
	try:
		return  repr( quote_plus(text.replace("'", '"').encode('utf-8')) )
	except:
		logError("encodeText()")
	return repr(text.replace("'", '"'))

#################################################################################################################
def decodeText(text, removeNewLines=True):
	""" convert chars from url encoding to normal chars """
	text = decodeEntities(text, removeNewLines)
	try:
		return unquote_plus(text).decode("unicode-escape")
	except:
		return unquote_plus(text)


#################################################################################################################
# if success: returns the page given in url as a string
# else: return -1 for Exception None for HTTP timeout, '' for empty page otherwise page data
#################################################################################################################
def fetchURL(url, file='', params=None, headers={}, isBinary=False, encodeURL=True):
	log("> bbbLib.fetchURL() %s isBinary=%s encodeURL=%s" % (url, isBinary, encodeURL))
	if encodeURL:
		safe_url = quote_plus(url,'/:&?=+#@')
	else:
		safe_url = url

	success = False
	data = None
	if not file:
		# create temp file if needed
		file = xbmc.translatePath(os.path.join(os.getcwd(), "temp.html"))

	# remove destination file if exists already
	deleteFile(file)

	# fetch from url
	try:
		opener = FancyURLopener()

		# add headers if supplied
#		if headers:
		if not headers.has_key('User-Agent')  and not headers.has_key('User-agent'):
			headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
		for name, value  in headers.items():
			opener.addheader(name, value)

		fn, resp = opener.retrieve(safe_url, file, data=params)
#		print fn, resp

		content_type = resp.get("Content-Type",'').lower()
		# fail if expecting an image but not corrent type returned
		if isBinary and (find(content_type,"text") != -1):
			raise "Not Binary"

		opener.close()
		del opener
		urlcleanup()
	except IOError, errobj:
		ErrorCode(errobj)
	except "Not Binary":
		log("Returned Non Binary content")
	except:
		handleException("fetchURL()")
	else:
		if not isBinary:
			data = readFile(file)		# read retrieved file
			if (not data) or ( "404 Not Found" in data ):
				data = ''
		else:
			data = fileExist(file)		# check image file exists

	if not data:
		deleteFile(file)
	else:
		success = True

	log( "< fetchURL success=%s" % success)
	return data

#################################################################################################################
def ErrorCode(e):
	log("> ErrorCode()")
	print "except=%s" % e
	if hasattr(e, 'code'):
		code = e.code
	else:
		code = ''
		if not isinstance(e, str):
			try:
				code = e[0]
			except:
				code = 'Unknown'
	title = 'Error, Code: %s' % code

	if hasattr(e, 'reason'):
		txt = e.reason
	else:
		try:
			txt = e[1]
		except:
			txt = 'Unknown reason'
	messageOK(title, str(txt))
	log("< ErrorCode()")

#################################################################################################################
def readFile(filename):
	try:
		f = xbmc.translatePath(filename)
		log("bbbLib.readFile() " + f)
		return file(f).read()
	except:
		return ""

#################################################################################################################
def fileExist(filename):
	try:
		osFN = xbmc.translatePath(filename)
		if os.path.isfile(osFN) and os.path.getsize(osFN) > 0:
			return True
	except:
		print str( sys.exc_info()[ 1 ] )
	return False

#################################################################################################################
def searchRegEx(data, regex, flags=re.MULTILINE+re.IGNORECASE+re.DOTALL, firstMatchOnly=True):
	try:
		value = ""
		match = re.search(regex, data, flags)
		if match:
			if firstMatchOnly:
				value = match.group(1)
			else:
				value = match.groups()
	except:
		value = ""
	return value

#################################################################################################################
def findAllRegEx(data, regex, flags=re.MULTILINE+re.IGNORECASE+re.DOTALL):
	try:
		matchList = re.compile(regex, flags).findall(data)
	except:
		matchList = []

	if matchList:
		sz = len(matchList)
	else:
		sz = 0
	log("findAllRegEx() matches=%s" % sz)
	return matchList

#################################################################################################################
# Thanks to Arboc for contributing most of the translation in this function. 
#################################################################################################################
def decodeEntities(txt, removeNewLines=True):
	if not txt: return ""
	txt = txt.replace('\t','')

# % values
	if find(txt,'%') >= 0:
		txt = txt.replace('%21', "!")
		txt = txt.replace('%22', '"')
		txt = txt.replace('%25', "%")
		txt = txt.replace('%26', "&")
		txt = txt.replace('%27', "'")
		txt = txt.replace('%28', "(")
		txt = txt.replace('%29', ")")
		txt = txt.replace('%2a', "*")
		txt = txt.replace('%2b', "+")
		txt = txt.replace('%2c', ",")
		txt = txt.replace('%2d', "-")
		txt = txt.replace('%2e', ".")
		txt = txt.replace('%3a', ":")
		txt = txt.replace('%3b', ";")
		txt = txt.replace('%3f', "?")
		txt = txt.replace('%40', "@")

# 
	if find(txt,"&#") >= 0:
		txt = txt.replace('&#034;','"')
		txt = txt.replace('&#039;','\'')
		txt = txt.replace('&#13;&#10;','\n')
		txt = txt.replace('&#10;','\n')
		txt = txt.replace('&#13;','\n')
		txt = txt.replace('&#146;', "'")
		txt = txt.replace('&#156;', "oe")
		txt = txt.replace('&#160;', " ") # no-break space = non-breaking space U+00A0 ISOnum
		txt = txt.replace('&#161;', "!") # inverted exclamation mark U+00A1 ISOnum
		txt = txt.replace('&#162;', "c") # cent sign U+00A2 ISOnum
		txt = txt.replace('&#163;', "p") # pound sign U+00A3 ISOnum
		txt = txt.replace('&#164;', "$") # currency sign U+00A4 ISOnum
		txt = txt.replace('&#165;', "y") # yen sign = yuan sign U+00A5 ISOnum
		txt = txt.replace('&#166;', "|") # broken bar = broken vertical bar U+00A6 ISOnum
		txt = txt.replace('&#167;', "S") # section sign U+00A7 ISOnum
		txt = txt.replace('&#168;', "''") # diaeresis = spacing diaeresis U+00A8 ISOdia
		txt = txt.replace('&#169;', "(c)") # copyright sign U+00A9 ISOnum
		txt = txt.replace('&#170;', "e") # feminine ordinal indicator U+00AA ISOnum
		txt = txt.replace('&#171;', '"') # left-pointing double angle quotation mark = left pointing guillemet U+00AB ISOnum
		txt = txt.replace('&#172;', "-.") # not sign U+00AC ISOnum
		txt = txt.replace('&#173;', "-") # soft hyphen = discretionary hyphen U+00AD ISOnum
		txt = txt.replace('&#174;', "(R)") # registered sign = registered trade mark sign U+00AE ISOnum
		txt = txt.replace('&#175;', "-") # macron = spacing macron = overline = APL overbar U+00AF ISOdia
		txt = txt.replace('&#176;', "o") # degree sign U+00B0 ISOnum
		txt = txt.replace('&#177;', "+-") # plus-minus sign = plus-or-minus sign U+00B1 ISOnum
		txt = txt.replace('&#178;', "2") # superscript two = superscript digit two = squared U+00B2 ISOnum
		txt = txt.replace('&#179;', "3") # superscript three = superscript digit three = cubed U+00B3 ISOnum
		txt = txt.replace('&#180;', " ") # acute accent = spacing acute U+00B4 ISOdia
		txt = txt.replace('&#181;', "u") # micro sign U+00B5 ISOnum
		txt = txt.replace('&#182;', "|p") # pilcrow sign = paragraph sign U+00B6 ISOnum
		txt = txt.replace('&#183;', ".") # middle dot = Georgian comma = Greek middle dot U+00B7 ISOnum
		txt = txt.replace('&#184;', " ") # cedilla = spacing cedilla U+00B8 ISOdia
		txt = txt.replace('&#185;', "1") # superscript one = superscript digit one U+00B9 ISOnum
		txt = txt.replace('&#186;', "o") # masculine ordinal indicator U+00BA ISOnum
		txt = txt.replace('&#187;', '"') # right-pointing double angle quotation mark = right pointing guillemet U+00BB ISOnum
		txt = txt.replace('&#188;', "1/4") # vulgar fraction one quarter = fraction one quarter U+00BC ISOnum
		txt = txt.replace('&#189;', "1/2") # vulgar fraction one half = fraction one half U+00BD ISOnum
		txt = txt.replace('&#190;', "3/4") # vulgar fraction three quarters = fraction three quarters U+00BE ISOnum
		txt = txt.replace('&#191;', "?") # inverted question mark = turned question mark U+00BF ISOnum
		txt = txt.replace('&#192;', "A") # latin capital letter A with grave = latin capital letter A grave U+00C0 ISOlat1
		txt = txt.replace('&#193;', "A") # latin capital letter A with acute U+00C1 ISOlat1
		txt = txt.replace('&#194;', "A") # latin capital letter A with circumflex U+00C2 ISOlat1
		txt = txt.replace('&#195;', "A") # latin capital letter A with tilde U+00C3 ISOlat1
		txt = txt.replace('&#196;', "A") # latin capital letter A with diaeresis U+00C4 ISOlat1
		txt = txt.replace('&#197;', "A") # latin capital letter A with ring above = latin capital letter A ring U+00C5 ISOlat1
		txt = txt.replace('&#198;', "AE") # latin capital letter AE = latin capital ligature AE U+00C6 ISOlat1
		txt = txt.replace('&#199;', "C") # latin capital letter C with cedilla U+00C7 ISOlat1
		txt = txt.replace('&#200;', "E") # latin capital letter E with grave U+00C8 ISOlat1
		txt = txt.replace('&#201;', "E") # latin capital letter E with acute U+00C9 ISOlat1
		txt = txt.replace('&#202;', "E") # latin capital letter E with circumflex U+00CA ISOlat1
		txt = txt.replace('&#203;', "E") # latin capital letter E with diaeresis U+00CB ISOlat1
		txt = txt.replace('&#204;', "I") # latin capital letter I with grave U+00CC ISOlat1
		txt = txt.replace('&#205;', "I") # latin capital letter I with acute U+00CD ISOlat1
		txt = txt.replace('&#206;', "I") # latin capital letter I with circumflex U+00CE ISOlat1
		txt = txt.replace('&#207;', "I") # latin capital letter I with diaeresis U+00CF ISOlat1
		txt = txt.replace('&#208;', "D") # latin capital letter ETH U+00D0 ISOlat1
		txt = txt.replace('&#209;', "N") # latin capital letter N with tilde U+00D1 ISOlat1
		txt = txt.replace('&#210;', "O") # latin capital letter O with grave U+00D2 ISOlat1
		txt = txt.replace('&#211;', "O") # latin capital letter O with acute U+00D3 ISOlat1
		txt = txt.replace('&#212;', "O") # latin capital letter O with circumflex U+00D4 ISOlat1
		txt = txt.replace('&#213;', "O") # latin capital letter O with tilde U+00D5 ISOlat1
		txt = txt.replace('&#214;', "O") # latin capital letter O with diaeresis U+00D6 ISOlat1
		txt = txt.replace('&#215;', "x") # multiplication sign U+00D7 ISOnum
		txt = txt.replace('&#216;', "O") # latin capital letter O with stroke = latin capital letter O slash U+00D8 ISOlat1
		txt = txt.replace('&#217;', "U") # latin capital letter U with grave U+00D9 ISOlat1
		txt = txt.replace('&#218;', "U") # latin capital letter U with acute U+00DA ISOlat1
		txt = txt.replace('&#219;', "U") # latin capital letter U with circumflex U+00DB ISOlat1
		txt = txt.replace('&#220;', "U") # latin capital letter U with diaeresis U+00DC ISOlat1
		txt = txt.replace('&#221;', "Y") # latin capital letter Y with acute U+00DD ISOlat1
		txt = txt.replace('&#222;', "D") # latin capital letter THORN U+00DE ISOlat1
		txt = txt.replace('&#223;', "SS") # latin small letter sharp s = ess-zed U+00DF ISOlat1
		txt = txt.replace('&#224;', "a") # latin small letter a with grave = latin small letter a grave U+00E0 ISOlat1
		txt = txt.replace('&#225;', "a") # latin small letter a with acute U+00E1 ISOlat1
		txt = txt.replace('&#226;', "a") # latin small letter a with circumflex U+00E2 ISOlat1
		txt = txt.replace('&#227;', "a") # latin small letter a with tilde U+00E3 ISOlat1
		txt = txt.replace('&#228;', "a") # latin small letter a with diaeresis U+00E4 ISOlat1
		txt = txt.replace('&#229;', "a") # latin small letter a with ring above = latin small letter a ring U+00E5 ISOlat1
		txt = txt.replace('&#230;', "ae") # latin small letter ae = latin small ligature ae U+00E6 ISOlat1
		txt = txt.replace('&#231;', "c") # latin small letter c with cedilla U+00E7 ISOlat1
		txt = txt.replace('&#232;', "e") # latin small letter e with grave U+00E8 ISOlat1
		txt = txt.replace('&#233;', "e") # latin small letter e with acute U+00E9 ISOlat1
		txt = txt.replace('&#234;', "e") # latin small letter e with circumflex U+00EA ISOlat1
		txt = txt.replace('&#235;', "e") # latin small letter e with diaeresis U+00EB ISOlat1
		txt = txt.replace('&#236;', "i") # latin small letter i with grave U+00EC ISOlat1
		txt = txt.replace('&#237;', "i") # latin small letter i with acute U+00ED ISOlat1
		txt = txt.replace('&#238;', "i") # latin small letter i with circumflex U+00EE ISOlat1
		txt = txt.replace('&#239;', "i") # latin small letter i with diaeresis U+00EF ISOlat1
		txt = txt.replace('&#240;', "d") # latin small letter eth U+00F0 ISOlat1
		txt = txt.replace('&#241;', "n") # latin small letter n with tilde U+00F1 ISOlat1
		txt = txt.replace('&#242;', "o") # latin small letter o with grave U+00F2 ISOlat1
		txt = txt.replace('&#243;', "o") # latin small letter o with acute U+00F3 ISOlat1
		txt = txt.replace('&#244;', "o") # latin small letter o with circumflex U+00F4 ISOlat1
		txt = txt.replace('&#245;', "o") # latin small letter o with tilde U+00F5 ISOlat1
		txt = txt.replace('&#246;', "o") # latin small letter o with diaeresis U+00F6 ISOlat1
		txt = txt.replace('&#247;', "/") # division sign U+00F7 ISOnum
		txt = txt.replace('&#248;', "o") # latin small letter o with stroke = latin small letter o slash U+00F8 ISOlat1
		txt = txt.replace('&#249;', "u") # latin small letter u with grave U+00F9 ISOlat1
		txt = txt.replace('&#250;', "u") # latin small letter u with acute U+00FA ISOlat1
		txt = txt.replace('&#251;', "u") # latin small letter u with circumflex U+00FB ISOlat1
		txt = txt.replace('&#252;', "u") # latin small letter u with diaeresis U+00FC ISOlat1
		txt = txt.replace('&#253;', "y") # latin small letter y with acute U+00FD ISOlat1
		txt = txt.replace('&#254;', "d") # latin small letter thorn U+00FE ISOlat1
		txt = txt.replace('&#255;', "y") # latin small letter y with diaeresis U+00FF ISOlat1
		txt = txt.replace('&#338;', "OE") # latin capital ligature OE U+0152 ISOlat2
		txt = txt.replace('&#339;', "oe") # latin small ligature oe U+0153 ISOlat2
		txt = txt.replace('&#34;', '"') # quotation mark = APL quote U+0022 ISOnum
		txt = txt.replace('&#352;', "S") # latin capital letter S with caron U+0160 ISOlat2
		txt = txt.replace('&#353;', "s") # latin small letter s with caron U+0161 ISOlat2
		txt = txt.replace('&#376;', "Y") # latin capital letter Y with diaeresis U+0178 ISOlat2
		txt = txt.replace('&#38;', "&") # ampersand U+0026 ISOnum
		txt = txt.replace('&#39;','\'')
		txt = txt.replace('&#402;', "f") # latin small f with hook = function = florin U+0192 ISOtech
		txt = txt.replace('&#60;', "<") # less-than sign U+003C ISOnum
		txt = txt.replace('&#62;', ">") # greater-than sign U+003E ISOnum
		txt = txt.replace('&#710;', "") # modifier letter circumflex accent U+02C6 ISOpub
		txt = txt.replace('&#732;', "~") # small tilde U+02DC ISOdia
		txt = txt.replace('&#8194;', "") # en space U+2002 ISOpub
		txt = txt.replace('&#8195;', " ") # em space U+2003 ISOpub
		txt = txt.replace('&#8201;', " ") # thin space U+2009 ISOpub
		txt = txt.replace('&#8204;', "|") # zero width non-joiner U+200C NEW RFC 2070
		txt = txt.replace('&#8205;', "|") # zero width joiner U+200D NEW RFC 2070
		txt = txt.replace('&#8206;', "") # left-to-right mark U+200E NEW RFC 2070
		txt = txt.replace('&#8207;', "") # right-to-left mark U+200F NEW RFC 2070
		txt = txt.replace('&#8211;', "--") # en dash U+2013 ISOpub
		txt = txt.replace('&#8212;', "---") # em dash U+2014 ISOpub
		txt = txt.replace('&#8216;', '"') # left single quotation mark U+2018 ISOnum
		txt = txt.replace('&#8217;', '"') # right single quotation mark U+2019 ISOnum
		txt = txt.replace('&#8218;', '"') # single low-9 quotation mark U+201A NEW
		txt = txt.replace('&#8220;', '"') # left double quotation mark U+201C ISOnum
		txt = txt.replace('&#8221;', '"') # right double quotation mark U+201D ISOnum
		txt = txt.replace('&#8222;', '"') # double low-9 quotation mark U+201E NEW
		txt = txt.replace('&#8224;', "|") # dagger U+2020 ISOpub
		txt = txt.replace('&#8225;', "||") # double dagger U+2021 ISOpub
		txt = txt.replace('&#8226;', "o") # bullet = black small circle U+2022 ISOpub
		txt = txt.replace('&#8230;', "...") # horizontal ellipsis = three dot leader U+2026 ISOpub
		txt = txt.replace('&#8240;', "%0") # per mille sign U+2030 ISOtech
		txt = txt.replace('&#8242;', "'") # prime = minutes = feet U+2032 ISOtech
		txt = txt.replace('&#8243;', "''") # double prime = seconds = inches U+2033 ISOtech
		txt = txt.replace('&#8249;', '"') # single left-pointing angle quotation mark U+2039 ISO proposed
		txt = txt.replace('&#8250;', '"') # single right-pointing angle quotation mark U+203A ISO proposed
		txt = txt.replace('&#8254;', "-") # overline = spacing overscore U+203E NEW
		txt = txt.replace('&#8260;', "/") # fraction slash U+2044 NEW
		txt = txt.replace('&#8364;', "EU$") # euro sign U+20AC NEW
		txt = txt.replace('&#8465;', "|I") # blackletter capital I = imaginary part U+2111 ISOamso
		txt = txt.replace('&#8472;', "|P") # script capital P = power set = Weierstrass p U+2118 ISOamso
		txt = txt.replace('&#8476;', "|R") # blackletter capital R = real part symbol U+211C ISOamso
		txt = txt.replace('&#8482;', "tm") # trade mark sign U+2122 ISOnum
		txt = txt.replace('&#8501;', "%") # alef symbol = first transfinite cardinal U+2135 NEW
		txt = txt.replace('&#8592;', "<-") # leftwards arrow U+2190 ISOnum
		txt = txt.replace('&#8593;', "^") # upwards arrow U+2191 ISOnum
		txt = txt.replace('&#8594;', "->") # rightwards arrow U+2192 ISOnum
		txt = txt.replace('&#8595;', "v") # downwards arrow U+2193 ISOnum
		txt = txt.replace('&#8596;', "<->") # left right arrow U+2194 ISOamsa
		txt = txt.replace('&#8629;', "<-'") # downwards arrow with corner leftwards = carriage return U+21B5 NEW
		txt = txt.replace('&#8656;', "<=") # leftwards double arrow U+21D0 ISOtech
		txt = txt.replace('&#8657;', "^") # upwards double arrow U+21D1 ISOamsa
		txt = txt.replace('&#8658;', "=>") # rightwards double arrow U+21D2 ISOtech
		txt = txt.replace('&#8659;', "v") # downwards double arrow U+21D3 ISOamsa
		txt = txt.replace('&#8660;', "<=>") # left right double arrow U+21D4 ISOamsa
		txt = txt.replace('&#8764;', "~") # tilde operator = varies with = similar to U+223C ISOtech
		txt = txt.replace('&#8773;', "~=") # approximately equal to U+2245 ISOtech
		txt = txt.replace('&#8776;', "~~") # almost equal to = asymptotic to U+2248 ISOamsr
		txt = txt.replace('&#8800;', "!=") # not equal to U+2260 ISOtech
		txt = txt.replace('&#8801;', "==") # identical to U+2261 ISOtech
		txt = txt.replace('&#8804;', "<=") # less-than or equal to U+2264 ISOtech
		txt = txt.replace('&#8805;', ">=") # greater-than or equal to U+2265 ISOtech
		txt = txt.replace('&#8901;', ".") # dot operator U+22C5 ISOamsb
		txt = txt.replace('&#913;', "Alpha") # greek capital letter alpha U+0391
		txt = txt.replace('&#914;', "Beta") # greek capital letter beta U+0392
		txt = txt.replace('&#915;', "Gamma") # greek capital letter gamma U+0393 ISOgrk3
		txt = txt.replace('&#916;', "Delta") # greek capital letter delta U+0394 ISOgrk3
		txt = txt.replace('&#917;', "Epsilon") # greek capital letter epsilon U+0395
		txt = txt.replace('&#918;', "Zeta") # greek capital letter zeta U+0396
		txt = txt.replace('&#919;', "Eta") # greek capital letter eta U+0397
		txt = txt.replace('&#920;', "Theta") # greek capital letter theta U+0398 ISOgrk3
		txt = txt.replace('&#921;', "Iota") # greek capital letter iota U+0399
		txt = txt.replace('&#922;', "Kappa") # greek capital letter kappa U+039A
		txt = txt.replace('&#923;', "Lambda") # greek capital letter lambda U+039B ISOgrk3
		txt = txt.replace('&#924;', "Mu") # greek capital letter mu U+039C
		txt = txt.replace('&#925;', "Nu") # greek capital letter nu U+039D
		txt = txt.replace('&#926;', "Xi") # greek capital letter xi U+039E ISOgrk3
		txt = txt.replace('&#927;', "Omicron") # greek capital letter omicron U+039F
		txt = txt.replace('&#928;', "Pi") # greek capital letter pi U+03A0 ISOgrk3
		txt = txt.replace('&#929;', "Rho") # greek capital letter rho U+03A1
		txt = txt.replace('&#931;', "Sigma") # greek capital letter sigma U+03A3 ISOgrk3
		txt = txt.replace('&#932;', "Tau") # greek capital letter tau U+03A4
		txt = txt.replace('&#933;', "Upsilon") # greek capital letter upsilon U+03A5 ISOgrk3
		txt = txt.replace('&#934;', "Phi") # greek capital letter phi U+03A6 ISOgrk3
		txt = txt.replace('&#935;', "Chi") # greek capital letter chi U+03A7
		txt = txt.replace('&#936;', "Psi") # greek capital letter psi U+03A8 ISOgrk3
		txt = txt.replace('&#937;', "Omega") # greek capital letter omega U+03A9 ISOgrk3
		txt = txt.replace('&#945;', "alpha") # greek small letter alpha U+03B1 ISOgrk3
		txt = txt.replace('&#946;', "beta") # greek small letter beta U+03B2 ISOgrk3
		txt = txt.replace('&#947;', "gamma") # greek small letter gamma U+03B3 ISOgrk3
		txt = txt.replace('&#948;', "delta") # greek small letter delta U+03B4 ISOgrk3
		txt = txt.replace('&#949;', "epsilon") # greek small letter epsilon U+03B5 ISOgrk3
		txt = txt.replace('&#950;', "zeta") # greek small letter zeta U+03B6 ISOgrk3
		txt = txt.replace('&#951;', "eta") # greek small letter eta U+03B7 ISOgrk3
		txt = txt.replace('&#952;', "theta") # greek small letter theta U+03B8 ISOgrk3
		txt = txt.replace('&#953;', "iota") # greek small letter iota U+03B9 ISOgrk3
		txt = txt.replace('&#954;', "kappa") # greek small letter kappa U+03BA ISOgrk3
		txt = txt.replace('&#955;', "lambda") # greek small letter lambda U+03BB ISOgrk3
		txt = txt.replace('&#956;', "mu") # greek small letter mu U+03BC ISOgrk3
		txt = txt.replace('&#957;', "nu") # greek small letter nu U+03BD ISOgrk3
		txt = txt.replace('&#958;', "xi") # greek small letter xi U+03BE ISOgrk3
		txt = txt.replace('&#959;', "omicron") # greek small letter omicron U+03BF NEW
		txt = txt.replace('&#960;', "pi") # greek small letter pi U+03C0 ISOgrk3
		txt = txt.replace('&#961;', "rho") # greek small letter rho U+03C1 ISOgrk3
		txt = txt.replace('&#962;', "sigma") # greek small letter final sigma U+03C2 ISOgrk3
		txt = txt.replace('&#963;', "sigma") # greek small letter sigma U+03C3 ISOgrk3
		txt = txt.replace('&#964;', "tau") # greek small letter tau U+03C4 ISOgrk3
		txt = txt.replace('&#965;', "upsilon") # greek small letter upsilon U+03C5 ISOgrk3
		txt = txt.replace('&#966;', "phi") # greek small letter phi U+03C6 ISOgrk3
		txt = txt.replace('&#967;', "chi") # greek small letter chi U+03C7 ISOgrk3
		txt = txt.replace('&#968;', "psi") # greek small letter psi U+03C8 ISOgrk3
		txt = txt.replace('&#969;', "omega") # greek small letter omega U+03C9 ISOgrk3
		txt = txt.replace('&#977;', "theta") # greek small letter theta symbol U+03D1 NEW
		txt = txt.replace('&#978;', "upsilon") # greek upsilon with hook symbol U+03D2 NEW
		txt = txt.replace('&#982;', "pi") # greek pi symbol U+03D6 ISOgrk3
		# remove any uncaught &#<number>;
		if find(txt,"&#") >= 0:
			reHash = re.compile('&#.+?;', re.IGNORECASE)
			txt = re.sub(reHash, '', txt)

	if find(txt,'&') >= 0:
		txt = txt.replace('&Aacute;', "A") # latin capital letter A with acute U+00C1 ISOlat1
		txt = txt.replace('&aacute;', "a") # latin small letter a with acute U+00E1 ISOlat1
		txt = txt.replace('&Acirc;', "A") # latin capital letter A with circumflex U+00C2 ISOlat1
		txt = txt.replace('&acirc;', "a") # latin small letter a with circumflex U+00E2 ISOlat1
		txt = txt.replace('&acute;', " ") # acute accent = spacing acute U+00B4 ISOdia
		txt = txt.replace('&AElig;', "AE") # latin capital letter AE = latin capital ligature AE U+00C6 ISOlat1
		txt = txt.replace('&aelig;', "ae") # latin small letter ae = latin small ligature ae U+00E6 ISOlat1
		txt = txt.replace('&Agrave;', "A") # latin capital letter A with grave = latin capital letter A grave U+00C0 ISOlat1
		txt = txt.replace('&agrave;', "a") # latin small letter a with grave = latin small letter a grave U+00E0 ISOlat1
		txt = txt.replace('&alefsym;', "%") # alef symbol = first transfinite cardinal U+2135 NEW
		txt = txt.replace('&Alpha;', "Alpha") # greek capital letter alpha U+0391
		txt = txt.replace('&alpha;', "alpha") # greek small letter alpha U+03B1 ISOgrk3
		txt = txt.replace('&amp;amp;','&')
		txt = txt.replace('&amp;;','&')
		txt = txt.replace('&amp;', "&") # ampersand U+0026 ISOnum		
		txt = txt.replace('&amp','&')		
		txt = txt.replace('&apos;', "'")
		txt = txt.replace('&Aring;', "A") # latin capital letter A with ring above = latin capital letter A ring U+00C5 ISOlat1
		txt = txt.replace('&aring;', "a") # latin small letter a with ring above = latin small letter a ring U+00E5 ISOlat1
		txt = txt.replace('&asymp;', "~~") # almost equal to = asymptotic to U+2248 ISOamsr
		txt = txt.replace('&Atilde;', "A") # latin capital letter A with tilde U+00C3 ISOlat1
		txt = txt.replace('&atilde;', "a") # latin small letter a with tilde U+00E3 ISOlat1
		txt = txt.replace('&auml;', "a")
		txt = txt.replace('&Auml;', "A")
		txt = txt.replace('&Auml;', "A") # latin capital letter A with diaeresis U+00C4 ISOlat1
		txt = txt.replace('&auml;', "a") # latin small letter a with diaeresis U+00E4 ISOlat1
		txt = txt.replace('&bdquo;', '"') # double low-9 quotation mark U+201E NEW
		txt = txt.replace('&Beta;', "Beta") # greek capital letter beta U+0392
		txt = txt.replace('&beta;', "beta") # greek small letter beta U+03B2 ISOgrk3
		txt = txt.replace('&brvbar;', "|") # broken bar = broken vertical bar U+00A6 ISOnum
		txt = txt.replace('&bull;', "o") # bullet = black small circle U+2022 ISOpub
		txt = txt.replace('&Ccedil;', "C") # latin capital letter C with cedilla U+00C7 ISOlat1
		txt = txt.replace('&ccedil;', "c") # latin small letter c with cedilla U+00E7 ISOlat1
		txt = txt.replace('&cedil;', " ") # cedilla = spacing cedilla U+00B8 ISOdia
		txt = txt.replace('&cent;', "c") # cent sign U+00A2 ISOnum
		txt = txt.replace('&Chi;', "Chi") # greek capital letter chi U+03A7
		txt = txt.replace('&chi;', "chi") # greek small letter chi U+03C7 ISOgrk3
		txt = txt.replace('&circ;', "") # modifier letter circumflex accent U+02C6 ISOpub
		txt = txt.replace('&cong;', "~=") # approximately equal to U+2245 ISOtech
		txt = txt.replace('&copy;', "(c)") # copyright sign U+00A9 ISOnum
		txt = txt.replace('&crarr;', "<-'") # downwards arrow with corner leftwards = carriage return U+21B5 NEW
		txt = txt.replace('&curren;', "$") # currency sign U+00A4 ISOnum
		txt = txt.replace('&dagger;', "|") # dagger U+2020 ISOpub
		txt = txt.replace('&Dagger;', "||") # double dagger U+2021 ISOpub
		txt = txt.replace('&darr;', "v") # downwards arrow U+2193 ISOnum
		txt = txt.replace('&dArr;', "v") # downwards double arrow U+21D3 ISOamsa
		txt = txt.replace('&deg;', "o") # degree sign U+00B0 ISOnum
		txt = txt.replace('&Delta;', "Delta") # greek capital letter delta U+0394 ISOgrk3
		txt = txt.replace('&delta;', "delta") # greek small letter delta U+03B4 ISOgrk3
		txt = txt.replace('&divide;', "/") # division sign U+00F7 ISOnum
		txt = txt.replace('&Eacute;', "E") # latin capital letter E with acute U+00C9 ISOlat1
		txt = txt.replace('&eacute;', "e") # latin small letter e with acute U+00E9 ISOlat1
		txt = txt.replace('&Ecirc;', "E") # latin capital letter E with circumflex U+00CA ISOlat1
		txt = txt.replace('&ecirc;', "e") # latin small letter e with circumflex U+00EA ISOlat1
		txt = txt.replace('&Egrave;', "E") # latin capital letter E with grave U+00C8 ISOlat1
		txt = txt.replace('&egrave;', "e") # latin small letter e with grave U+00E8 ISOlat1
		txt = txt.replace('&emsp;', " ") # em space U+2003 ISOpub
		txt = txt.replace('&ensp;', " ") # en space U+2002 ISOpub
		txt = txt.replace('&Epsilon;', "Epsilon") # greek capital letter epsilon U+0395
		txt = txt.replace('&epsilon;', "epsilon") # greek small letter epsilon U+03B5 ISOgrk3
		txt = txt.replace('&equiv;', "==") # identical to U+2261 ISOtech
		txt = txt.replace('&Eta;', "Eta") # greek capital letter eta U+0397
		txt = txt.replace('&eta;', "eta") # greek small letter eta U+03B7 ISOgrk3
		txt = txt.replace('&ETH;', "D") # latin capital letter ETH U+00D0 ISOlat1
		txt = txt.replace('&eth;', "d") # latin small letter eth U+00F0 ISOlat1
		txt = txt.replace('&Euml;', "E") # latin capital letter E with diaeresis U+00CB ISOlat1
		txt = txt.replace('&euml;', "e") # latin small letter e with diaeresis U+00EB ISOlat1
		txt = txt.replace('&euro;', "EU$") # euro sign U+20AC NEW
		txt = txt.replace('&fnof;', "f") # latin small f with hook = function = florin U+0192 ISOtech
		txt = txt.replace('&frac12;', "1/2") # vulgar fraction one half = fraction one half U+00BD ISOnum
		txt = txt.replace('&frac14;', "1/4") # vulgar fraction one quarter = fraction one quarter U+00BC ISOnum
		txt = txt.replace('&frac34;', "3/4") # vulgar fraction three quarters = fraction three quarters U+00BE ISOnum
		txt = txt.replace('&frasl;', "/") # fraction slash U+2044 NEW
		txt = txt.replace('&Gamma;', "Gamma") # greek capital letter gamma U+0393 ISOgrk3
		txt = txt.replace('&gamma;', "gamma") # greek small letter gamma U+03B3 ISOgrk3
		txt = txt.replace('&ge;', ">=") # greater-than or equal to U+2265 ISOtech
		txt = txt.replace('&gt;', ">") # greater-than sign U+003E ISOnum
		txt = txt.replace('&hArr;', "<=>") # left right double arrow U+21D4 ISOamsa
		txt = txt.replace('&harr;', "<->") # left right arrow U+2194 ISOamsa
		txt = txt.replace('&hellip;', "...") # horizontal ellipsis = three dot leader U+2026 ISOpub
		txt = txt.replace('&Iacute;', "I") # latin capital letter I with acute U+00CD ISOlat1
		txt = txt.replace('&iacute;', "i") # latin small letter i with acute U+00ED ISOlat1
		txt = txt.replace('&Icirc;', "I") # latin capital letter I with circumflex U+00CE ISOlat1
		txt = txt.replace('&icirc;', "i") # latin small letter i with circumflex U+00EE ISOlat1
		txt = txt.replace('&iexcl;', "!") # inverted exclamation mark U+00A1 ISOnum
		txt = txt.replace('&Igrave;', "E") # latin capital letter I with grave U+00CC ISOlat1
		txt = txt.replace('&igrave;', "i") # latin small letter i with grave U+00EC ISOlat1
		txt = txt.replace('&image;', "|I") # blackletter capital I = imaginary part U+2111 ISOamso
		txt = txt.replace('&Iota;', "Iota") # greek capital letter iota U+0399
		txt = txt.replace('&iota;', "iota") # greek small letter iota U+03B9 ISOgrk3
		txt = txt.replace('&iquest;', "?") # inverted question mark = turned question mark U+00BF ISOnum
		txt = txt.replace('&Iuml;', "I") # latin capital letter I with diaeresis U+00CF ISOlat1
		txt = txt.replace('&iuml;', "i") # latin small letter i with diaeresis U+00EF ISOlat1
		txt = txt.replace('&Kappa;', "Kappa") # greek capital letter kappa U+039A
		txt = txt.replace('&kappa;', "kappa") # greek small letter kappa U+03BA ISOgrk3
		txt = txt.replace('&Lambda;', "Lambda") # greek capital letter lambda U+039B ISOgrk3
		txt = txt.replace('&lambda;', "lambda") # greek small letter lambda U+03BB ISOgrk3
		txt = txt.replace('&laquo;', '"') # left-pointing double angle quotation mark = left pointing guillemet U+00AB ISOnum
		txt = txt.replace('&larr;', "<-") # leftwards arrow U+2190 ISOnum
		txt = txt.replace('&lArr;', "<=") # leftwards double arrow U+21D0 ISOtech
		txt = txt.replace('&ldquo;', '"') # left double quotation mark U+201C ISOnum
		txt = txt.replace('&le;', "<=") # less-than or equal to U+2264 ISOtech
		txt = txt.replace('&lrm;', "") # left-to-right mark U+200E NEW RFC 2070
		txt = txt.replace('&lsaquo;', '"') # single left-pointing angle quotation mark U+2039 ISO proposed
		txt = txt.replace('&lsquo;', '"') # left single quotation mark U+2018 ISOnum
		txt = txt.replace('&lt;', "<") # less-than sign U+003C ISOnum
		txt = txt.replace('&macr;', "-") # macron = spacing macron = overline = APL overbar U+00AF ISOdia
		txt = txt.replace('&mdash;', "---") # em dash U+2014 ISOpub
		txt = txt.replace('&micro;', "u") # micro sign U+00B5 ISOnum
		txt = txt.replace('&middot;', ".") # middle dot = Georgian comma = Greek middle dot U+00B7 ISOnum
		txt = txt.replace('&Mu;', "Mu") # greek capital letter mu U+039C
		txt = txt.replace('&mu;', "mu") # greek small letter mu U+03BC ISOgrk3
		txt = txt.replace('&nbsp;&nbsp;',' ')
		txt = txt.replace('&nbsp;', " ") # no-break space = non-breaking space U+00A0 ISOnum
		txt = txt.replace('&ndash;', "--") # en dash U+2013 ISOpub
		txt = txt.replace('&ne;', "!=") # not equal to U+2260 ISOtech
		txt = txt.replace('&not;', "-.") # not sign U+00AC ISOnum
		txt = txt.replace('&Ntilde;', "N") # latin capital letter N with tilde U+00D1 ISOlat1
		txt = txt.replace('&ntilde;', "n") # latin small letter n with tilde U+00F1 ISOlat1
		txt = txt.replace('&Nu;', "Nu") # greek capital letter nu U+039D
		txt = txt.replace('&nu;', "nu") # greek small letter nu U+03BD ISOgrk3
		txt = txt.replace('&Oacute;', "O") # latin capital letter O with acute U+00D3 ISOlat1
		txt = txt.replace('&oacute;', "o") # latin small letter o with acute U+00F3 ISOlat1
		txt = txt.replace('&Ocirc;', "O") # latin capital letter O with circumflex U+00D4 ISOlat1
		txt = txt.replace('&ocirc;', "o") # latin small letter o with circumflex U+00F4 ISOlat1
		txt = txt.replace('&OElig;', "OE") # latin capital ligature OE U+0152 ISOlat2
		txt = txt.replace('&oelig;', "oe") # latin small ligature oe U+0153 ISOlat2
		txt = txt.replace('&Ograve;', "O") # latin capital letter O with grave U+00D2 ISOlat1
		txt = txt.replace('&ograve;', "o") # latin small letter o with grave U+00F2 ISOlat1
		txt = txt.replace('&oline;', "-") # overline = spacing overscore U+203E NEW
		txt = txt.replace('&Omega;', "Omega") # greek capital letter omega U+03A9 ISOgrk3
		txt = txt.replace('&omega;', "omega") # greek small letter omega U+03C9 ISOgrk3
		txt = txt.replace('&Omicron;', "Omicron") # greek capital letter omicron U+039F
		txt = txt.replace('&omicron;', "omicron") # greek small letter omicron U+03BF NEW
		txt = txt.replace('&ordf;', "e") # feminine ordinal indicator U+00AA ISOnum
		txt = txt.replace('&ordm;', "o") # masculine ordinal indicator U+00BA ISOnum
		txt = txt.replace('&Oslash;', "O") # latin capital letter O with stroke = latin capital letter O slash U+00D8 ISOlat1
		txt = txt.replace('&oslash;', "o") # latin small letter o with stroke = latin small letter o slash U+00F8 ISOlat1
		txt = txt.replace('&Otilde;', "O") # latin capital letter O with tilde U+00D5 ISOlat1
		txt = txt.replace('&otilde;', "o") # latin small letter o with tilde U+00F5 ISOlat1
		txt = txt.replace('&Ouml;', "O") # latin capital letter O with diaeresis U+00D6 ISOlat1
		txt = txt.replace('&ouml;', "o") # latin small letter o with diaeresis U+00F6 ISOlat1
		txt = txt.replace('&para;', "|p") # pilcrow sign = paragraph sign U+00B6 ISOnum
		txt = txt.replace('&permil;', "%0") # per mille sign U+2030 ISOtech
		txt = txt.replace('&Phi;', "Phi") # greek capital letter phi U+03A6 ISOgrk3
		txt = txt.replace('&phi;', "phi") # greek small letter phi U+03C6 ISOgrk3
		txt = txt.replace('&Pi;', "Pi") # greek capital letter pi U+03A0 ISOgrk3
		txt = txt.replace('&pi;', "pi") # greek small letter pi U+03C0 ISOgrk3
		txt = txt.replace('&piv;', "pi") # greek pi symbol U+03D6 ISOgrk3
		txt = txt.replace('&plusmn;', "+-") # plus-minus sign = plus-or-minus sign U+00B1 ISOnum
		txt = txt.replace('&pound;', "p") # pound sign U+00A3 ISOnum
		txt = txt.replace('&Prime;', "''") # double prime = seconds = inches U+2033 ISOtech
		txt = txt.replace('&prime;', "'") # prime = minutes = feet U+2032 ISOtech
		txt = txt.replace('&Psi;', "Psi") # greek capital letter psi U+03A8 ISOgrk3
		txt = txt.replace('&psi;', "psi") # greek small letter psi U+03C8 ISOgrk3
		txt = txt.replace('&quot;', '"') # quotation mark = APL quote U+0022 ISOnum
		txt = txt.replace('&raquo;', '"') # right-pointing double angle quotation mark = right pointing guillemet U+00BB ISOnum
		txt = txt.replace('&rArr;', "=>") # rightwards double arrow U+21D2 ISOtech
		txt = txt.replace('&rarr;', "->") # rightwards arrow U+2192 ISOnum
		txt = txt.replace('&rdquo;', '"') # right double quotation mark U+201D ISOnum
		txt = txt.replace('&real;', "|R") # blackletter capital R = real part symbol U+211C ISOamso
		txt = txt.replace('&reg;', "(R)") # registered sign = registered trade mark sign U+00AE ISOnum
		txt = txt.replace('&Rho;', "Rho") # greek capital letter rho U+03A1
		txt = txt.replace('&rho;', "rho") # greek small letter rho U+03C1 ISOgrk3
		txt = txt.replace('&rlm;', "") # right-to-left mark U+200F NEW RFC 2070
		txt = txt.replace('&rsaquo;', '"') # single right-pointing angle quotation mark U+203A ISO proposed
		txt = txt.replace('&rsquo;', '"') # right single quotation mark U+2019 ISOnum
		txt = txt.replace('&sbquo;', '"') # single low-9 quotation mark U+201A NEW
		txt = txt.replace('&Scaron;', "S") # latin capital letter S with caron U+0160 ISOlat2
		txt = txt.replace('&scaron;', "s") # latin small letter s with caron U+0161 ISOlat2
		txt = txt.replace('&sdot;', ".") # dot operator U+22C5 ISOamsb
		txt = txt.replace('&sect;', "S") # section sign U+00A7 ISOnum
		txt = txt.replace('&shy;', "-") # soft hyphen = discretionary hyphen U+00AD ISOnum
		txt = txt.replace('&Sigma;', "Sigma") # greek capital letter sigma U+03A3 ISOgrk3
		txt = txt.replace('&sigma;', "sigma") # greek small letter sigma U+03C3 ISOgrk3
		txt = txt.replace('&sigmaf;', "sigma") # greek small letter final sigma U+03C2 ISOgrk3
		txt = txt.replace('&sim;', "~") # tilde operator = varies with = similar to U+223C ISOtech
		txt = txt.replace('&sup1;', "1") # superscript one = superscript digit one U+00B9 ISOnum
		txt = txt.replace('&sup2;', "2") # superscript two = superscript digit two = squared U+00B2 ISOnum
		txt = txt.replace('&sup3;', "3") # superscript three = superscript digit three = cubed U+00B3 ISOnum
		txt = txt.replace('&szlig;', "SS") # latin small letter sharp s = ess-zed U+00DF ISOlat1
		txt = txt.replace('&Tau;', "Tau") # greek capital letter tau U+03A4
		txt = txt.replace('&tau;', "tau") # greek small letter tau U+03C4 ISOgrk3
		txt = txt.replace('&Theta;', "Theta") # greek capital letter theta U+0398 ISOgrk3
		txt = txt.replace('&theta;', "theta") # greek small letter theta U+03B8 ISOgrk3
		txt = txt.replace('&thetasym;', "theta") # greek small letter theta symbol U+03D1 NEW
		txt = txt.replace('&thinsp;', " ") # thin space U+2009 ISOpub
		txt = txt.replace('&THORN;', "D") # latin capital letter THORN U+00DE ISOlat1
		txt = txt.replace('&thorn;', "d") # latin small letter thorn U+00FE ISOlat1
		txt = txt.replace('&tilde;', "~") # small tilde U+02DC ISOdia
		txt = txt.replace('&times;', "x") # multiplication sign U+00D7 ISOnum
		txt = txt.replace('&trade;', "tm") # trade mark sign U+2122 ISOnum
		txt = txt.replace('&Uacute;', "U") # latin capital letter U with acute U+00DA ISOlat1
		txt = txt.replace('&uacute;', "u") # latin small letter u with acute U+00FA ISOlat1
		txt = txt.replace('&uarr;', "^") # upwards arrow U+2191 ISOnum
		txt = txt.replace('&uArr;', "^") # upwards double arrow U+21D1 ISOamsa
		txt = txt.replace('&Ucirc;', "U") # latin capital letter U with circumflex U+00DB ISOlat1
		txt = txt.replace('&ucirc;', "u") # latin small letter u with circumflex U+00FB ISOlat1
		txt = txt.replace('&Ugrave;', "U") # latin capital letter U with grave U+00D9 ISOlat1
		txt = txt.replace('&ugrave;', "u") # latin small letter u with grave U+00F9 ISOlat1
		txt = txt.replace('&uml;', "''") # diaeresis = spacing diaeresis U+00A8 ISOdia
		txt = txt.replace('&upsih;', "upsilon") # greek upsilon with hook symbol U+03D2 NEW
		txt = txt.replace('&Upsilon;', "Upsilon") # greek capital letter upsilon U+03A5 ISOgrk3
		txt = txt.replace('&upsilon;', "upsilon") # greek small letter upsilon U+03C5 ISOgrk3
		txt = txt.replace('&Uuml;', "U") # latin capital letter U with diaeresis U+00DC ISOlat1
		txt = txt.replace('&uuml;', "u") # latin small letter u with diaeresis U+00FC ISOlat1
		txt = txt.replace('&weierp;', "P") # script capital P = power set = Weierstrass p U+2118 ISOamso
		txt = txt.replace('&Xi;', "Xi") # greek capital letter xi U+039E ISOgrk3
		txt = txt.replace('&xi;', "xi") # greek small letter xi U+03BE ISOgrk3
		txt = txt.replace('&Yacute;', "Y") # latin capital letter Y with acute U+00DD ISOlat1
		txt = txt.replace('&yacute;', "y") # latin small letter y with acute U+00FD ISOlat1
		txt = txt.replace('&yen;', "y") # yen sign = yuan sign U+00A5 ISOnum
		txt = txt.replace('&Yuml;', "Y") # latin capital letter Y with diaeresis U+0178 ISOlat2
		txt = txt.replace('&yuml;', "y") # latin small letter y with diaeresis U+00FF ISOlat1
		txt = txt.replace('&Zeta;', "Zeta") # greek capital letter zeta U+0396
		txt = txt.replace('&zeta;', "zeta") # greek small letter zeta U+03B6 ISOgrk3
		txt = txt.replace('&zwj;', "|") # zero width joiner U+200D NEW RFC 2070
		txt = txt.replace('&zwnj;', " ") # zero width non-joiner U+200C NEW RFC 2070

	if find(txt,'\\u') >= 0:
		txt = txt.replace("\\u0027", "'").replace("\\u0022",'"').replace("\\u0026","&").replace('\\u003c','<').replace('\\u003e','>')

	if removeNewLines:
		txt = txt.replace('\n','')
		txt = txt.replace('\r','')

	return txt

#################################################################################################################
def color_score( score):
	log("> color_score() %s" % score)
	try:
		score = int(score)
		score_full = "%d/100" % score
	except:
		# text score, convert to a value so it can be coloured
		score_full = score
		if score in ('Favorable', 'Outstanding'):
			score = 61
		elif score == 'Mixed':
			score = 40
		elif score == 'Unfavorable':
			score = 0
		else:
			score = -1

	# colour according to rating
	if score >= 61:
		score_rated = LABEL_COLOUR_GREEN % score_full
	elif score >= 40:
		score_rated = LABEL_COLOUR_YELLOW % score_full
	elif score >= 0:
		score_rated = LABEL_COLOUR_RED % score_full
	else:
		score_rated = LABEL_COLOUR_NONE % score_full
	log("< color_score() %s" % score_rated)
	return score_rated
