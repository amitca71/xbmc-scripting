import time, sys, xbmc, xbmcgui, traceback
from XinBox_Settings import Settings
import XinBox_Util
import XinBox_MMPopup
from XinBox_EmailEngine import Email
from XinBox_Language import Language
import threading
import XinBox_MainMenu
from XinBox_Language import Language
import os
from os.path import join, exists

TITLE = XinBox_Util.__scriptname__

class Minimode:
    def init(self):
        self.account = sys.argv[1:][0]
        self.srcpath = sys.argv[1:][1]
        f = open("X:\\mmcomu.xib", "w")
        f.close()
        time.sleep(2)
        self.emailist = []
        lang = Language(TITLE)
        lang.load(self.srcpath + "\\language")
        self.language = lang.string
        xbmc.executebuiltin('XBMC.Notification(XinBox Mini-Mode,Started)')
        time.sleep(5)
        try:
            self.exit = False
            self.loadsettings()
            self.inboxes = self.buildinboxdict()
            if not len(self.inboxes) == 0:self.startmm()
        except:pass
        if exists("X:\\mmcomu.xib"):
            os.remove("X:\\mmcomu.xib")
        if self.exit:
            w = XinBox_MainMenu.GUI("XinBox_MainMenu.xml",self.srcpath,"DefaultSkin",bforeFallback=False,minimode=self.account, minibox=self.inbox, lang=self.language)
            w.doModal()
            del w
        else:
            xbmc.executebuiltin('XBMC.Notification(XinBox Mini-Mode,Closed)')
        

    def startmm(self):
        while exists("X:\\mmcomu.xib"):
            for inbox in self.inboxes:
                if exists("X:\\mmcomu.xib"):
                    inboxsettings = self.accountsettings.getSettingInListbyname("Inboxes",inbox)
                    self.checkfornew(inboxsettings,inbox)
                    if self.exit:return
                else:return
            for i in xrange(0,int(self.accountsettings.getSetting("MiniMode Time"))):
                if exists("X:\\mmcomu.xib"):
                    time.sleep(1)
                else:break
        return
        
    def buildinboxdict(self):
        inboxes = []
        for set in self.accountsettings.getSetting("Inboxes")[1]:
            if set[1].getSetting("Mini Mode Enabled") == "True":
                inboxes.append(set[0])
        return inboxes

    def loadsettings(self):
        self.settings = Settings("XinBox_Settings.xml",TITLE,"")
        self.accountsettings = self.settings.getSettingInListbyname("Accounts",self.account)

    def checkfornew(self, ibsettings, inbox):
        if exists("X:\\mmcomu.xib"):
            w = Email(ibsettings,inbox,self.account,False, True)
            w.checkemail()
            newlist = w.newlist
            ibfolder = w.ibfolder
            del w
            if len(newlist) != 0:
                self.popup(newlist, inbox, ibsettings,ibfolder)

    def popup(self, newlist, inbox, ibsettings,ibfolder):
        if exists("X:\\mmcomu.xib"):
            if self.accountsettings.getSetting("Mini Mode SFX",None) == None or self.accountsettings.getSetting("Mini Mode SFX",None) == "True":
                xbmc.playSFX(str(ibsettings.getSetting("Email Notification")))
            mymessage = self.language(210) + inbox + "\n" + self.language(219) % str(len(newlist))
            w = Popup("XinBox_Popup.xml",self.srcpath,"DefaultSkin",0,message=mymessage, lang=self.language)
            w.doModal()
            self.returnval = w.returnval
            del w
            if self.returnval == 1:
                for item in newlist:
                    self.emailist.insert(0,ibfolder + item[0] + ".sss")
                w = XinBox_MMPopup.GUI("XinBox_MMPopup.xml",self.srcpath,"DefaultSkin",0,emailist=self.emailist,lang=self.language,ibox=inbox)
                w.doModal()
                self.returnval = w.returnval
                del w
                self.emailist = []
                if self.returnval == 1:
                    self.inbox = inbox
                    self.exit = True
            
class Popup( xbmcgui.WindowXMLDialog ):
    def __init__(self,strXMLname, strFallbackPath,strDefaultName,bforeFallback=0,message=False,lang=False):
        self.lang = lang
        self.message = message
        self.control_action = XinBox_Util.setControllerAction()

    def onInit(self):
        self.returnval = 0
        self.getControl(21).setText(self.message)
        self.animating = True
        xbmc.executebuiltin("Skin.SetBool(showpopup)")
        time.sleep(0.5)
        self.animating = False
        self.showing = True
        subThread = threading.Thread(target=self.SubthreadProc, args=())
        subThread.start()

    def SubthreadProc(self):
        time.sleep(8)
        if self.showing:
            self.animating = True
            xbmc.executebuiltin("Skin.ToggleSetting(showpopup)")
            time.sleep(0.5)
            self.animating = False
            self.close()

    def onClick(self, controlID):
        passs

    def onAction( self, action ):
        if not self.animating:
            button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
            actionID   =  action.getId()
            try:focusid = self.getFocusId()
            except:focusid = 0
            try:control = self.getFocus()
            except: control = 0
            if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu'):
                self.exitme()
            elif ( button_key == 'Keyboard TAB Button' or button_key == 'White Button' or button_key == 'Remote Display'):
                self.returnval = 1
                self.close()

    def exitme(self):
        self.animating = True
        xbmc.executebuiltin("Skin.ToggleSetting(showpopup)")
        time.sleep(0.5)
        self.animating = False
        self.returnval = 0
        self.showing = False
        self.close()        

    def onFocus(self, controlID):
        pass    

Minimode().init()
