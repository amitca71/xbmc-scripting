"""

 bbbSkinGUILib - Skinned (windowXML/dialogXML) objects.

"""
import xbmc, xbmcgui, sys

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "bbbSkinGUILib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '26-02-2009'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)


#################################################################################################################
class TextBoxDialogXML( xbmcgui.WindowXML ):
	""" Create a skinned textbox window """

	XML_FILENAME = "DialogScriptInfo.xml"
	
	def __init__( self, *args, **kwargs):
		self.EXIT_CODES = (9, 10, 216, 257, 275, 216, 61506, 61467,)
		
	def onInit( self ):
		xbmc.output( "TextBoxDialogXML.onInit()" )
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
		if actionID in self.EXIT_CODES or buttonCode in self.EXIT_CODES:
			self.close()

	def ask(self, title="", text="", fn=None ):
		xbmc.output("TextBoxDialogXML.ask()")
		if not title and fn:
			self.title = fn
		else:
			self.title = title
		if fn:
			try:
				self.text = file(fn).read()
			except:
				self.text = "Failed to load file: %s" % fn
		else:
			self.text = text

		self.doModal()		# causes window to be drawn

