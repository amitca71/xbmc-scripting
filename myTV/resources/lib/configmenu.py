"""
 ConfigMenu - show and set settings for myTV
"""

import xbmc, xbmcgui
import sys, os.path
from bbbLib import *
from bbbGUILib import DialogSelect
from mytvLib import *
from bbbSkinGUILib import TextBoxDialogXML
import mytvGlobals

__language__ = sys.modules[ "__main__" ].__language__
DIR_HOME = sys.modules[ "__main__" ].DIR_HOME     			# should be in default.py

#######################################################################################################################    
# CONFIG MENU
#######################################################################################################################    
class ConfigMenu:
	def __init__(self):
		debug("> ConfigMenu() init()")

		self.TITLE = 0
		self.FUNC = 1
		self.REINIT_REQUIRED = 2
		self.CONFIG_KEY = 3

		# init config file
		self.selectedPos = 0
		debug("< ConfigMenu() init()")

	def createMenuList(self):
		debug("> ConfigMenu().createMenuList()")

		# menu choices [title, func, reInit epg, config file setting name, config value]
		MENU_REC_CONFIG_DS = [__language__(532), configDataSource,mytvGlobals.INIT_FULL]
		MENU_REC_CONFIG_SP = [__language__(534), configSaveProgramme,mytvGlobals.INIT_FULL]
		MENU_REC_TIMER_CLASH = [__language__(538), configTimerClash, mytvGlobals.INIT_NONE, MYTVConfig.KEY_SYSTEM_TIMER_CLASH_CHECK]
		self.menu = [
			[__language__(500)],
			[__language__(530), clearCache, mytvGlobals.INIT_FULL],
			[__language__(531), changeDataSource,mytvGlobals.INIT_FULL_NOW, MYTVConfig.KEY_SYSTEM_DATASOURCE],
			MENU_REC_CONFIG_DS,
			[__language__(533), selectSaveProgramme,mytvGlobals.INIT_FULL_NOW, MYTVConfig.KEY_SYSTEM_SAVE_PROG],
			MENU_REC_CONFIG_SP,
			MENU_REC_TIMER_CLASH,
			[__language__(536), configClock, mytvGlobals.INIT_DISPLAY, MYTVConfig.KEY_SYSTEM_CLOCK],
			[__language__(539), configChannelName, mytvGlobals.INIT_DISPLAY, MYTVConfig.KEY_SYSTEM_SHOW_CH_ID],
			[__language__(540), configReorderChannels, mytvGlobals.INIT_FULL],
			[__language__(541), ConfigEPGColours().ask, mytvGlobals.INIT_DISPLAY],
			[__language__(544), configFonts().ask, mytvGlobals.INIT_DISPLAY],
			[__language__(542), ConfigGenreIcons().ask, mytvGlobals.INIT_PART],
			[__language__(543), ConfigGenreColours().ask, mytvGlobals.INIT_PART],
			[__language__(545), configEPGRows, mytvGlobals.INIT_DISPLAY],
			[__language__(557), configShowDSSP, mytvGlobals.INIT_DISPLAY, MYTVConfig.KEY_SYSTEM_SHOW_DSSP],
			[__language__(546), configSMB, mytvGlobals.INIT_NONE],
			[__language__(547), configEditTemplate, mytvGlobals.INIT_NONE, MYTVConfig.KEY_SYSTEM_SAVE_TEMPLATE],
			[__language__(548), ProgrammeSaveTemplate().viewTemplates,mytvGlobals.INIT_NONE],
			[__language__(549), configLSOTV, mytvGlobals.INIT_NONE, MYTVConfig.KEY_SYSTEM_USE_LSOTV],
			[__language__(555), configWOL, mytvGlobals.INIT_NONE, MYTVConfig.KEY_SYSTEM_WOL],
			[__language__(556), downloadLogos, mytvGlobals.INIT_DISPLAY],
			[__language__(553), configScriptUpdateCheck, mytvGlobals.INIT_NONE, MYTVConfig.KEY_SYSTEM_CHECK_UPDATE],
			[__language__(554), updateScript, mytvGlobals.INIT_NONE],
			[__language__(550), viewReadme, mytvGlobals.INIT_NONE],
			[__language__(551), viewChangelog, mytvGlobals.INIT_NONE],
			[__language__(552), mytvGlobals.config.reset, mytvGlobals.INIT_FULL]
			]

		# remove unwanted options
		# option config DS only if needed
		if not canDataSourceConfig():
			self.menu.remove(MENU_REC_CONFIG_DS)

		# tv card SAVEPROG related options
		if not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG):
			self.menu.remove(MENU_REC_CONFIG_SP)
			self.menu.remove(MENU_REC_TIMER_CLASH)

		list = []
		for menuItem in self.menu:
			label2=''
			label = menuItem[self.TITLE]
			# read in config setting if this menu item is a config setting
			try:
				key = menuItem[self.CONFIG_KEY]
				value = mytvGlobals.config.getSystem(key)
				if key == MYTVConfig.KEY_SYSTEM_SAVE_PROG:
					if not value:
						label2 = MYTVConfig.VALUE_SAVE_PROG_NOTV
				elif key == MYTVConfig.KEY_SYSTEM_SHOW_CH_ID:
					if value == '0':
						label2 = __language__(577)		# no ch name or id
					elif value == '2':
						label2 = __language__(561)		# show ch id
					elif value == '3':
						label2 = __language__(562)		# show alt ch id
					else:
						label2 = __language__(560)		# ch name only
				else:
					label2 = ''

				if not label2:
					label2 = mytvGlobals.config.configHelper.boolToYesNo(value)
			except:
				label2 = ''
			list.append(xbmcgui.ListItem(label, label2=label2))

		
		debug("< ConfigMenu().createMenuList() list sz: " + str(len(list)))
		return list

	def ask(self):
		debug("> ConfigMenu().ask()")
		# show this dialog and wait until it's closed

		reInit = mytvGlobals.INIT_NONE
		selectedPos = 0
		while True:
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(502), width=550, rows=len(menuList), banner=LOGO_FILENAME, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
				break # exit selected

			# exec func associated with menu option (if has one)
			if self.menu[selectedPos][self.FUNC]:
				done = self.menu[selectedPos][self.FUNC]()							# call menu func

				# force exit if updating script
				if done and self.menu[selectedPos][0] == __language__(554):         # update script
					# restart script after update
					deleteCacheFiles(0)
					xbmc.executebuiltin('XBMC.RunScript(%s)'%(os.path.join(DIR_HOME, 'default.py')))
					sys.exit(0)	                                                    # end current instance
			else:
				done = True

			# set reInit status if still false.
			# this allows setting to persist
			if done:
				optInitLevel = self.menu[selectedPos][self.REINIT_REQUIRED]
				debug("func complete, optInitLevel=" + str(optInitLevel))
				if optInitLevel > reInit:
					reInit = optInitLevel	# save highest reinit level

				# exit back to epg for reInint now for some options
				if optInitLevel == mytvGlobals.INIT_FULL_NOW:
					debug("options requires exit menu to epg now")
					break

		debug("< ConfigMenu().ask() reInit=%s" % reInit)
		return reInit

#################################################################################################################
def changeDataSource():
	debug("> changeDataSource()")

	changed = selectDataSource()
	if changed:
		mytvGlobals.mytvFavShows.deleteSaved()
		mytvGlobals.mytvFavShows = None
	
	debug("< changeDataSource()")
	return changed

#################################################################################################################
def configChannelName():
	debug("> configChannelName()")
	changed = False
	# exit, No Channel name, No IDs, ID, alt.ID
	menuList = [__language__(500), __language__(577), __language__(560), __language__(561), __language__(562)]

	# popup dialog to select choice
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(539), rows=len(menuList), width=270, panel=mytvGlobals.DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menuList)
	if selectedPos > 0:	
		# 0 no ch names or id
		# 1 no ch id shown
		# 2 ch id
		# 3 alt ch id
		changed = mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_SHOW_CH_ID, selectedPos-1)

	debug("< configChannelName() changed=%s" % changed)
	return changed

#################################################################################################################
def configFetchTimersStartup():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_FETCH_TIMERS_STARTUP)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_FETCH_TIMERS_STARTUP, value)
	return True

#################################################################################################################
def configScriptUpdateCheck():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_CHECK_UPDATE)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_CHECK_UPDATE, value)
	return True

#################################################################################################################
def configTimerClash():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_TIMER_CLASH_CHECK)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_TIMER_CLASH_CHECK, value)
	return True

#################################################################################################################
# MENU ITEM - Is LiveSportOnTV MainMenu option visible in main menu
#################################################################################################################
def configLSOTV():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_USE_LSOTV)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_USE_LSOTV, value)
	return True

#################################################################################################################
# Show SP and DS names
#################################################################################################################
def configShowDSSP():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SHOW_DSSP)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_SHOW_DSSP, value)
	return True


#################################################################################################################
# MENU ITEM - Use 12 or 24hr clock and epg intervals
#################################################################################################################
def configClock():
	value = not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_CLOCK)
	mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_CLOCK, value)
	return True

############################################################################################################
def configSMB(reset=True):
    debug("> configSMB() reset=%s" % reset)
    success = False
    isLibLoaded = sys.modules.has_key('smbLib')
    if not isLibLoaded:
        from smbLib import ConfigSMB

    cSMB = ConfigSMB(__language__(976))
    while not success:
        if not reset:
            smbDetails = cSMB.checkAll(silent=True)
            if smbDetails:
                success = True
            elif not xbmcgui.Dialog().yesno(__language__(959), __language__(309)):
                break

        if not success or reset:
            cSMB.ask()
            reset = False	# allows changes to be checked

    if not isLibLoaded: # wasnt loaded at beginning so ok to remove
        del sys.modules['smbLib']
    debug("< myTV.configSMB() success= %s" % success)
    return success

#################################################################################################################
def viewReadme():
	debug("> viewReadme()")
	fn = getReadmeFilename()
	doc = readFile(fn)
	if not doc:
		doc = "File not found: " + fn
	tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
	tbd.ask(__language__(550), doc)
	del tbd
	debug("< viewReadme()")

#################################################################################################################
def viewChangelog():
	debug("> viewChangelog()")
	fn = os.path.join(DIR_HOME, "Changelog.txt")
	doc = readFile(fn)
	if not doc:
		doc = "File not found: " + fn
	tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
	tbd.ask(__language__(551), doc)
	del tbd
	debug("< viewChangelog()")

#################################################################################################################
def configReorderChannels():
	debug("> configReorderChannels()")

	def isHiddenText(text):
		if text[0] == '*':					# * indicates HIDDEN
			text = __language__(350)		# YES
			isHidden = True
		else:
			text = __language__(351)		# NO
			isHidden = False
		return text, isHidden

	def setHidden(text, isHidden):
		if isHidden and text[0] != '*':						# make hidden
			return '*' + text
		elif not isHidden and text[0] == '*':				# unhide
			return text[1:]
		return text

	def makeMenu():
		debug("> ReorderChannels.makeMenu()")
		# add channel name to list from [chid, ch name, alt ch id]
		menu = [ [__language__(500), ''] ]
		for channel in channels:
			label2,isHidden = isHiddenText(channel[1])
			if isHidden:
				label = channel[1][1:]			# removes the * at beginnning
			else:
				label = channel[1]
			menu.append( [label, label2] )
		debug("< ReorderChannels.makeMenu()")
		return menu

	# load channel names
	channelsFilename = getChannelListFilename()
	channels = readChannelsList(channelsFilename, loadHidden=True)	# chid, chname, alt.chid

	# loop until finished then break
	useXOptions = [ __language__(350), __language__(351) ]			# YES , NO
	newChannels = []
	menu = makeMenu()
	allowReorder = (len(menu) > 2)

	selectDialog = DialogSelect()
	selectDialog.setup(__language__(597), width=450, rows=len(menu), useXOptions=useXOptions, \
					   reorder=allowReorder,title2=__language__(609),movingTitle=__language__(598), \
					   panel=mytvGlobals.DIALOG_PANEL)
	selectedPos,action = selectDialog.ask(menu)

	if selectedPos <= 0:
		for menuIdx in range(len(menu)):
			label,label2 = menu[menuIdx]
			if not label2:		# ignore exit
				continue

			for channel in channels:
				# compare menu's chName against channel chName, whcih may/not have * prefix
				if label == channel[1] or label == channel[1][1:]:
					isHidden = (label2 == __language__(350))
					channel[1] = setHidden(channel[1], isHidden)
					newChannels.append(channel)
					break

	del selectDialog

	writeChannelsList(channelsFilename, newChannels)
	changed = True

	debug("< configReorderChannels changed=%s" % changed)
	return changed

#######################################################################################################################    
# Edit the save programme template
#######################################################################################################################    
def configEditTemplate():
	debug("> configEditTemplate()")

	pst = ProgrammeSaveTemplate()
	value = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_TEMPLATE)
	if value == None:
		value = ''

	while True:
		value = doKeyboard(value, __language__(547))
		if pst.validTemplate(value):
			mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_SAVE_TEMPLATE, value)
			break
		else:
			messageOK(__language__(547), __language__(110))

	debug("< configEditTemplate()")

#################################################################################################################
# CONFIG EPG BUTTON COLOURS
#################################################################################################################
class ConfigEPGColours:
	def __init__(self):
		debug("> ConfigEPGColours() init()")

		self.EXT = '.png'
		self.MENU_OPT_CHNAME = "Channel Name Colour"
		self.MENU_OPT_TITLE = "Title Colour"
		self.MENU_OPT_TITLE_DESC = "Title Description Colour"
		self.MENU_OPT_ODD = "ODD Rows"
		self.MENU_OPT_EVEN = "EVEN Rows"
		self.MENU_OPT_FAV = "FAV Programme"
		self.MENU_OPT_FOCUS = "HIGHLIGHTED Programme"
		self.MENU_OPT_COLOUR_ARROWS = "Programme Arrows Colour"
		self.MENU_OPT_COLOUR_NOWTIME = "Current Time Line Colour"
		self.MENU_OPT_COLOUR_TIMERBAR = "Timerbar Colour"
		self.MENU_OPT_RESET = "Reset to Current Skin: %s" % getSkinName()

		self.menu = [
			__language__(500),		# exit
			self.MENU_OPT_CHNAME,
			self.MENU_OPT_TITLE,
			self.MENU_OPT_TITLE_DESC,
			self.MENU_OPT_ODD,
			self.MENU_OPT_EVEN,
			self.MENU_OPT_FAV,
			self.MENU_OPT_FOCUS,
			self.MENU_OPT_COLOUR_ARROWS,
			self.MENU_OPT_COLOUR_NOWTIME,
			self.MENU_OPT_COLOUR_TIMERBAR,
			self.MENU_OPT_RESET
			]
		# append extra .skin files
		fileList = listDir(DIR_EPG, '.skin')
		self.menu += fileList

		debug("< ConfigEPGColours() init()")

	def ask(self):
		debug("> ConfigEPGColours.ask()")
		reInit = False

		# show this dialog and wait until it's closed
		selectedPos = 0
		while True:
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(541), width=330, rows=len(self.menu), panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(self.menu, selectedPos)
			if selectedPos <= 0:
				break

			selectedOpt = self.menu[selectedPos]
			if selectedOpt == self.MENU_OPT_CHNAME:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_CHNAMES)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_CHNAMES, textColor)
			elif selectedOpt == self.MENU_OPT_TITLE:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TITLE)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TITLE, textColor)
			elif selectedOpt == self.MENU_OPT_TITLE_DESC:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_SHORT_DESC)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_SHORT_DESC, textColor)
			elif selectedOpt == self.MENU_OPT_ODD:			# ODD line
				backgFile = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_ODD)
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD)
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_ODD, backgFile)
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD, textColor)
			elif selectedOpt == self.MENU_OPT_EVEN:			# EVEN line
				backgFile = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_EVEN)
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_EVEN)
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_EVEN, backgFile)
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_EVEN, textColor)
			elif selectedOpt == self.MENU_OPT_FAV:			# FAV SHOWS
				backgFile = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_FAV)
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_FAV)
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_FAV, backgFile)
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_FAV, textColor)
			elif selectedOpt == self.MENU_OPT_FOCUS:		# FOCUS
				backgFile = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_FOCUS)
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD)
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_FOCUS, backgFile)
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD, textColor)
			elif selectedOpt == self.MENU_OPT_COLOUR_ARROWS:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_ARROWS)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_ARROWS, textColor)
			elif selectedOpt == self.MENU_OPT_COLOUR_NOWTIME:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_NOWTIME)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_NOWTIME, textColor)
			elif selectedOpt == self.MENU_OPT_COLOUR_TIMERBAR:
				textColor = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TIMERBAR)
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TIMERBAR, textColor)
			elif selectedOpt == self.MENU_OPT_RESET:
				mytvGlobals.config.setDisplay(MYTVConfig.KEY_DISPLAY_SKIN, "")
				mytvGlobals.config.initSectionDisplay()
				messageOK(__language__(541), __language__(215) % selectedOpt)
			else:
				# load a .skin file and overwrite keys with loaded values
				debug("change to a theme")
				section = mytvGlobals.SECTION_DISPLAY
				skinName = self.menu[selectedPos]
				items = mytvGlobals.config.action(section, mode=ConfigHelper.MODE_ITEMS)				# get curr items
				# make dict from items
				displayDict = {}
				for key, value in items:
					displayDict[key] = value

				displayDict = mytvGlobals.config.loadSkinConfig(displayDict, skinName)					# load skin file
				mytvGlobals.config.action(section, mode=ConfigHelper.MODE_REMOVE_SECTION)				# clear section
				mytvGlobals.config.action(section, displayDict, mode=ConfigHelper.MODE_INIT_SECTION)	# save new
				messageOK(__language__(541), __language__(215) % selectedOpt)

			reInit = True

		debug("< ConfigEPGColours.ask() reInit=%s" % reInit)
		return reInit


#######################################################################################################################    
# CONFIG GENRE ICONS
#######################################################################################################################    
class ConfigGenreIcons:
	def __init__(self):
		debug("ConfigGenreIcons() init()")

		self.genres = {}
		self.EXT = '.png'
		self.DISABLED_STR = '_disabled' + self.EXT
		self.ENABLED_STR = self.EXT

	# find all icon files , create a dict of {fname, fullpath + fname}
	def load(self):
		debug("> ConfigGenreIcons().load()")
		try:
			self.genres = {}
			fileList = listDir(DIR_GENRE, self.EXT, getFullFilename=True)
			for fname in fileList:
				name = fname.replace(self.DISABLED_STR, '').replace(self.ENABLED_STR,'').replace('_',' ')
				self.genres[name] = prefixDirPath(fname, DIR_GENRE)
		except:
			handleException("ConfigGenreIcons.load()")
		debug("< ConfigGenreIcons().load()")
		return self.genres

	# return a dict containing only enabled genres (those without _disabled on end of fname)
	def getEnabledGenres(self):
		debug("> ConfigGenreIcons().getEnabledGenres()")
		self.load()

		enabledGenres = {}
		for key,value in self.genres.items():
			if not value.endswith(self.DISABLED_STR):
				enabledGenres[key] = value

		debug("< ConfigGenreIcons().getEnabledGenres()")
		return enabledGenres

	def setState(self, key, state):
		changed = False
		try:
			src = self.genres[key]										# current state
			dest = src.replace(self.DISABLED_STR,self.ENABLED_STR)		# make enabled
			if not state:
				dest = dest.replace(self.ENABLED_STR,self.DISABLED_STR)	# make not enabled
			if src != dest:
				try:
					# os rename file
					self.genres[key] = dest
					os.rename(src, dest)
					changed = True
				except: pass
		except: pass
		return changed
	
	def ask(self):
		debug("> ConfigGenreIcons().ask()")
		reInit = False
		self.load()

		# make menu
		imageList = [None]
		menu = [(__language__(500), '')]	# exit
		keyList = self.genres.keys()
		keyList.sort()
		for key in keyList:
			fname = self.genres[key]
			yesno = mytvGlobals.config.configHelper.boolToYesNo(not fname.endswith(self.DISABLED_STR))
			menu.append([key, yesno])
			imageList.append(fname)

		useXOptions = [ __language__(350), __language__(351) ]			# YES , NO
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(542), rows=len(menu), width=330, imageWidth=30, \
						   title2=__language__(617),useXOptions=useXOptions, panel=mytvGlobals.DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, 0, imageList)

		# rename genre files if changed
		changed=False
		for key, value in menu:
			if value:
				if self.setState(key, mytvGlobals.config.configHelper.yesNoToBool(value)):
					changed = True 
		del selectDialog

		debug("< ConfigGenreIcons().ask() changed=%s" % changed)
		return changed

#################################################################################################################
# CONFIG GENRE BUTTON COLOURS
#################################################################################################################
class ConfigGenreColours:
	def __init__(self):
		debug("ConfigGenreColours() init()")

		self.SECTION_GENRE_COLOURS = "GENRE_COLORS"
		self.EXT = '.png'
		self.DISABLED_STR = '_disabled' + self.EXT
		self.genres = {}

	# RESET ALL OFF
	def reset(self):
		debug("> ConfigGenreColours().reset()")
		mytvGlobals.config.action(self.SECTION_GENRE_COLOURS, mode=ConfigHelper.MODE_REMOVE_SECTION)
		for genreName in self.genres.keys():
			self.genres[genreName] = None
		debug("< ConfigGenreColours().reset()")

	# load values from file
	def load(self):
		debug("> ConfigGenreColours().load()")
		try:
			# find all genres
			self.genres = {}
			fileList = listDir(DIR_GENRE, self.EXT, getFullFilename=True)
			for fname in fileList:
				genreName = os.path.basename(fname).replace(self.DISABLED_STR, '').replace(self.EXT, '').replace('_',' ')

				# get saved genre colour file, if exists in config
				colourName = mytvGlobals.config.action(self.SECTION_GENRE_COLOURS, genreName)
				if colourName:
					self.genres[genreName] = prefixDirPath(colourName, DIR_EPG)
				else:
					self.genres[genreName] = None
		except:
			handleException()
		debug("< ConfigGenreColours().load() loaded=%s" % len(self.genres))
		return self.genres

	# menu consists of icon image, genre name, filename
	def createMenu(self):
		debug("> ConfigGenreColours().createMenu()")
		menu = [ (__language__(500),""), ("All OFF", "") ]	# exit
		colourImgList = [None,None]

		genres = self.genres.items()
		genres.sort()
		for genreName, colourName in genres:
			if colourName:
				menu.append( (genreName, os.path.basename(colourName)) )
				colourImgFN = prefixDirPath(colourName, DIR_EPG)
			else:
				menu.append( (genreName, __language__(357)) )		# OFF
				colourImgFN = None
			colourImgList.append(colourImgFN)

		debug("< ConfigGenreColours().createMenu()")
		return menu, colourImgList

	def ask(self):
		debug("> ConfigGenreColours().ask()")
		reInit = mytvGlobals.INIT_NONE
		if not self.genres:
			self.load()

		# show this dialog and wait until it's closed
		selectedPos = 0
		while True:
			menu, colourImgList = self.createMenu()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(543), rows=len(menu), width=450, imageWidth=30, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu, selectedPos, colourImgList)
			if selectedPos <= 0:			# exit
				break
			elif selectedPos == 1:			# ALL OFF
				self.reset()
				reInit = mytvGlobals.INIT_DISPLAY
			else:
				genreName = menu[selectedPos][0]
				backgFile = self.genres[genreName]
				if not backgFile:					# set a default backg colour
					backgFile = "DarkBlue.png"
				backgFile, textColor = ButtonColorPicker().ask(backgFile)
				if backgFile == None:				# DISABLED
					self.genres[genreName] = None
					mytvGlobals.config.action(self.SECTION_GENRE_COLOURS, genreName, mode=ConfigHelper.MODE_REMOVE_OPTION)
					reInit = mytvGlobals.INIT_DISPLAY
				elif backgFile:						# SELECTED
					self.genres[genreName] = backgFile
					mytvGlobals.config.action(self.SECTION_GENRE_COLOURS, genreName, os.path.basename(backgFile), \
								  mode=ConfigHelper.MODE_WRITE)
					reInit = mytvGlobals.INIT_DISPLAY

		debug("< ConfigGenreColours().ask() reInit=%s" % reInit)
		return reInit


#######################################################################################################################    
# CONFIG OVESCAN & FONTS
#######################################################################################################################    
class configFonts:
	def __init__(self):
		debug("> configFonts() init()")

		self.menu = [
			[__language__(500),None],
#			[__language__(593), MYTVConfig.KEY_DISPLAY_FONT_TITLE],
#			[__language__(594), MYTVConfig.KEY_DISPLAY_FONT_SHORT_DESC],
			[__language__(595), MYTVConfig.KEY_DISPLAY_FONT_CHNAMES],
			[__language__(596), MYTVConfig.KEY_DISPLAY_FONT_EPG]
			]

		self.TITLE = 0
		self.CONFIG_KEY = 1

		# init config file
		self.selectedPos = 0
		debug("< configFonts() init()")

	def enterFont(self, currentValue):
		debug("> enterFont()")
		value = currentValue
		menu = [__language__(500)]
		for font in ALL_FONTS:
			menu.append(font)
		try:
			currentIdx = menu.index(currentValue)
		except:
			currentIdx = 0
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(572), rows=len(menu), width=360, panel=mytvGlobals.DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, currentIdx)
		if selectedPos > 0:
			value = menu[selectedPos]
		debug("< enterFont() value=%s" % value)
		return value

	def createMenuList(self):
		debug("> createMenuList()")

		list = []
		for label, key in self.menu:
			if key:
				label2 = mytvGlobals.config.getDisplay(key)
				if not label2:
					label2 = "?"
			else:
				label2 = ''
			list.append(xbmcgui.ListItem(label, label2=label2))

		debug("< createMenuList() list sz: " + str(len(list)))
		return list

	def ask(self):
		debug("> ask()")
		# show this dialog and wait until it's closed

		changed = False
		selectedPos = 0
		while True:
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(544), rows=len(menuList), width=300, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
			 	break # exit selected

			else:												# FONTS
				selectedValue = menuList[selectedPos].getLabel2()
				key = self.menu[selectedPos][self.CONFIG_KEY]

				value = self.enterFont(selectedValue)
				if (value != selectedValue) and mytvGlobals.config.setDisplay(key, value):
					changed = True

		debug("< ask() changed=%s " % changed)
		return changed

#######################################################################################################################    
# CONFIG EPG ROW / GAP HEIGHTS
#######################################################################################################################    
def configEPGRows():
	debug("configEPGRows()")
	selectedPos = 0
	while True:
		menuList = [ xbmcgui.ListItem(__language__(500)),
					 xbmcgui.ListItem(__language__(573), mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_EPG_ROW_HEIGHT)),
					 xbmcgui.ListItem(__language__(574), mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT))
					 ]
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(545), rows=len(menuList), width=270, panel=mytvGlobals.DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menuList, selectedPos)
		if selectedPos <= 0:
			break # exit selected

		
		if selectedPos == 1:
			key = MYTVConfig.KEY_DISPLAY_EPG_ROW_HEIGHT
		elif selectedPos == 2:
			key = MYTVConfig.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT

		title = menuList[selectedPos].getLabel()
		value = menuList[selectedPos].getLabel2()
		value = int(doKeyboard(value, title, KBTYPE_NUMERIC))
		mytvGlobals.config.setDisplay(key, value)
	
#######################################################################################################################    
# Config Wake On LAN MAC
#######################################################################################################################    
def configWOL():
    debug("> configWOL()")

    macOK = False
    mac = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_WOL)
    while True:
        mac = doKeyboard(mac, __language__(555) + " eg. 0:e:7f:ac:d6:4d")
        # check valid MAC
        if mac and not validMAC(mac):
            messageOK(__language__(555), __language__(134))
        else:
            mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_WOL, mac)
            sendWOL(True)
            break

    debug("< configWOL()")



#################################################################################################################
class ButtonColorPicker(xbmcgui.WindowDialog):
	def __init__(self):
		debug("> ButtonColorPicker().init")

		setResolution(self)

		width = 620
		height = 430
		originX = int((REZ_W /2) - (width /2))
		originY = int((REZ_H /2) - (height /2)) +10
		try:
			self.addControl(xbmcgui.ControlImage(originX, originY, width, height, mytvGlobals.DIALOG_PANEL))
		except: pass

		# TITLE
		xpos = originX + 70
		ypos = originY + 30
		self.titleCL = xbmcgui.ControlLabel(xpos, ypos, width, 40, '', FONT13, "0xFFFFFF66")
		self.addControl(self.titleCL)

		# PICKER BUTTON
		self.pickerW = 350
		self.pickerH = 60
		self.pickerX = originX + 225
		self.pickerY = originY + 150
		self.pickerCB = None
		self.pickerFileIDX = 0

		# CHANGER buttons
		changerBtnW = 145
		changerBtnH = 35

		# background changer NEXT
		xpos = originX + 70
		ypos = originY + 90
		self.backgNextCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(602))
		self.addControl(self.backgNextCB)
		self.backgNextCB.setVisible(False)
		self.backgNextCB.setEnabled(False)

		# background changer PREV
		ypos += changerBtnH + 10
		self.backgPrevCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(603))
		self.addControl(self.backgPrevCB)
		self.backgPrevCB.setVisible(False)
		self.backgPrevCB.setEnabled(False)

		# TEXT changer NEXT
		ypos += changerBtnH + 20
		self.textNextCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(604))
		self.addControl(self.textNextCB)
		self.textNextCB.setVisible(False)
		self.textNextCB.setEnabled(False)

		# TEXT changer PREV
		ypos += changerBtnH + 10
		self.textPrevCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(605))
		self.addControl(self.textPrevCB)
		self.textPrevCB.setVisible(False)
		self.textPrevCB.setEnabled(False)

		# accept button
		ypos += changerBtnH + 30
		self.acceptCB = xbmcgui.ControlButton(xpos, ypos, 70, 25, __language__(360))	# OK
		self.addControl(self.acceptCB)

		# cancel button
		xpos += 90
		self.cancelCB = xbmcgui.ControlButton(xpos, ypos, 70, 25, __language__(355))	# cancel
		self.addControl(self.cancelCB)

		# DISABLE button
		xpos += 90
		self.disableCB = xbmcgui.ControlButton(xpos, ypos, 80, 25, __language__(606))	# turn off
		self.addControl(self.disableCB)
		self.disableCB.setEnabled(False)
		self.disableCB.setVisible(False)

		self.textColor = ""
		self.backgFile = ""
		debug("< ButtonColorPicker().init")

	def setNav(self):
		debug("ButtonColorPicker().setNav()")
		self.backgNextCB.controlUp(self.acceptCB)
		self.backgNextCB.controlDown(self.backgPrevCB)

		self.backgPrevCB.controlUp(self.backgNextCB)
		self.backgPrevCB.controlDown(self.textNextCB)

		self.textNextCB.controlUp(self.backgPrevCB)
		self.textNextCB.controlDown(self.textPrevCB)

		self.textPrevCB.controlUp(self.textNextCB)
		self.textPrevCB.controlDown(self.acceptCB)

		self.acceptCB.setNavigation(self.textPrevCB,self.backgNextCB,self.disableCB,self.cancelCB)
		self.cancelCB.setNavigation(self.textPrevCB,self.backgNextCB,self.acceptCB,self.disableCB)
		self.disableCB.setNavigation(self.textPrevCB,self.backgNextCB,self.cancelCB,self.acceptCB)

	def drawPicker(self):
		debug("> drawPicker()")
		try:
			self.removeControl(self.pickerCB)
		except: pass

		text = ""
		if self.backgFile:
			text += " File: " + os.path.basename(self.backgFile)
		if self.textColor:
			text += " Text: " + self.textColor

		texture = prefixDirPath(self.backgFile, DIR_EPG)
		debug("texture=%s  textColor=%s" % (texture, self.textColor))
		self.pickerCB = xbmcgui.ControlButton(self.pickerX, self.pickerY, self.pickerW, self.pickerH, \
								text, texture, texture, font=FONT13, textColor=self.textColor, \
								alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
		self.addControl(self.pickerCB)
		debug("< drawPicker()")

	# show this dialog and wait until it's closed
	def ask(self, backgFile="", textColor="", title=""):
		debug("> ask()")
		debug("backgFile=%s  textColor=%s" % (backgFile, textColor))

		self.backgFile = backgFile
		self.textColor = textColor
		if title:
			selectText = title
		elif backgFile and textColor:
			selectText = __language__(599)	# back + text
		elif backgFile:
			selectText = __language__(600)	# backg
		elif textColor:
			selectText = __language__(601)	# text
		else:
			selectText = ""
		self.titleCL.setLabel(selectText)

		if textColor:
			self.textNextCB.setVisible(True)
			self.textNextCB.setEnabled(True)
			self.textPrevCB.setVisible(True)
			self.textPrevCB.setEnabled(True)

		if backgFile:
			# show disable button
			self.disableCB.setVisible(True)
			self.disableCB.setEnabled(True)
			self.fileList = listDir(DIR_EPG, '.png', getFullFilename=True)
			if not self.fileList:
				messageOK("Alert","No background colour files found in folder:", DIR_EPG)
				self.backgFile = ""
				self.textColor = ""
			else:
				self.backgNextCB.setVisible(True)
				self.backgNextCB.setEnabled(True)
				self.backgPrevCB.setVisible(True)
				self.backgPrevCB.setEnabled(True)

		if self.backgFile or self.textColor:
			self.drawPicker()
			self.setNav()

		if self.backgFile:
			self.setFocus(self.backgNextCB)
		elif self.textColor:
			self.setFocus(self.textNextCB)
		else:
			self.setFocus(self.cancelCB)

		self.doModal()
		debug("< ask() backgFile=%s textColor=%s" % (self.backgFile, self.textColor))
		return self.backgFile, self.textColor

	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonID = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonID in CANCEL_DIALOG + EXIT_SCRIPT:
			self.backgFile = ""
			self.textColor = ""
			self.close()

	def onControl(self, control):
		if control == self.cancelCB:
			# unset values
			self.backgFile = ""
			self.textColor = ""
			self.close()
		elif control == self.acceptCB:
			self.close()
		elif control == self.backgNextCB:
			self.pickerFileIDX += 1
			if self.pickerFileIDX >= len(self.fileList):
				self.pickerFileIDX = 0
			self.backgFile = self.fileList[self.pickerFileIDX]
			self.drawPicker()
			self.setFocus(control)
		elif control == self.backgPrevCB:
			self.pickerFileIDX -= 1
			if self.pickerFileIDX < 0 :
				self.pickerFileIDX = len(self.fileList)-1
			self.backgFile = self.fileList[self.pickerFileIDX]
			self.drawPicker()
			self.setFocus(control)
		elif control == self.textNextCB:
			# move fwd in 0x33 increments
			hex_num = int(self.textColor.replace('0xFF',''),16)
			if self.textColor[-4:] == "FFFF":
				hex_num +=  0x320001
			elif self.textColor[-2:] == "FF":
				hex_num += 0x003201
			else:
				hex_num += 0x33
			if hex_num >= 0xFFFFFF:
				self.textColor = "0xFF000066"		# dark blue
			else:
				self.textColor = "0xFF" + upper(hex(hex_num).replace('0x','').rjust(6, '0'))

			self.drawPicker()
			self.setFocus(control)
		elif control == self.textPrevCB:
			# move back in 0x33 increments
			hex_num = int(self.textColor.replace('0xFF',''),16)
			if self.textColor[-4:] == "0000":
				hex_num -=  0x320001
			elif self.textColor[-2:] == "00":
				hex_num -= 0x003201
			else:
				hex_num -= 0x33
			if hex_num < 0:
				self.textColor = "0xFFFFFFFF"
			else:
				self.textColor = "0xFF" + upper(hex(hex_num).replace('0x','').rjust(6, '0'))
			self.drawPicker()
			self.setFocus(control)
		elif control == self.disableCB:
			self.backgFile = None
			self.textColor = None
			self.close()

