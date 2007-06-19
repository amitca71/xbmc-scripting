"""
    WindowSettings

    A WindowXML setup to handle the basis modifying the settings provided by the settings class

    Author: Sean Donnellan (Donno)  [darkdonno@gmail.com]
    Depends on: xbmcgui, xbmc, os
    Requires: A Setting and Language class passed to it

    How to Use:
        from windowsettings import WindowSettings
        class className(WindowSettings):
            def __init__(self,xmlName,thescriptPath,defaultName,forceFallback):
                WindowSettings.__init__(self, xmlName,thescriptPath,defaultName,forceFallback, scriptSettings, lang, __title__)
                
        # the point is u pass all the main info on as well as the settings and language classes and title
"""


import xbmcgui,traceback
import xbmc
import os
import xib_util



# Maybe make add inbox a dialog over the top of this account :-D


### Edit Account
##
##
class WindowSettings(xbmcgui.WindowXML):
    def __init__(self, xmlName, thescriptPath,defaultName,forceFallback, scriptSettings,language, title, account):
        self.account = account
        if self.account == "XinBoxDefault":
            self.newaccount = True
        else:self.newaccount = False
        
        self.title = title
        self.thescriptPath = thescriptPath
        self.language = language.string

        self.theSettings = scriptSettings
        
        if self.newaccount:
            self.accountname = "-"
            self.accountpass = "-"
            self.defaultaccount = False
        else:
            self.accountSettings = self.getaccountsettings(self.account)
            self.accountinboxes = self.buildinboxdict(self.accountSettings)

    def buildinboxdict(self,accountsettings):
        self.inboxes = {} 
        for set in self.accountSettings.getSetting("Inboxes")[1] :
            self.inboxes[set[0]] = set[1]
        return self.inboxes

    def getinboxsettings(self,accountsettings,inbox):
        return accountsettings.getSettingInListbyname("Inboxes",inbox)

    def getaccountsettings(self,account):
        return self.theSettings.getSettingInListbyname("Accounts",account)

    
    def onInit(self):
        self.control_action = xib_util.setControllerAction()
        self.list2 = self.getControl(88)
        self.buttonids = [61,62,63,64,64]
        if self.newaccount:
            self.getControl(80).setLabel(self.language(50))
        else:self.getControl(80).setLabel(self.language(74))
        self.builsettingsList()
        self.buildinboxlist()
        for ID in self.buttonids:
            self.getControl(ID).setLabel(self.language(ID))
        self.getControl(82).setLabel(self.language(20))
        self.getControl(83).setLabel(self.language(21))
    
    def builsettingsList(self):
        if self.newaccount:
            self.addItem(self.SettingListItem(self.language(51),""))
            self.addItem(self.SettingListItem(self.language(52),""))
            self.addItem(self.SettingListItem(self.language(53),""))
        else:
            for set in self.accountSettings.settings:
                if self.accountSettings.getSettingType(set) == "text" or self.accountSettings.getSettingType(set) == "boolean":
                    self.addItem(self.SettingListItem(set, self.accountSettings.getSetting(set)))

    def buildinboxlist(self):
        if self.newaccount:
            self.list2.addItem(self.SettingListItem(self.language(75), ""))
        else:
            for set in self.accountinboxes:
                self.list2.addItem(self.SettingListItem(set, ""))
##        test = self.inboxes[self.getListItem(4).getLabel()]
##      # will be able to do: test = self.inboxes[self.getListItem(self.getCurrentListPosition()).getLabel()]  
##        print "test for inbox = " + str(test)

    def onAction( self, action ):
        button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
        actionID   =  action.getId()
        try:focusid = self.getFocusId()
        except:focusid = 0
        if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu Button' ):
            self.close()
##        elif ( button_key == 'Keyboard Menu Button' or button_key == 'Y Button' or button_key == 'Remote Title' ):
##            self.launchinfo(100 + self.getCurrentListPosition(),self.getListItem(self.getCurrentListPosition()).getLabel())

    def onClick(self, controlID):
        if ( controlID == 51):
            curPos  = self.getCurrentListPosition()
            curItem = self.getListItem(curPos)
            curName = curItem.getLabel()
            curName2 = curItem.getLabel2()
            if self.newaccount:
                if curName == self.language(51):
                    value = self.showKeyboard(self.language(66) % curName,curName2)
                    self.accountname = value
                    curItem.setLabel2(value)
                elif curName == self.language(52):
                    value = self.showKeyboard(self.language(66) % curName,curName2)
                    self.accountpass = value
                    curItem.setLabel2(value)
                elif curName == self.language(53):
                    self.defaultaccount = not self.defaultaccount
                    self.getControl(104).setSelected(self.defaultaccount)
            else:
                type = self.accountSettings.getSettingType(curName)
                if (type == "text"):
                    value = self.showKeyboard(self.language(66) % curName,curName2)
                    curItem.setLabel2(value)
                    self.accountSettings.setSetting(curName,value)
                    if curName == self.language(51):
                        self.theSettings.setSettingnameInList("Accounts",curName2,value)
                elif (type == "boolean"):
                    self.defaultaccount = not self.defaultaccount
                    self.getControl(104).setSelected(self.defaultaccount)
                    self.accountSettings.setSetting(curName,str(self.defaultaccount))
        elif ( controlID == 64):
            if self.newaccount:
                self.Addsetting("Accounts",self.accountname)
                self.accountSettings = self.getaccountsettings(self.accountname)
                self.accountSettings.setSetting(self.language(51),self.accountname)
                self.accountSettings.setSetting(self.language(52),self.accountpass)
                self.accountSettings.setSetting(self.language(53),str(self.defaultaccount))
            self.theSettings.saveXMLfromArray()
            self.close()

    def addnewItem(self, settingname,value1,value2="",type="text"):
        self.theSettings.addSettingInList(settingname,value1,value2,"settings")
        return

    def onFocus(self, controlID):
        pass

    def showKeyboard(self, heading,default=""):
        # Open the Virutal Keyboard.
        keyboard = xbmc.Keyboard(default,heading)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            return keyboard.getText()
        else:
            return default
        
    def SettingListItem(self, label1,label2):
        if label2 == "True":
            self.defaultaccount = True
            self.getControl(104).setSelected(self.defaultaccount)
            return xbmcgui.ListItem(label1,"","","")
        elif label2 == "False":
            self.defaultaccount = False
            self.getControl(104).setSelected(self.defaultaccount)
            return xbmcgui.ListItem(label1,"","","")
        else:
            return xbmcgui.ListItem(label1,label2,"","")

    def showKeyboard(self, heading,default=""):
        # Open the Virutal Keyboard.
        keyboard = xbmc.Keyboard(default,heading)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            return keyboard.getText()
        else:
            return default
