"""
 bbbLib.py

 General functions.
 
"""

import sys, os.path
import xbmc, xbmcgui
import os, re, unicodedata, traceback
import urllib, urllib2
from string import strip, replace, find, rjust
import sgmllib
from xml.dom.minidom import parse, parseString
from shutil import rmtree
import cookielib
import zipstream

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "bbbLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '28-08-2008'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

DIR_HOME = sys.modules[ "__main__" ].DIR_HOME

# setup cookiejar
cookiejar = cookielib.LWPCookieJar()       # This is a subclass of FileCookieJar that has useful load and save methods
urlopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
urllib2.install_opener(urlopener)

# KEYPAD CODES
ACTION_UNKNOWN			= 0
ACTION_MOVE_LEFT 	    = 1 	# Dpad
ACTION_MOVE_RIGHT	    = 2		# Dpad
ACTION_MOVE_UP		    = 3		# Dpad
ACTION_MOVE_DOWN	    = 4		# Dpad
ACTION_SCROLL_UP		= 5		# trigger up
ACTION_SCROLL_DOWN		= 6		# trigger down
ACTION_A	            = 7     # A
ACTION_HIGHLIGHT_ITEM	= 8		#
ACTION_B	            = 9     # B
ACTION_BACK	            = 10	# back btn
ACTION_REMOTE_INFO		= 11	# info on remote
ACTION_REMOTE_PAUSE		= 12	# remote
ACTION_REMOTE_STOP		= 13	# remote
ACTION_REMOTE_NEXT_ITEM	= 14	# remote Skip Next
ACTION_REMOTE_PREV_ITEM	= 15	# remote Skip Previous
ACTION_X 	            = 18    # X
ACTION_Y 	            = 34	# Y
ACTION_LEFT_TRIGGER		= 111	# trigger left
ACTION_RIGHT_TRIGGER	= 112	# trigger right
ACTION_WHITE	        = 117	# white button
ACTION_LEFT_STICK       = 85   # left stick clicked in
ACTION_RIGHT_STICK      = 122   # right stick clicked in
ACTION_RIGHT_STICK_UP	= 88
ACTION_RIGHT_STICK_DOWN	= 89
ACTION_RIGHT_STICK_RIGHT= 124
ACTION_RIGHT_STICK_LEFT	= 125
ACTION_REMOTE_RECORD	= 2010  # record button on remote - assigned in keymap.xml

PAD_A                        = 256
PAD_B                        = 257
PAD_X                        = 258
PAD_Y                        = 259
PAD_BLACK                    = 260
PAD_WHITE                    = 261
PAD_LEFT_TRIGGER             = 262
PAD_RIGHT_TRIGGER            = 263
PAD_LEFT_STICK              = 264
PAD_RIGHT_STICK             = 265
PAD_RIGHT_STICK_UP          = 266 # right thumb stick directions
PAD_RIGHT_STICK_DOWN        = 267 # for defining different actions per direction
PAD_RIGHT_STICK_LEFT        = 268
PAD_RIGHT_STICK_RIGHT       = 269
PAD_DPAD_UP                  = 270
PAD_DPAD_DOWN                = 271
PAD_DPAD_LEFT                = 272
PAD_DPAD_RIGHT               = 273
PAD_START                    = 274
PAD_BACK                     = 275
PAD_LEFT_STICK              = 276
PAD_RIGHT_STICK             = 277
PAD_LEFT_ANALOG_TRIGGER      = 278
PAD_RIGHT_ANALOG_TRIGGER= 279
PAD_LEFT_STICK_UP           = 280 # left thumb stick  directions
PAD_LEFT_STICK_DOWN         = 281 # for defining different actions per direction
PAD_LEFT_STICK_LEFT         = 282
PAD_LEFT_STICK_RIGHT        = 283

REMOTE_LEFT             = 169
REMOTE_RIGHT            = 168
REMOTE_UP               = 166   
REMOTE_DOWN             = 167
REMOTE_1                = 206
REMOTE_4                = 203
REMOTE_INFO             = 195
REMOTE_BACK				= 216

KEYBOARD_LEFT          = 61477 
KEYBOARD_UP            = 61478 
KEYBOARD_RIGHT         = 61479 
KEYBOARD_DOWN          = 61480
KEYBOARD_PLUS          = 61627 
KEYBOARD_PG_UP         = 61473 
KEYBOARD_PG_DOWN        = 61474
KEYBOARD_INSERT         = 61485
KEYBOARD_X              = 61528
KEYBOARD_A              = 61505
KEYBOARD_B              = 61506
KEYBOARD_Y              = 61529
KEYBOARD_NUM_PLUS       = 61547
KEYBOARD_NUM_MINUS      = 61549
KEYBOARD_ESC            = 61467
KEYBOARD_RETURN         = 61453
KEYBOARD_HOME           = 61476
KEYBOARD_DEL_BACK       = 61448


# ACTION CODE GROUPS
CLICK_A = ( ACTION_A, PAD_A, KEYBOARD_A, KEYBOARD_RETURN, )
CLICK_B = ( ACTION_B, PAD_B, KEYBOARD_B, )
CLICK_X = ( ACTION_X, PAD_X, KEYBOARD_X, ACTION_REMOTE_STOP, )
CLICK_Y = ( ACTION_Y, PAD_Y, KEYBOARD_Y, )
SELECT_ITEM = CLICK_A
EXIT_SCRIPT = ( ACTION_BACK, PAD_BACK, REMOTE_BACK, KEYBOARD_ESC, )
CANCEL_DIALOG = CLICK_B
CONTEXT_MENU = ( ACTION_WHITE, PAD_WHITE, ACTION_REMOTE_INFO, REMOTE_INFO, KEYBOARD_HOME,)
LEFT_STICK_CLICK = (ACTION_LEFT_STICK, PAD_LEFT_STICK, )
RIGHT_STICK_CLICK = (ACTION_RIGHT_STICK, PAD_RIGHT_STICK, )
MOVEMENT_DPAD = ( ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP, ACTION_MOVE_DOWN, )
MOVEMENT_RIGHT_STICK = (PAD_RIGHT_STICK_UP, PAD_RIGHT_STICK_DOWN, PAD_RIGHT_STICK_LEFT, PAD_RIGHT_STICK_RIGHT, ACTION_RIGHT_STICK_UP,ACTION_RIGHT_STICK_DOWN,ACTION_RIGHT_STICK_LEFT,ACTION_RIGHT_STICK_RIGHT, )
MOVEMENT_LEFT_STICK = (PAD_LEFT_STICK_UP, PAD_LEFT_STICK_DOWN, PAD_LEFT_STICK_LEFT, PAD_LEFT_STICK_RIGHT, )
MOVEMENT_STICKS = MOVEMENT_RIGHT_STICK + MOVEMENT_LEFT_STICK
MOVEMENT_SCROLL_UP = ( ACTION_LEFT_TRIGGER, PAD_LEFT_ANALOG_TRIGGER, ACTION_SCROLL_UP, KEYBOARD_PG_UP, PAD_LEFT_TRIGGER, ACTION_REMOTE_PREV_ITEM, )
MOVEMENT_SCROLL_DOWN = ( ACTION_RIGHT_TRIGGER, PAD_RIGHT_ANALOG_TRIGGER, ACTION_SCROLL_DOWN, KEYBOARD_PG_DOWN, PAD_RIGHT_TRIGGER, ACTION_REMOTE_NEXT_ITEM, )
MOVEMENT_SCROLL = MOVEMENT_SCROLL_UP + MOVEMENT_SCROLL_DOWN
MOVEMENT_KEYBOARD = ( KEYBOARD_LEFT, KEYBOARD_UP, KEYBOARD_RIGHT, KEYBOARD_DOWN, KEYBOARD_PG_UP, KEYBOARD_PG_DOWN, )
MOVEMENT_REMOTE = ( REMOTE_LEFT, REMOTE_RIGHT, REMOTE_UP, REMOTE_DOWN, ACTION_REMOTE_NEXT_ITEM, ACTION_REMOTE_PREV_ITEM, )
MOVEMENT_UP = ( ACTION_MOVE_UP, PAD_LEFT_STICK_UP, PAD_RIGHT_STICK_UP, PAD_DPAD_UP, KEYBOARD_UP, REMOTE_UP, ACTION_RIGHT_STICK_UP,)
MOVEMENT_DOWN = ( ACTION_MOVE_DOWN, PAD_LEFT_STICK_DOWN,PAD_RIGHT_STICK_DOWN, PAD_DPAD_DOWN, KEYBOARD_DOWN, REMOTE_DOWN, ACTION_RIGHT_STICK_DOWN,)
MOVEMENT_LEFT = ( ACTION_MOVE_LEFT, PAD_LEFT_STICK_LEFT, PAD_RIGHT_STICK_LEFT,PAD_DPAD_LEFT, KEYBOARD_LEFT, REMOTE_LEFT, ACTION_RIGHT_STICK_LEFT,)
MOVEMENT_RIGHT = (  ACTION_MOVE_RIGHT, PAD_LEFT_STICK_RIGHT, PAD_RIGHT_STICK_RIGHT, PAD_DPAD_RIGHT, KEYBOARD_RIGHT, REMOTE_RIGHT, ACTION_RIGHT_STICK_RIGHT, )
MOVEMENT = MOVEMENT_UP + MOVEMENT_DOWN + MOVEMENT_LEFT + MOVEMENT_RIGHT + MOVEMENT_SCROLL + MOVEMENT_KEYBOARD + MOVEMENT_REMOTE

XBFONT_LEFT       = 0x00000000
XBFONT_RIGHT      = 0x00000001
XBFONT_CENTER_X   = 0x00000002
XBFONT_CENTER_Y   = 0x00000004
XBFONT_TRUNCATED  = 0x00000008

KBTYPE_ALPHA = -1
KBTYPE_NUMERIC = 0
KBTYPE_DATE = 1
KBTYPE_TIME = 2
KBTYPE_IP = 3
KBTYPE_SMB = 4      # not a real kbtype, just a common value
KBTYPE_YESNO = 5    # not a real kbtype, just a common value

# xbmc skin FONT NAMES
FONT10 = 'font10'
FONT11 = 'font11'
FONT12 = 'font12'
FONT13 = 'font13'
FONT14 = 'font14'
FONT16 = 'font16'
FONT18 = 'font18'
FONT_SPECIAL_10 = 'special10'
FONT_SPECIAL_11 = 'special11'
FONT_SPECIAL_12 = 'special12'
FONT_SPECIAL_13 = 'special13'
FONT_SPECIAL_14 = 'special14'
ALL_FONTS = (FONT10,FONT11,FONT12,FONT13,FONT14,FONT16,FONT18,FONT_SPECIAL_10,FONT_SPECIAL_11,FONT_SPECIAL_12,FONT_SPECIAL_13,FONT_SPECIAL_14,)

REGEX_URL_PREFIX = '^((?:http://|www).+?)[/?]'

global dialogProgress
dialogProgress = xbmcgui.DialogProgress()
REZ_W = 720
REZ_H = 576

#######################################################################################################################    
# DEBUG - display indented information
#######################################################################################################################    
DEBUG = True
debugIndentLvl = 0	# current indentation level
def debug( value ):
	global debugIndentLvl
	if (DEBUG and value):
		try:
			if value[0] == ">": debugIndentLvl += 2
			pad = rjust("", debugIndentLvl)
			print pad + str(value)
			if value[0] == "<": debugIndentLvl -= 2
		except:
			try:
				print value
			except:
				print "Debug() Bad chars in string"

#################################################################################################################
def messageOK(title='', line1='', line2='',line3=''):
	debug("%s\n%s\n%s\n%s" % (title, line1,line2,line3))
	xbmcgui.Dialog().ok(title ,line1,line2,line3)

#################################################################################################################
def dialogOK(title, line1='', line2='',line3=''):
	xbmcgui.Dialog().ok(title ,line1,line2,line3)

#################################################################################################################
def handleException(txt=''):
	try:
		title = "EXCEPTION: " + txt
		e=sys.exc_info()
		list = traceback.format_exception(e[0],e[1],e[2],3)
		text = ''
		for l in list:
			text += l
#		print text
		messageOK(title, text)
	except: pass

#################################################################################################################
def makeScriptDataDir():
	try:
		scriptPath = os.path.join("T:\script_data", __scriptname__)
		os.makedirs(scriptPath)
		debug("makeScriptDataDir() created=%s" % scriptPath )
		return True
	except:
		return False

#############################################################################################################
def makeDir(dir):
	try:
		os.makedirs( dir )
		debug("bbbLib.created dir: " + dir)
		return True
	except:
		return False

#############################################################################################################
def removeDir(dir, title="", msg="", msg2="", force=False):
	if force or xbmcgui.Dialog().yesno(title, msg, msg2):
		try:
			rmtree(dir,ignore_errors=True)
			debug("removeDir() done %s" % dir)
		except: pass
	
#################################################################################################################
# delete a single file
def deleteFile(filename):
	try:
		os.remove(filename)
		debug("bbbLib.file deleted: " + filename)
	except: pass

#################################################################################################################
def readFile(filename):
	try:
		return file(filename).read()
	except:
		return ""

#################################################################################################################
def fileExist(filename):
	exist = False
	try:
		if os.path.isfile(filename) and os.path.getsize(filename) > 0:
			exist = True
	except: pass
	return exist

#################################################################################################################
def isFileNewer(oldFilename, newFilename):
	new = True
	try:
		# returns secs since epoch
		oldFileTime = os.path.getmtime(oldFilename)
		newFileTime = os.path.getmtime(newFilename)
		new = (newFileTime > oldFileTime)
	except: pass
	return new

##############################################################################################
def doKeyboard(currentValue='', heading='', kbType=KBTYPE_ALPHA):
	debug("doKeyboard() kbType=%s" % kbType)
	if currentValue == None:
		currentValue = ''
	value = currentValue
	if kbType == KBTYPE_ALPHA:
		keyboard = xbmc.Keyboard(currentValue, heading)
		keyboard.doModal()
		if keyboard.isConfirmed:
			value = keyboard.getText().strip()
		else:
			value = None
	else:
		d = xbmcgui.Dialog()
		value = d.numeric(kbType, heading, currentValue)

	return value

##############################################################################################
# if current and skinned resolutions differ and skinned resolution is not
# 1080i or 720p (they have no 4:3), calculate widescreen offset
##############################################################################################
def setResolution(win):
	try:
		# '1080i'=0, '720p'=1, '480p'=2, '480p16x9'=3, 'ntsc'=4, 'ntsc16x9'=5, 'pal'=6, 'pal16x9'=7, 'pal60'=8, 'pal6016x9'=9}
		rez = 6		# PAL
		currRez = win.getResolution()
		if (currRez != rez) and rez > 1:
			# If resolutions differ calculate widescreen offset
			# check if current resolution is 16x9
			if (currRez == 0 or currRez % 2): iCur16x9 = 1
			else: iCur16x9 = 0

			# check if skinned resolution is 16x9
			if (rez == 0 or rez % 2): iSkin16x9 = 1
			else: iSkin16x9 = 0

			# calculate offset
			offset = iCur16x9 - iSkin16x9
			rez += offset
	except:
		handleException()

	win.setCoordinateResolution(rez)
	debug("setResolution() curr Rez=" + str(currRez) + " new Rez="+str(rez))

#######################################################################################################################    
def parseDocList(doc, regex, startStr='', endStr=''):
	if not doc: return []
	# find section
	startPos = -1
	endPos = -1
	if startStr:
		startPos = find(doc,startStr)
		if startPos == -1:
			print "parseDocList() start not found " + startStr

	if endStr:
		endPos = find(doc, endStr, startPos+1)
		if endPos == -1:
			print "parseDocList() end not found " + endStr

	if startPos < 0:
		startPos = 0
	if endPos < 0 or endPos <= startPos:
		endPos = len(doc)-1

	# do regex on section
	try:
		findRe = re.compile(regex, re.DOTALL + re.MULTILINE + re.IGNORECASE)
		matchList = findRe.findall(doc[startPos:endPos])
	except:
		matchList = []

	if matchList:
		sz = len(matchList)
	else:
		sz = 0
	debug( "parseDocList() matches=%s" % sz)
	return matchList

#################################################################################################################
# look for html between < and > chars and remove it
def cleanHTML(data, breaksToNewline=False):
	if not data: return ""
	try:
		if breaksToNewline:
			data = data.replace('<br>','\n').replace('<p>','\n')
		reobj = re.compile('<.+?>', re.IGNORECASE+re.DOTALL+re.MULTILINE)
		return (re.sub(reobj, '', data)).strip()
	except:
		return data

#################################################################################################################
def ErrorCode(e):
	debug("> ErrorCode()")
	print "except=%s" % e
	if hasattr(e, 'code'):
		code = e.code
	else:
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
	debug("< ErrorCode()")

#################################################################################################################
# Class to return a char or string pixel length. Thanks to madtw.
# Until truncation of labels on ControlButtons is working.
#################################################################################################################
class FontAttr:
	def __init__(self):
		# w/s rez multiplier, 0 - 1080i (1920x1080), 1 - 720p (1280x720)
		self.rezAdjust = {0 : 2.65, 1 : 1.77}
		self.fonts = {'font10': 9, 'font11':9, 'font12':10, 'font13':11, 'font14':12, 'font16':13, 'font18': 13, \
					  'special10':9, 'special11':9, 'special12':11, 'special13':12, 'special14':12, 'special16':13, 'special18':13}
		
	def truncate(self, maxWidth, text, font, rez = 6):
#		print "FontAttr() orig maxWidth=%s %s %s %s" % (maxWidth, font, rez, text)
		try:
			maxWidth *= self.rezAdjust[rez]
		except: pass
		try:
			fontW =  self.fonts[font.lower()]
		except:
			fontW = 11
		shortFontW = 8

		for i in range(len(text), 0, -1):
			newText = text[:i]
			shortChCount = newText.count('i')+ newText.count('l') + newText.count('t') + newText.count(' ') + \
						   newText.count('r')
			otherChCount = len(newText) - shortChCount
			strW = (otherChCount * fontW) + (shortChCount * shortFontW)
			if strW <= maxWidth:
#				print "FontAttr() %s %s maxWidth=%s  strW=%s  shortChCount=%s otherChCount=%s" % (fontW, newText, maxWidth, strW, shortChCount,otherChCount)
				break

		return newText

#################################################################################################################
class FontAttr_old:
	def __init__(self):
		# w/s rez multiplier, 0 - 1080i (1920x1080), 1 - 720p (1280x720)
		self.rezAdjust = {0 : 2.65, 1 : 1.77}	
		self.adjust = {'font10':-.2, 'font11':0, 'font12':.1, 'font13':.1, 'font14':.1, 'font16':1, 'font18':2, \
					   'special10':-.1, 'special11':0, 'special12':2, 'special13':2.5, 'special14':3, 'special16':4, 'special18':5}

		# base widths based on font14
		self.width = [ \
			0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
			0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
			0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
			#       SP   !   "   #   $   %   &   '
			0,  0,  6,  6,  8, 14, 10, 19, 13,  4,
			#(   )   *   +   ,   -   .   /   0   1
			7,  7, 24, 14,  6,  7,  6,  7, 10, 10,
			#2   3   4   5   6   7   8   9   :  ;
			10, 10, 10, 10, 10, 10, 10, 10,  7,  7,
			#<   =   >   ?   @   A   B   C   D   E
			14, 14, 14,  9, 17, 11, 11, 11, 13, 11,
			#F   G   H   I   J   K   L   M   N   O
			10, 13, 13,  7,  8, 11,  9, 15, 13, 13,
			#P   Q   R   S   T   U   V   W   X   Y
			10, 13, 12, 11, 11, 12, 11, 17, 11, 11,
			#Z   [   \   ]   ^   _   `   a   b   c
			11,  7,  7,  7, 14, 10, 10, 10, 11,  9,
			#d   e   f   g   h   i   j   k   l   m
			11, 10,  6, 11, 11,  4,  5,  9,  4, 16,
			#n   o   p   q   r   s   t   u   v   w
			11, 10, 11, 11,  7,  8,  6, 11,  9, 14,
			#x   y   z   {   |   }   ~
			9,  9,  8,  9,  7,  9, 14
		]

	def getWidth( self, c, font ):
		try:
			w = self.width[ord(c)] + self.adjust[font]
		except:
			w = 14			# unknown ch, use avg width
		return w

	def getTextWidth(self, txt, font):
		len = 0
		for c in txt:
			len += self.getWidth(c, font)
		return int(len)

	def truncate(self, maxWidth, text, font, rez = 6):
		chCount = len(text)
		maxWidth = int(maxWidth)
		font = font.lower()
		try:
			maxWidth *= self.rezAdjust[rez]
		except: pass
			
		newText = ''
		for i in range(chCount, 0, -1):
			if self.getTextWidth(text[0:i], font) <= maxWidth:
				newText = text[0:i]
				break

		return newText

#################################################################################################################
# Convert a text string containing &#x<hex_value> to ascii ch
#################################################################################################################
def urlTextToASCII(text):
	if not text: return ""
	try:
		compile_obj = re.compile('(&#x(.*?);)',  re.IGNORECASE + re.MULTILINE + re.DOTALL)
		match_obj = compile_obj.findall(text)
		for match in match_obj:
			ch = chr(int('0x'+match[1], 16))
			text = text.replace(match[0], ch)

		compile_obj = re.compile('(&#(\d+);)',  re.IGNORECASE + re.MULTILINE + re.DOTALL)
		match_obj = compile_obj.findall(text)
		for match in match_obj:
			ch = chr(int(match[1]))
			text = text.replace(match[0], ch)
	except:
		debug("bbbLib.urlTextToASCII() exception")
	return text


#################################################################################################################
# Thanks to Arboc for this
#################################################################################################################
def unicodeToAscii(text, charset='utf8'):
	if not text: return ""
	try:
		newtxt = text.decode(charset)
		newtxt = unicodedata.normalize('NFKD', newtxt).encode('ASCII','replace')
		return newtxt
	except:
		return text

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

	if removeNewLines:
		txt = txt.replace('\n','')
		txt = txt.replace('\r','')

	return txt


#################################################################################################################
def isFloat(s):
	try:
		float(s)
		return True
	except:
		return False

#################################################################################################################
def isInt(s):
	try:
		int(s)
		return True
	except:
		return False

#################################################################################################################
# if success: returns the html page given in url as a string
# else: return -1 for Exception None for HTTP timeout, '' for empty page otherwise page data
#################################################################################################################
def fetchURL(url, file='', params='', headers={}, isBinary=False, encodeURL=True):
	debug("> bbbLib.fetchURL() isBinary=%s encodeURL=%s" % (isBinary, encodeURL))
	if encodeURL:
		safe_url = urllib.quote_plus(url,'/:&?=+#@')
	else:
		safe_url = url
	if not safe_url.startswith('http://'):
		safe_url = 'http://' + safe_url

	def _report_hook( count, blocksize, totalsize ):
		# just update every x%
		if count and totalsize:
			percent = int( float( count * blocksize * 100) / totalsize )
			if (percent % 5) == 0:
				dialogProgress.update( percent )
		if ( dialogProgress.iscanceled() ):
			debug("fetchURL() iscanceled()")
			raise "Cancel"

	success = False
	data = None
	if not file:
		# create temp file if needed
		file = os.path.join(os.getcwd().replace( ";", "" ), "temp.html")

	# remove destination file if exists already
	deleteFile(file)

	# fetch from url
	try:
		opener = urllib.FancyURLopener()

		# add headers if supplied
		if headers:
			if not headers.has_key('User-Agent')  and not headers.has_key('User-agent'):
				headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			for name, value  in headers.items():
				opener.addheader(name, value)

		if DEBUG:
			print "safe_url=%s" % safe_url
			print "file=%s" % file
			print "params=%s" % params
			print "headers=%s" % headers

		if params:
			fn, resp = opener.retrieve(safe_url, file, _report_hook, data=params)
		else:
			fn, resp = opener.retrieve(safe_url, file, _report_hook)

		if DEBUG:
			print resp
			showCookies()

		content_type = resp["Content-Type"].lower()
		# fail if expecting an image but not corrent type returned
		if isBinary and (find(content_type,"text") != -1):
			raise "Not Binary"

		opener.close()
		del opener
		urllib.urlcleanup()
	except IOError, errobj:
		ErrorCode(errobj)
	except "Not Binary":
		debug("Returned Non Binary content")
		data = False
	except "Cancel":
		debug("download cancelled")
	except:
		handleException("fetchURL()")
	else:
		if not isBinary:
			data = readFile(file)		# read retrieved file
		else:
			data = fileExist(file)		# check image file exists

		if data:
			success = True

	debug( "< fetchURL success=%s" % success)
	return data

#################################################################################################################
# fetch using urllib2 and Cookies
#################################################################################################################
def fetchCookieURL(url, fn='', params=None, headers={}, isBinary=False, encodeURL=True, newRequest=True):
	debug("> bbbLib.fetchCookieURL() isBinary=%s encodeURL=%s newRequest=%s" % (isBinary, encodeURL,newRequest))
	if encodeURL:
		safe_url = urllib.quote_plus(url,'/:&?=+#@')
	else:
		safe_url = url
	if not safe_url.startswith('http://'):
		safe_url = 'http://' + safe_url

	data = None
	handle = None
	if fn:
		deleteFile(fn)		# remove destination file if exists already

	try:
		if DEBUG:
			print "safe_url=%s" % safe_url
			print "fn=%s" % fn
			print "params=%s" % params
			print "headers=%s" % headers

		if newRequest:
			debug("create new Request")
			if not headers.has_key('User-Agent') and not headers.has_key('User-agent'):
				headers['User-Agent'] = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			req = urllib2.Request(safe_url, params, headers)       # create a request object
			handle = urllib2.urlopen(req)
		else:
			handle = urllib2.urlopen(safe_url)					# open new url using existing req
		debug("Request done")

		if DEBUG:
			print handle.info()
			showCookies()

		debug("reading from url ...")
		data = handle.read()

	except IOError, errobj:
		ErrorCode(errobj)
	except:
		handleException("fetchCookieURL()")
	else:
		# write to file if required
		if fn and data:
			if isBinary:
				mode = "wb"
			else:
				mode = "w"
			debug("writing data to file, mode=%s ..." % mode)
			try:
				f = open(fn,mode)
				f.write(data)
				f.flush()
				f.close()
				del f

				handle.fp._sock.recv=None # hacky avoidance of uncleared handles bug
				handle.close()
				del handle
				if isBinary:
					data = True
			except:
				handleException()
				data = None

	success = (data != '' and data != None and data != False)
	debug("< bbbLib.fetchCookieURL() %s" % success)
	return data


#################################################################################################################
def showCookies():
	try:
		for index, cookie in enumerate(cookiejar):
			print "cookie %i = %s" % (index, cookie)
	except: 
		print "no cookiejar"


#################################################################################################################
# extract URL and name from data
def extractURLName(data):
	# URL and name
	link = ''
	name = ''
	matches = re.search("href=[\"'](.*?)[\"'].*?>(.*?)<", data, re.IGNORECASE)
	if matches:
		link = matches.group(1)
		name = matches.group(2)
	else:
		name = cleanHTML(data)
	return link, name

#################################################################################################################
def searchRegEx(data, regex, flags=re.IGNORECASE):
	try:
		value = re.search(regex, data, flags).group(1)
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
#	debug ("findAllRegEx() matches= " + str(sz))
	return matchList

#############################################################################################################
def safeFilename(path, replaceCh='_'):
#	head, tail = os.path.split(path.replace( "\\", "/" ))
	head, tail = os.path.split(path)
	name, ext = os.path.splitext(tail)
	return  os.path.join(head, cleanPunctuation(name, replaceCh) + ext)

#################################################################################################################
def cleanPunctuation(text, replaceCh='_'):
	try:
		return re.sub(r'[\'\";:?*<>|+\\/,=!\.]', replaceCh, text)
	except:
		debug("cleanPunctuation() re failed")
		return text

#################################################################################################################
# Does a direct image URL exist in string ?
def isImageURL(url):
	match = re.search('([^"\'<>]+)(?<=(?:\.gif|\.jpg|\.bmp|\.png))', url, re.IGNORECASE)
	try:
		url = match.group(1)
	except:
		url = ''
	debug("bbbLib.isImageURL() " + str(url != ''))
	return url

#################################################################################################################
def isRSSLink(url):
	return searchRegEx(url, '(rss|rdf|xml)$')

#################################################################################################################
def isHTMLLink(url):
	return searchRegEx(url, '(html|htm)$')

######################################################################################
def loadFileObj( filename, dataType={} ):
    debug( "loadFileObj() " + filename)
    try:
        file_handle = open( filename, "r" )
        loadObj = eval( file_handle.read() )
        file_handle.close()
    except:
        # reset to empty according to dataType
        if isinstance(dataType, dict):
            loadObj = {}
        elif isinstance(dataType, list) or isinstance(dataType, tuple):
            loadObj = ()
        else:
            loadObj = None
    return loadObj

######################################################################################
def saveFileObj( filename, saveObj ):
    debug( "saveFileObj() " + filename)
    try:
        file_handle = open( filename, "w" )
        file_handle.write( repr( saveObj ) )
        file_handle.close()
    except:
        handleException( "_save_file_obj()" )

#################################################################################################################
def listDir(path, ext='', fnRE='', getFullFilename=False, lower=False, upper=False):
	debug("> bbbLib.listDir() path=%s ext=%s full=%s lower=%s upper=%s" % (path, ext, getFullFilename, lower, upper))

	fileList = []
	if ext:
		ext = ext.lower()
		if ext[0] != '.':
			ext = '.'+ext

	if os.path.isdir(path):
		files = os.listdir(path)
		for f in files:
			fn, ex = os.path.splitext(f)
			if not ext or ex.lower() == ext:
				found = True
				if fnRE:
					matches = re.search(fnRE, fn, re.IGNORECASE)
					if not matches:
						found = False

				if found:
					if getFullFilename:
						filename = f
					else:
						filename = fn

					if lower:
						fileList.append(filename.lower())
					elif upper:
						fileList.append(filename.upper())
					else:
						fileList.append(filename)

	debug("< bbbLib.listDir() file count=%s" % len(fileList))
	return fileList


#################################################################################################################
# RSS Parser, copes with badly formed data
# Thanks to www.xml.com
#################################################################################################################
class RSSParserSMGL(sgmllib.SGMLParser):
	def reset(self):
		self.items = []
		self.currentTag = None
		self.lastTag = None
		self.currentValue = ''
		self.initem = 0
		sgmllib.SGMLParser.reset(self)

	def start_item(self, attrs):
		# set a flag that we're within an RSS item now
		self.items.append({})
		self.initem = 1

	def end_item(self):
		# OK, we're out of the RSS item
		self.initem = 0

	def unknown_starttag(self, tag, attrs):
		self.currentTag = tag

	def unknown_endtag(self, tag):
		# if we're within an RSS item, save the data we've buffered
		if self.initem:
			# decode entities and strip whitespace
			self.currentValue = decodeEntities(self.currentValue.strip())
			self.items[-1][self.currentTag] = self.currentValue
		self.currentValue = ''

	def handle_data(self, data):
		# buffer all text data
#		self.currentValue += data
		self.currentValue += data.decode('latin-1')

	def handle_entityref(self, data):
		# buffer all entities
		self.currentValue += '&' + data
	handle_charref = handle_entityref

# Parser that parses version 2.0 RSS documents
# enhanced to now find required name in tag attributes
class RSSParser2:
	def __init__(self):
		debug("RSSParser2().init()")

	# feeds the xml document from given url or file to the parser
	def feed(self, url="", file="", doc="", title=""):
		debug("> RSSParser2().feed()")
		success = False
		self.dom = None

		if url:
			debug("parseString from URL")
			if not file:
				dir = os.getcwd().replace(';','')
				file = os.path.join(dir, "temp.xml")
			doc = fetchCookieURL(url, file)
		elif file:
			debug("parseString from FILE " + file)
			doc = readFile(file)
		else:
			debug("parseString from DOC")

		if doc:
			success = self.__parseString(doc)

		debug("< RSSParser2().feed() success: " + str(success))
		return success

	def __parseString(self, xmlDocument):
		debug("> RSSParser2().__parseString()")
		success = True
		try:
			self.dom = parseString(xmlDocument.encode( "utf-8" ))
		except UnicodeDecodeError:
			try:
				debug("__parseString() UnicodeDecodeError, try unicodeToAscii")
				self.dom = parseString(unicodeToAscii(xmlDocument))
			except:
				try:
					debug("__parseString() unicodeToAscii failed - try without encoding")
					self.dom = parseString(xmlDocument)
				except:
					debug("__parseString() failure - give up!")
					handleException()
					success = False
		except:
			success = False

		if not self.dom:
			messageOK("XML Parser Failed","Empty/Bad XML file","Unable to parse data.")
			success = False

		debug("< RSSParser2().__parseString() success=%s" % success)
		return success


	# parses RSS document items and returns an list of objects
	def __parseElements(self, tagName, elements, elementDict):
		debug("> RSSParser2().__parseElements() element count=%s" % len(elements))

		# extract required attributes from element attribute
		def _get_element_attributes(el, attrNameList):
			attrDataList = {}
			for attrName in attrNameList:
				data = el.getAttribute( attrName )
				if data:
					attrDataList[attrName] = data
			return attrDataList
		
		objectsList = []
		for index, el in enumerate(elements):
			dict = {}
			# check element attributes
			elAttrItems = el.attributes.items()

			# get data from item with attributes
			if elAttrItems and elementDict.has_key(tagName):
				attrDataList= _get_element_attributes(el, elementDict[tagName])
				if attrDataList:
					dict[tagName] = attrDataList

			# get data from item
			for elTagName, attrNameList in elementDict.items():
				if elTagName == tagName:
					# skip element tagName - already processed it attributes
					continue

				data = None

				try:
					# get value for tag (without any attributes)
					data = el.getElementsByTagName(elTagName)[0].childNodes[0].data
				except:
					try:
						# get required attributes from tag
						subEl = el.getElementsByTagName(elTagName)[0]
						attrItems = subEl.attributes.items()
						data = _get_element_attributes(subEl, attrNameList)
					except: pass

				if data:
#					debug("Tag: %s = %s" % (elTagName, data)
					dict[elTagName] = data
#				else:
#					debug("Tag: %s No Data found" % (elTagName, )

#			if DEBUG:
#				print "%s %s" % (index, dict)
			objectsList.append(RSSNode(dict))

		debug("< RSSParser2().__parseElements() No. objects=%s" % len(objectsList))
		return objectsList


	# parses the RSS document
	def parse(self, tagName, elementDict):
		debug("> RSSParser2().parse() tagName: %s %s" % (tagName,elementDict))

		parsedList = None
		if self.dom:
			try:
				elements = self.dom.getElementsByTagName(tagName)
				parsedList = self.__parseElements(tagName, elements, elementDict)
			except:
				debug("exception No parent elements found for tagName")

		debug("< RSSParser2().parse()")
		return parsedList

#################################################################################################################
class RSSNode:
	def __init__(self, elements):
		self.elements = elements
		
	def getElement(self, element):
		try:
			return self.elements[element]
		except:
			return ""
		
	def getElementNames(self):
		return self.elements.keys()
		
	def hasElement(self, element):
		return self.elements.has_key(element)

#############################################################################################################
# detect if using MC360 style skin - any theme
def isMC360():
	skinName = getSkinName()
	is360 = (find(skinName,'360') >= 0)
	debug("bbbLib.isMC360() " +str(is360))
	return is360

#############################################################################################################
def getSkinName():
	skinName = os.path.basename(xbmc.getSkinDir())
	debug("bbbLib.getSkinName() skinName="+skinName)
	return skinName


#################################################################################################################
def isIP(host):
	return re.match('^\d+\.\d+\.\d+\.\d+$', host)

#################################################################################################################
def getReadmeFilename():
    debug("> getReadmeFilename()")
    filename = "readme.txt"
    base_path, language = getLanguagePath()
    fn = os.path.join( base_path, language, filename)
    if not fileExist( fn ):
        fn = os.path.join( base_path, "English", filename )

    debug("< getReadmeFilename() %s" % fn)
    return fn

#######################################################################################################################    
def prefixDirPath(fn, dirPath):
	if not fn.startswith(dirPath):
		return os.path.join(dirPath, fn)
	return fn

#############################################################################################################
# pluginType = music, video, pictures
def installPlugin(pluginType, name='', checkOnly=True):
	debug("> installPlugin() %s %s checkOnly=%s"  % (pluginType, name, checkOnly))
	exists = False
	if not name:
		name = __scriptname__
	name += " Plugin"

	try:
		copyFromPath = xbmc.translatePath( os.path.join( DIR_HOME, "Plugin" ) )
		copyFromFile = os.path.join( copyFromPath, 'default.py')
		copyToPath = xbmc.translatePath( os.path.join( "Q:\\", "plugins", pluginType, name ) )
		copyToFile = os.path.join( copyToPath, 'default.py')

		# set not exist if; path/file missing or previous installed is older
		copyFromFileSecs = os.path.getmtime(copyFromFile)
		copyToFileSecs = os.path.getmtime(copyToFile)
		debug( "comparing fromSecs %d  toSecs %d"  % (copyFromFileSecs, copyToFileSecs))
		exists = fileExist(copyToFile) and copyFromFileSecs <= copyToFileSecs
	except:
		debug( "paths dont exist. This is OK if we're just checking" )

	if not checkOnly:
		# do installation
		try:
			from shutil import copytree, rmtree
			try:
				rmtree( copyToPath,ignore_errors=True )
			except: pass
			copytree( copyFromPath, copyToPath )
			dialogOK(__scriptname__, "In plugins 'Add Source' to complete installation.", name)
		except:
			msg = "Plugin Failed\n" + str(sys.exc_info()[ 1 ])
			dialogOK(__scriptname__, msg)

	debug("< installPlugin() exists=%s" % exists)
	return exists

##############################################################################################################    
def validMAC(mac):
    valid = False
    if mac and len(mac) >= 11 and len(mac) <= 17:
        if ':' in mac:
            ch = ':'
        elif '-' in mac:
            ch = '-'
        elif '.' in mac:
            ch = '.'
        else:
            ch = ''
            debug("mac seperator missing")
        if ch and len(mac.split(ch)) == 6:
            valid = True
    debug("validMAC() %s" % valid)
    return valid

##############################################################################################################    
def playMedia(filename):
	debug("> playMedia() " + filename)
	success = False

	try:
		xbmc.Player().play(filename)
		success = xbmc.Player().isPlaying()
	except:
		debug('xbmc.Player().play() failed trying xbmc.PlayMedia() ')
		try:
			cmd = 'xbmc.PlayMedia(%s)' % filename
			xbmc.executebuiltin(cmd)
			success = True
		except:
			handleException('xbmc.PlayMedia()')

	debug("< playMedia() success=%s" % success)
	return success

##############################################################################################################    
def logFreeMem(msg=""):
    mem = xbmc.getFreeMem()
    debug( "Freemem=%sMB  %s" % (mem, msg))
    return mem

##############################################################################################################    
# sub all non-alpha chars for '-'
def alphaOnlyText(text, subChar='-'):
	newText = ''
	for ch in text:
		if not ch.isalpha():
			newText += subChar
		else:
			newText += ch
	return newText

##############################################################################################################    
def getLanguagePath():
	try:
		base_path = os.path.join( os.getcwd().replace(';',''), 'resources', 'language' )
		language = xbmc.getLanguage()
		langPath = os.path.join( base_path, language )
		if not os.path.exists(langPath):
			debug("getLanguagePath() not exist: " + langPath)
			raise
	except:
		language = 'English'
	debug("getLanguagePath() path=%s lang=%s" % ( base_path, language ))
	return base_path, language

#################################################################################################################
def unzip(extract_path, filename, silent=False, msg=""):
	""" unzip an archive, using ChunkingZipFile to write large files as chunks if necessery """
	debug("> unzip() extract_path=%s fn=%s" % (extract_path, filename))
	success = False
	cancelled = False
	installed_path = ""

	zip=zipstream.ChunkingZipFile(filename, 'r')
	namelist = zip.namelist()
	infos=zip.infolist()
	max_files = len(namelist)
	debug("max_files=%s" % max_files)

	for file_count, entry in enumerate(namelist):
		debug("%i entry=%s" % (file_count, entry))
		info = infos[file_count]

		if not silent:
			percent = int( file_count * 100.0 / max_files )
			root, name = os.path.split(entry)
			dialogProgress.update( percent, msg, root, name)
			if ( dialogProgress.iscanceled() ):
				cancelled = True
				break

		filePath = os.path.join(extract_path, entry)
		if filePath.endswith('/'):
			if not os.path.isdir(filePath):
				os.makedirs(filePath)
		elif (info.file_size + info.compress_size) > 25000000:
			debug( "LARGE FILE: f sz=%s  c sz=%s  reqd sz=%s %s" % (info.file_size, info.compress_size, (info.file_size + info.compress_size), entry ))
			outfile=file(filePath, 'wb')
			fp=zip.readfile(entry)
			fread=fp.read
			ftell=fp.tell
			owrite=outfile.write
			size=info.file_size

			# write out in chunks
			while ftell() < size:
				hunk=fread(4096)
				owrite(hunk)

			outfile.flush()
			outfile.close()
		else:
			file(filePath, 'wb').write(zip.read(entry))

	if not cancelled:
		success = True
		if namelist[0][-1] in ('\\/'):
			namelist[0] = namelist[0][-1]
		installed_path = os.path.join(extract_path, namelist[0])
	
	zip.close()
	del zip
	debug("< unzip() success=%s installed_path=%s" % (success, installed_path))
	return success, installed_path

