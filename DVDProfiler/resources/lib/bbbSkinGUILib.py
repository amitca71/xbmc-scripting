"""

 bbbSkinGUILib - Skinned (windowXML/dialogXML) objects.

"""
import xbmc, xbmcgui, sys

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "bbbSkinGUILib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '21-10-2008'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

PAD_A                   = 256
PAD_B                   = 257
PAD_X                   = 258
PAD_Y                   = 259
ACTION_A	            = 7
ACTION_X 	            = 18    # X
ACTION_Y 	            = 34	# Y
ACTION_B	            = 9     # B
ACTION_REMOTE_STOP		= 13	# remote
KEYBOARD_X              = 61528
KEYBOARD_A              = 61505
KEYBOARD_B              = 61506
KEYBOARD_Y              = 61529
KEYBOARD_RETURN         = 61453
KEYBOARD_ESC            = 61467
CLICK_A = ( ACTION_A, PAD_A, KEYBOARD_A, KEYBOARD_RETURN, )
CLICK_B = ( ACTION_B, PAD_B, KEYBOARD_B, )
CLICK_X = ( ACTION_X, PAD_X, KEYBOARD_X, ACTION_REMOTE_STOP, )
CLICK_Y = ( ACTION_Y, PAD_Y, KEYBOARD_Y, )
EXIT_CODES = (9, 10, 216, 257, 275, 216, 61506, 61467,)

def log(text):
    try:
        xbmc.output(text)
    except: pass

#################################################################################################################
class TextBoxDialogXML( xbmcgui.WindowXML ):
	""" Create a skinned textbox window """

	XML_FILENAME = "DialogScriptInfo.xml"
	
	def __init__( self, *args, **kwargs):
		pass
		
	def onInit( self ):
		log( "TextBoxDialogXML.onInit()" )
		try:
			self.getControl( 3 ).setLabel( self.title )
		except: pass
		self.getControl( 5 ).setText( self.text )

	def onClick( self, controlId ):
		pass

	def onFocus( self, controlId ):
		pass

	def onAction( self, action ):
		if not action:
			return
		buttonCode =  action.getButtonCode()
		actionID   =  action.getId()
		if actionID in EXIT_CODES or buttonCode in EXIT_CODES:
			self.close()

	def ask(self, title="", text="", fn=None ):
		log("TextBoxDialogXML.ask()")
		self.title = title
		if fn:
			try:
				self.text = file(fn).read()
			except:
				self.text = "Failed to load file: %s" % fn
		else:
			self.text = text

		self.doModal()		# causes window to be drawn

###########################################################################################################
class DialogSelectXML(xbmcgui.WindowXMLDialog):
	# control id's
	CLBL_TITLE = 1
	CLST_SELECT = 3
	CLBL_COL1_TITLE = 6
	CLBL_COL2_TITLE = 7

	def __init__( self, *args, **kwargs ):
		log("DialogSelectXML().__init__")
		self.isStartup = True
		self.lastAction = 0

	#################################################################################################################
	def onInit( self ):
		log("> DialogSelectXML.onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			self.getControl(self.CLBL_TITLE).setLabel(self.title)
			try:
				self.getControl(self.CLBL_COL1_TITLE).setLabel(self.colTitle1)
			except: pass
			try:
				self.getControl(self.CLBL_COL2_TITLE).setLabel(self.colTitle2)
			except: pass

			if self.options:
				xbmcgui.lock()
				ctrl = self.getControl(self.CLST_SELECT)
				if isinstance(self.options[0], str):
					for lbl1 in self.options:
						ctrl.addItem(lbl1)
				elif isinstance(self.options[0], xbmcgui.ListItem):
					for li in self.options:
						ctrl.addItem(li)
				else:
					# list of [str, str]
					for lbl1, lbl2 in self.options:
						ctrl.addItem(xbmcgui.ListItem(lbl1, lbl2))
				xbmcgui.unlock()

				sz = len(self.options)
				if self.selectedPos >= sz:
					self.selectedPos = sz-1
				if self.selectedPos < 0:
					self.selectedPos = 0
				if self.selectedPos >= 0:
					ctrl.selectItem(self.selectedPos)
			self.isStartup = False

		log("< DialogSelectXML.onInit()")


	#################################################################################################################
	def onAction(self, action):
		try:
			buttonCode =  action.getButtonCode()
			actionID   =  action.getId()
			if not actionID:
				actionID = buttonCode
		except: return

		log("onAction() %s %s" % (actionID, buttonCode))
		self.lastAction = actionID
		if actionID in EXIT_CODES or buttonCode in EXIT_CODES:
			log("exit")
			self.selectedPos = -1
			self.close()
		self.selectedPos = self.getControl(self.CLST_SELECT).getSelectedPosition()
		if actionID in CLICK_A or buttonCode in CLICK_A:
			log("CLICK_A")
			self.close()
		elif (self.useX and (actionID in CLICK_X or buttonCode in CLICK_X)):
			log("CLICK_X")
			self.close()
		elif (self.useY and (actionID in CLICK_Y or buttonCode in CLICK_Y)):
			log("CLICK_Y")
			self.close()

	#################################################################################################################
	def onClick(self, controlID):
		if not controlID:
			return
		self.selectedPos = self.getControl(self.CLST_SELECT).getSelectedPosition()
		log("DialogSelectXML.onClick() selectedPos=%s" % self.selectedPos)
		self.close()

	###################################################################################################################
	def onFocus(self, controlID):
		pass

	###################################################################################################################
	def ask(self, title, options, selectedPos=0, colTitle1="", colTitle2="", useX=False, useY=False):
		log("> DialogSelectXML.ask()")
		self.title = title
		self.options = options
		self.colTitle1 = colTitle1
		self.colTitle2 = colTitle2
		self.selectedPos = selectedPos
		self.useX = useX
		self.useY = useY
		self.doModal()
		log("< DialogSelectXML.ask() selectedPos=%s lastAction=%s" % (self.selectedPos,self.lastAction))
		return self.selectedPos, self.lastAction

