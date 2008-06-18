"""
 Common GUI funcs and globals
""" 

import sys,os.path
import xbmc, xbmcgui

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "bbbGUILib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '09-06-2008'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

from bbbLib import *
try:
    DIR_GFX = sys.modules[ "__main__" ].DIR_GFX                 # should be in default.py
except:
    DIR_RESOURCES = sys.modules[ "__main__" ].DIR_RESOURCES     # should be in default.py
    DIR_GFX = os.path.join(DIR_RESOURCES,'gfx')


# GFX - for library funcs
BACKGROUND_FILENAME = os.path.join(DIR_GFX,'background.png')
PANEL_HEADER_NAME = 'header.png'
HEADER_FILENAME = os.path.join(DIR_GFX, PANEL_HEADER_NAME)
PANEL_FOOTER_NAME = 'footer.png'
FOOTER_FILENAME = os.path.join(DIR_GFX, PANEL_FOOTER_NAME)
LOGO_FILENAME = os.path.join(DIR_GFX,'logo.png')
BTN_A_FILENAME = os.path.join(DIR_GFX,'abutton.png')
BTN_B_FILENAME = os.path.join(DIR_GFX,'bbutton.png')
BTN_X_FILENAME = os.path.join(DIR_GFX,'xbutton.png')
BTN_Y_FILENAME = os.path.join(DIR_GFX,'ybutton.png')
BTN_WHITE_FILENAME = os.path.join(DIR_GFX,'whitebutton.png')
BTN_BACK_FILENAME = os.path.join(DIR_GFX,'backbutton.png')
LIST_HIGHLIGHT_FILENAME = os.path.join(DIR_GFX,'list_highlight.png')
FRAME_FOCUS_FILENAME = os.path.join(DIR_GFX,'frame_focus.png')
FRAME_NOFOCUS_FILENAME = os.path.join(DIR_GFX,'frame_nofocus.png')
FRAME_NOFOCUS_LRG_FILENAME = os.path.join(DIR_GFX,'frame_nofocus_large.png')
DIALOG_PANEL_NAME = 'dialog-panel.png'
PANEL_FILENAME = os.path.join(DIR_GFX, DIALOG_PANEL_NAME)
DIALOG_PANEL_NAME_MC360 = 'dialog-panel_mc360.png'
PANEL_FILENAME_MC360 = os.path.join(DIR_GFX, DIALOG_PANEL_NAME_MC360)
MENU_FILENAME = os.path.join(DIR_GFX,'menu.png')

# rez GUI defined in
REZ_W = 720
REZ_H = 576

try: Emulating = xbmcgui.Emulating
except: Emulating = False


#################################################################################################################
# Dialog with options
#################################################################################################################
class DialogSelect(xbmcgui.WindowDialog):
	def __init__(self):
		if Emulating: xbmcgui.WindowDialog.__init__(self)

		setResolution(self)

		self.selectedPos = 0
		self.panelCI = None
		self.menuCL = None
		self.lastAction = 0
		self.useY = False
		self.useX = False
		self.isMove = False

	def setup(self, title='',width=430, height=490, xpos=-1, ypos=-1, textColor='0xFFFFFFFF', \
			  imageWidth=0,imageHeight=22, itemHeight=25, rows=0, \
			  useY=False, useX=False, isMove=False, panel='', banner='', font='font13', title2=''):
		debug("> DialogSelect().setup() useY=%s useX=%s isMove=%s" % (useY,useX,isMove))

		if not panel:
			panel = DIALOG_PANEL
		debug("panel=%s" % panel)
		self.useY = useY
		self.useX = useX
		self.isMove = isMove
		offsetLabelX = 15
		offsetListX = 20

		if width < 150:
			width = 150

		listW = width - offsetListX - 10
		if imageHeight > itemHeight:
			itemHeight = imageHeight

		if banner:
			bannerH = 40
		else:
			bannerH = 0

		if title:
			titleH = 25
		else:
			titleH = 0

		# calc height based on rows, otherwise use supplied height
		if rows > 0:
			rows += 3		 # add 'exit' + extra rows
			listH = (rows * itemHeight)
		else:
			listH = height

		if height > listH:
			height = listH						# shrink height to fit list
		elif height < listH:
			listH = height-itemHeight			# shrink list to height, minus 1 line

		height += titleH + bannerH				# add space onto for title + gap

		# center on screen
		if xpos < 0:
			xpos = int((REZ_W /2) - (width /2))
		if ypos < 0:
			ypos = int((REZ_H /2) - (height /2)) + 10

		bannerY = ypos + 10
		titleY = bannerY + bannerH 
		listY = titleY + titleH
		defaultAnims = [('WindowOpen', 'effect=fade start=0 end=100 time=200'),
						('WindowClose', 'effect=slide time=200 end=0,576 acceleration=1.1')]

		try:
			self.removeControl(self.panelCI)
		except: pass
		try:
			self.panelCI = xbmcgui.ControlImage(xpos, ypos, width, height, panel)
			self.addControl(self.panelCI)
			self.panelCI.setAnimations(defaultAnims)
		except: pass

		
		if title2:
			x = xpos+offsetLabelX + listW
			title2CL = xbmcgui.ControlLabel(x, titleY, listW, titleH, \
										title2, FONT13, '0xFFFFFF00', alignment=XBFONT_RIGHT)
			self.addControl(title2CL)
			title2CL.setAnimations(defaultAnims)
			titleAlignment = XBFONT_LEFT
		else:
			titleAlignment = XBFONT_CENTER_X

		if title:
			titleCL = xbmcgui.ControlLabel(xpos+offsetLabelX, titleY, listW, titleH, \
										title, FONT13, '0xFFFFFF00', alignment=titleAlignment)
			self.addControl(titleCL)
			titleCL.setAnimations(defaultAnims)


		if bannerH:
			try:
				self.removeControl(self.bannerCI)
			except: pass
			try:
				self.bannerCI = xbmcgui.ControlImage(xpos+offsetListX, bannerY,
													listW, bannerH, banner, aspectRatio=2)
				self.addControl(self.bannerCI)
				self.bannerCI.setAnimations(defaultAnims)
			except:
				debug("failed to place banner")

		if imageWidth > 0:
			rowSpace = 1
		else:
			rowSpace = 0

		try:
			self.removeControl(self.menuCL)
		except: pass
		if not self.isMove:
			self.menuCL = xbmcgui.ControlList(xpos+offsetListX, listY, \
											listW, listH, font, textColor=textColor, \
											imageWidth=imageWidth, imageHeight=imageHeight, \
											itemHeight=itemHeight, \
#											buttonTexture=LIST_NOFOCUS_FILENAME, \
											itemTextXOffset=0, space=rowSpace, alignmentY=XBFONT_CENTER_Y)
		else:
			self.menuCL = xbmcgui.ControlList(xpos+offsetListX, listY, \
											listW, listH, font, textColor=textColor, \
											imageWidth=imageWidth, imageHeight=imageHeight, \
											itemHeight=itemHeight, buttonFocusTexture=LIST_HIGHLIGHT_FILENAME, \
#											buttonTexture=LIST_NOFOCUS_FILENAME, \
											itemTextXOffset=0, space=rowSpace, alignmentY=XBFONT_CENTER_Y)
		self.addControl(self.menuCL)
		self.menuCL.setPageControlVisible(False)
		self.menuCL.setAnimations(defaultAnims)

		debug("< DialogSelect().setup()")

	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonCode = action.getButtonCode()
			if not actionID:
				actionID = buttonCode
		except: return
		debug( "dialogSelect.onAction(): actionID=%i" % actionID )

		self.lastAction = actionID
		if actionID in EXIT_SCRIPT + CANCEL_DIALOG:
			self.selectedPos = -1
			self.close()
		elif ((actionID in CLICK_Y or buttonCode in CLICK_Y) and self.useY) or \
			 ((actionID in CLICK_X or buttonCode in CLICK_X) and self.useX):
			self.selectedPos = self.menuCL.getSelectedPosition()
			self.close()
		elif self.isMove:
			if actionID in MOVEMENT_UP:
				item = self.menu.pop(self.selectedPos)
				self.selectedPos -= 1
				if self.selectedPos < 1 :	# skip over EXIT at pos 0
					# move to end
					self.selectedPos = len(self.menu)
					self.menu.append(item)
				else:
					self.menu.insert(self.selectedPos, item)
				self.setMenu()
			elif actionID in MOVEMENT_DOWN:
				item = self.menu.pop(self.selectedPos)
				self.selectedPos += 1
				if self.selectedPos > len(self.menu):	# allow for popped item
					self.selectedPos = 1
				self.menu.insert(self.selectedPos, item)
				self.setMenu()

	def onControl(self, control):
		if not control:
			return
		self.selectedPos = self.menuCL.getSelectedPosition()
		print "onControl self.selectedPos=%s" % self.selectedPos
		debug("DialogSelect onControl() QUIT")
		self.close()

	def setMenu(self):
		debug("> DialogSelect.setMenu()")
		self.menuCL.reset()
		if self.menu:
			menuSZ = len(self.menu)
			for idx in range(menuSZ):
				opt = self.menu[idx]
				try:
					img = self.icons[idx]
				except:
					img = ''

				if isinstance(opt, xbmcgui.ListItem):
					# associate an img with listitems that have them
					if img:
						opt.setIconImage(img)
						opt.setThumbnailImage(img)
					self.menuCL.addItem(opt)
				elif isinstance(opt, list) or isinstance(opt, tuple):
					# option is itself a list/tuple
					l1 = opt[0].strip()
					try:
						l2 = opt[1].strip()
					except:
						l2 = ''
					self.menuCL.addItem(xbmcgui.ListItem(l1, l2, img, img))
				else:
					# single string value
					if opt == None:
						opt = ''
					self.menuCL.addItem(xbmcgui.ListItem(opt.strip(), '', img, img))

			if self.selectedPos >= menuSZ:
				self.selectedPos = menuSZ-1
			elif self.selectedPos < 0:
				self.selectedPos = 0
			self.menuCL.selectItem(self.selectedPos)
		debug("< DialogSelect.setMenu()")

	# show this dialog and wait until it's closed
	def ask(self, menu, selectIdx=0, icons=[]):
		debug ("> DialogSelect().ask() selectIdx=" +str(selectIdx))

		self.icons = icons
		self.menu = menu
		self.selectedPos = selectIdx
		self.setMenu()
		self.setFocus(self.menuCL)
		self.doModal()

		debug ("< DialogSelect.ask() selectedPos=%s lastAction=%s" % (self.selectedPos,self.lastAction))
		return self.selectedPos, self.lastAction

#################################################################################################################
class TextBoxDialog(xbmcgui.WindowDialog):
	def __init__(self):
		debug("TextBoxDialog().__init__")
		if Emulating: xbmcgui.WindowDialog.__init__(self)
		setResolution(self)

	def _setupDisplay(self, width, height):
		debug( "TextBoxDialog()._setupDisplay()" )

		xpos = int((REZ_W /2) - (width /2))
		ypos = int((REZ_H /2) - (height /2))

		try:
			self.addControl(xbmcgui.ControlImage(xpos, ypos, width, height, self.panel))
		except: pass

		xpos += 25
		ypos += 10
		self.titleCL = xbmcgui.ControlLabel(xpos, ypos, width-35, 30, '', \
											FONT14, "0xFFFFFF99", alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
		self.addControl(self.titleCL)
		ypos += 25
		self.descCTB = xbmcgui.ControlTextBox(xpos, ypos, width-44, height-85, FONT10, '0xFFFFFFEE')
		self.addControl(self.descCTB)

	def ask(self, title, text="", file=None, width=685, height=560, panel=""):
		debug( "> TextBoxDialog().ask()" )
		if not panel:
			self.panel = DIALOG_PANEL
		else:
			self.panel = panel
		self._setupDisplay(width, height)
		if not title and file:
			head, title = os.path.split(file)
		self.titleCL.setLabel(title)
		if file:
			text = readFile(file)
		self.descCTB.setText(text)
		self.setFocus(self.descCTB)
		self.doModal()
		debug( "< TextBoxDialog().ask()" )

	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return
		debug( "TextBoxDialog onAction(): actionID=%i" % actionID )
		if actionID in EXIT_SCRIPT + CANCEL_DIALOG:
			self.close()

	def onControl(self, control):
		pass

######################################################################################
def setDialogPanel(filename):
    debug("bbbGUI().setDialogPanel() " + filename)
    global DIALOG_PANEL
    DIALOG_PANEL = filename

######################################################################################
# establish default panel to use for dialogs
global DIALOG_PANEL
try:
    DIALOG_PANEL = sys.modules[ "__main__" ].DIALOG_PANEL
except:
    if isMC360():
        DIALOG_PANEL = os.path.join(DIR_GFX, PANEL_FILENAME_MC360)
    else:
        DIALOG_PANEL = os.path.join(DIR_GFX, PANEL_FILENAME)
debug("bbbGUILib() DIALOG_PANEL=%s" % DIALOG_PANEL)