import os
import sys
import xbmcgui, default

from XinBox_Settings import Settings
from XinBox_AccountMenu import AccountSettings

    
class Account_Settings (AccountSettings):
    def __init__(self,xmlName,thescriptPath,defaultName,forceFallback, scriptSettings,language, title="XinBox",account="Default"):
        self.title = title
        AccountSettings.__init__(self, xmlName,thescriptPath,defaultName,forceFallback, scriptSettings,language,title,account)

    def Addaccount(self,settingname,newName):
        defSettingsForAnAccount = {
            "Account Password": ["-","text"],
            "Default Account": ["False","boolean"],
            "Inboxes": [['Inbox',[]],"list"]}
        newSettings = Settings("",self.title,defSettingsForAnAccount,2)
        self.addnewaccount(settingname,newName,newSettings,"settings")

    def Addinbox(self,settingname,newName):
        defSettingsForAnAccount = {
            "Email Address": ["-","text"],
            "POP Server": ["-","text"],
            "SMTP Server": ["-","text"],
            "Account Name": ["-","text"],
            "Account Password": ["-","text"],
            "SERV Inbox Size": ["0","text"],
            "XinBox Inbox Size": ["0","text"],
            "Keep Copy Emails": ["True","boolean"],
            "POP SSL": ["0","text"],
            "SMTP SSL": ["0","text"]}
        newSettings = Settings("",self.title,defSettingsForAnAccount,2)
        self.addinbox(settingname,newName,newSettings,"settings")
