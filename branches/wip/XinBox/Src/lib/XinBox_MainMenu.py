

import xbmc, xbmcgui, time, sys, os

import XinBox_InfoDialog
import XinBox_Util
import XinBox_LoginMenu
from XinBox_Settings import Settings
from XinBox_AccountSettings import Account_Settings
import XinBox_MyAccountMenu
import XinBox_About

TITLE = XinBox_Util.__scriptname__
VERSION =  XinBox_Util.__version__
URL = XinBox_Util.__url__

defSettings = {"Default Account": ["-","text"],"Mini Mode Account": ["-","text"],"Accounts": [['Account',[]],"list"]}

class GUI( xbmcgui.WindowXML ):
    def __init__(self,strXMLname, strFallbackPath,strDefaultName,bforeFallback=0,minimode=False, minibox = False, lang=False):
        self.srcpath = strFallbackPath
        self.lang = lang
        self.minibox = minibox
        self.minimode = minimode
        self.init = 0

    def loadsettings(self):
        self.settings = Settings("XinBox_Settings.xml",TITLE,defSettings)     

    def buildaccounts(self):
        accounts = []
        for set in self.settings.getSetting("Accounts")[1]:
            accounts.append(set[0])
        if len(accounts) == 0:
            self.noaccounts = True
        else:self.noaccounts = False
        return accounts

    def onInit(self):
        self.loadsettings()
        self.accounts = self.buildaccounts()
        self.setupvars()
        if self.init == 0:
            self.init = 1
            self.checkdefault()
        xbmcgui.lock()
        self.setupcontrols()
        xbmcgui.unlock()

    def checkdefault(self):
        if self.settings.getSetting("Default Account") != "-" or self.minimode != False:
            if self.minimode != False:
                account = self.minimode
            else:account = self.settings.getSetting("Default Account")
            self.accountsettings = self.getaccountsettings(account)
            accountpass = self.accountsettings.getSetting("Account Password")
            if accountpass != "-":
                value = self.showKeyboard(self.lang(31),"",1)
                if value != "":
                    if value == accountpass.decode("hex"):
                        self.defaultlogin(account)
                    else:self.launchinfo("","",self.lang(93),self.lang(32))
            else:self.defaultlogin(account)

    def defaultlogin(self, account):
        if self.minibox != False:w = XinBox_MyAccountMenu.GUI("XinBox_AccountMenu.xml",self.srcpath,"DefaultSkin",lang=self.lang,theaccount=account,title=TITLE,minibox=self.minibox)
        else:w = XinBox_MyAccountMenu.GUI("XinBox_AccountMenu.xml",self.srcpath,"DefaultSkin",lang=self.lang,theaccount=account,title=TITLE)
        w.doModal()
        self.mmenabled = w.mmenabled
        del w
        if self.mmenabled != 0:
            xbmc.executebuiltin('XBMC.RunScript(' + self.srcpath+ "\\lib\\XinBox_MiniMode.py" + "," + self.mmenabled + "," + self.srcpath + ')')
            self.close()
        
    def getaccountsettings(self,account):
        return self.settings.getSettingInListbyname("Accounts",account)
    
    def getinboxsettings(self,inbox,settings):
        return settings.getSettingInListbyname("Inboxes",inbox)
    
    def setupcontrols(self):
        self.clearList()
        self.getControl(80).setLabel(self.lang(10))
        self.getControl(81).setLabel(VERSION)
        MenuItems = [xbmcgui.ListItem(self.lang(11),self.lang(16),"XBlogin.png","XBlogin.png"),
                     xbmcgui.ListItem(self.lang(12),self.lang(17),"XBcreatenew.png","XBcreatenew.png"),
                     xbmcgui.ListItem(self.lang(13),self.lang(19),"XBchangesettings.png","XBchangesettings.png"),
                     xbmcgui.ListItem(self.lang(14),self.lang(19),"XBabouticon.png","XBabouticon.png"),
                     xbmcgui.ListItem(self.lang(15),self.lang(19),"XBquiticon.png","XBquiticon.png")]
        for item in MenuItems:
            self.addItem(item)

    def setupvars(self):
        self.mmenabled = 0
        self.control_action = XinBox_Util.setControllerAction()
        
    def onFocus(self, controlID):
        pass
    
    def onClick(self, controlID):
        if ( controlID == 50):
            if self.getCurrentListPosition() == 0:
                if self.noaccounts:
                    self.launchinfo(22,"",self.lang(93))
                else:self.launchloginmenu()
            elif self.getCurrentListPosition() == 1:
                self.launchcreatemenu()
            elif self.getCurrentListPosition() == 2:
                pass
            elif self.getCurrentListPosition() == 3:
                self.launchabout()
            elif self.getCurrentListPosition() == 4:
                self.close()

    def launchabout(self):
        w = XinBox_About.GUI("XinBox_About.xml",self.srcpath,"DefaultSkin",lang=self.lang)
        w.doModal()
        del w
                    
    def onAction( self, action ):
        print "action = " + str(action.getButtonCode())
        button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
        actionID   =  action.getId()
        try:focusid = self.getFocusId()
        except:focusid = 0
        if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu Button' ):
            self.close()
        elif ( button_key == 'Keyboard Menu Button' or button_key == 'Y Button' or button_key == 'Remote Title' ):
            self.launchinfo(100 + self.getCurrentListPosition(),self.getListItem(self.getCurrentListPosition()).getLabel())

    def launchinfo(self, focusid, label,heading=False,text=False):
        dialog = XinBox_InfoDialog.GUI("XinBox_InfoDialog.xml",self.srcpath,"DefaultSkin",thefocid=focusid,thelabel=label,language=self.lang,theheading=heading,thetext=text)
        dialog.doModal()
        value = dialog.value
        del dialog
        return value
    
    def launchcreatemenu(self):
        winSettings = Account_Settings("XinBox_EditAccountMenu.xml",self.srcpath,"DefaultSkin",0,scriptSettings=self.settings,language=self.lang, title=TITLE,account="")
        winSettings.doModal()
        self.loadsettings()
        del winSettings

    def launchloginmenu(self):
        self.accounts = self.buildaccounts()
        w = XinBox_LoginMenu.GUI("XinBox_LoginMenu.xml",self.srcpath,"DefaultSkin",lang=self.lang,title=TITLE)
        w.doModal()
        self.mmenabled = w.mmenabled
        del w
        if self.mmenabled != 0:
            xbmc.executebuiltin('XBMC.RunScript(' + self.srcpath + "\\lib\\XinBox_MiniMode.py" + "," + self.mmenabled + "," + self.srcpath + ')')
            self.close()
            
    def showKeyboard(self, heading,default="",hidden=0):
        keyboard = xbmc.Keyboard(default,heading)
        if hidden == 1:keyboard.setHiddenInput(True)
        keyboard.doModal()
        if hidden == 1:keyboard.setHiddenInput(False)
        if (keyboard.isConfirmed()):
            return keyboard.getText()
        else:return default