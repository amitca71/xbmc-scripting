      ##########################
      #                        #                      
      #   XinBox (V.0.9)       #         
      #     By Stanley87       #         
      #                        #
#######                        #######             
#                                    #
#                                    #
#   A pop3 email client for XBMC     #
#                                    #
######################################

import xbmcgui, language, time
lang = language.Language().string
import xbmc, sys,os, threading ,xib_util
import shutil
import default
import traceback
import mailchecker
import email
import poplib, mimetypes
import string

SETTINGDIR = default.__scriptsettings__
SCRIPTSETDIR = SETTINGDIR + default.__scriptname__ + "\\"
DATADIR = SCRIPTSETDIR + "data\\"
DELETEFOLDER = "deleted\\"
IDFOLDER = "ids\\"
NEWFOLDER = "new\\"
CORFOLDER = "cor\\"
MAILFOLDER = "mail\\"
SCRIPTFOLDER = default.__scriptpath__
MEDIAFOLDER = SCRIPTFOLDER + "src//skins//media//"
TEMPFOLDER = SCRIPTSETDIR + "temp\\"


class gui( xbmcgui.WindowXMLDialog ):
    def __init__(self,strXMLname, strFallbackPath,strDefaultName,bforeFallback=0):
        print "_init here"
        self.control_action = xib_util.setControllerAction()
        xbmcgui.lock()

    def setupvars(self, arg1, arg2, arg3, arg4, arg5, arg6):
        self.temp3 = arg1
        self.listsize = arg2
        self.emfolder = arg3
        self.CurrentListPosition = arg4
        self.emails = arg5
        inbox = arg6
        if inbox == 1:
    	    self.box1 = 1
    	    self.box2 = 0
        else:
    	    self.box2 = 1
    	    self.box1 = 0    	    
    
    def onInit(self):
        self.openit()

    def openit(self):
        xbmc.executebuiltin("Skin.SetBool(attachlistnotempty)")
        xbmc.executebuiltin("Skin.ToggleSetting(attachlistnotempty)")
        self.attachlabel = self.getControl(79)
        self.attlist = self.getControl(77)
        self.fsoverlay = self.getControl(71)
        self.fsmsgbody = self.getControl(72)
        self.emailinfo = self.getControl(73)
        self.emailrec = self.getControl(74)
        self.attbutn = self.getControl(75)
        self.delbutn = self.getControl(76)
        self.imgagebox = self.getControl(80)
        self.attachlabel.setLabel( lang(202) )
        self.attopen = False
        self.showingimage = False
        self.getemailinfo()
        self.getstatus()
        self.readstatus = "READ"
        self.writestatus()
        self.processEmail(self.temp)
        self.emailinfo.reset()
        self.emailrec.reset()
        self.fsmsgbody.reset()
        self.fsmsgbody.setText(self.msgText)
        self.setFocus(self.fsmsgbody)
        self.emailinfo.addLabel(self.temp3)
        self.emailrec.addLabel( lang( 63 ) + str(self.time) + " - " + str(self.date))
        xbmcgui.unlock()        
        
    def onClick(self, controlID):
        if ( controlID == 76):
            self.deletemail()
        elif ( controlID == 75):
            if not self.attopen:
                self.click = 0
                self.click2 = 0
                self.attopen = True
                xbmc.executebuiltin("Skin.SetBool(attachlistnotempty)")
              #  time.sleep(0.1)
            else:
                self.attopen = False
                xbmc.executebuiltin("Skin.SetBool(attachlistnotempty)")
                xbmc.executebuiltin("Skin.ToggleSetting(attachlistnotempty)")
                self.RemoveImage()
              #  time.sleep(0.1)               
            
    def onAction( self, action ):
        button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
        actionID   =  action.getId()
        try:focusid = self.getFocusId()
        except:focusid = 0
        if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu Button' ):
                self.exitme()
        elif ( button_key == 'A Button' or button_key == 'Keyboard Menu Button'):
            if (focusid == 77):
                self.openattach(self.attlist.getSelectedPosition())

    def openattach(self, arg1):
        filetype = string.split(self.attachments[arg1], '.').pop()
        lcfiletype = string.lower(filetype)
        if lcfiletype=="jpg" or lcfiletype=="jpeg" or lcfiletype=="gif" or lcfiletype=="png" or lcfiletype=="bmp":
            self.click2 = 0
            if not self.showingimage:
                self.click = self.click + 1
                self.ShowImage(self.attachments[arg1])
            else:
                if self.currentimage != self.attachments[arg1]:
                    self.click = 1
                    self.RemoveImage()
                    self.ShowImage(self.attachments[arg1])
                else:
                    self.click = self.click + 1
                    if self.click == 2:
                        self.saveattachment(self.attachments[arg1])
                        self.click = 2
                    elif self.click == 3:
                        self.RemoveImage()
                        self.click = 0
        else:
            if self.click2 == 0:
                self.click2 = 1
                if not self.PlayMedia(self.attachments[arg1]):
                    print "In-compatible file type"
                    self.RemoveImage()
                    self.imgagebox.setImage(MEDIAFOLDER + "XBbadfile.png")
                    self.showingimage = True
                else:
                   self.RemoveImage()
                   self.showingimage = False
            elif self.click2 == 1:
                self.RemoveImage()
                self.showingimage = False
                self.saveattachment(self.attachments[arg1])
                self.click2 = 2
            elif self.click2 == 2:
                if not self.PlayMedia(self.attachments[arg1]):
                    self.RemoveImage()
                    self.showingimage = False
                    self.click2 = 0
                else:
                    self.RemoveImage()
                    self.showingimage = False
                    self.click2 = 1
            

    def saveattachment(self, filename):
        dialog = xbmcgui.Dialog()
        fn = dialog.browse(0, 'Save Attachment to...', 'files')
        if fn:
            path = fn
            print str(path)
            shutil.copy(TEMPFOLDER + filename, path)
            return
        else:return
        

    def PlayMedia(self, filename):
        try:
            xbmc.Player().stop()
        except:pass
        xbmc.Player().play(TEMPFOLDER + filename)
        if xbmc.Player().isPlaying():
            return True
        else:
            return False
        
    def RemoveImage(self):
        self.imgagebox.setImage(MEDIAFOLDER + "XB.png")
        self.showingimage = False   
        
    def ShowImage(self, filename):
        self.currentimage = filename
        self.imgagebox.setImage(TEMPFOLDER + filename)
        self.showingimage = True
        
    def exitme(self):
        self.returnvar1 = self.listsize
        self.close()

    def onFocus(self, controlID):
        pass 

    def getemailinfo(self):
        self.temp = self.CurrentListPosition
        fh = open(self.emfolder + CORFOLDER + str(self.temp)+ ".cor")
        self.updateme = fh.read()
        fh.close()
        fh = open(self.emfolder + MAILFOLDER + str(self.updateme) +".sss")
        self.tempStr = fh.read()
        fh.close()
        return

    def processEmail(self, selected):
        self.attachments = []
        if self.emails[selected].is_multipart():
            for part in self.emails[selected].walk():
                if part.get_content_type() != "text/plain" and part.get_content_type() != "text/html" and part.get_content_type() != "multipart/mixed" and part.get_content_type() != "multipart/alternative":
                    filename = part.get_filename()
                    if not filename:
                        print "Bad attachment - no Filename, Attachment not saved."
                    else:
                        try:
                            f=open(TEMPFOLDER + filename, "wb")
                            f.write(part.get_payload(decode=1))
                            f.close()
                            self.attachments.append(filename)
                        except:
                            print "problem saving attachment " + filename
        for attachment in self.attachments:
            self.attlist.addItem(attachment)        
        if len(self.attachments)==0:
            self.attbutn.setEnabled( False )
        else:
            self.attbutn.setEnabled( True )
        self.printEmail(selected) 

    def printEmail(self, selected):
        self.msgText = ""
        if self.emails[selected].is_multipart():
            for part in self.emails[selected].walk():
                if part.get_content_type() == "text/plain":
                    email = self.parse_email(part.get_payload())
                    self.msgText = email
                    break
        else:
            if self.emails[selected].get_content_type() == "text/html":
                # email in html only, so strip html tags
                email2 = self.parse_email(self.emails[selected].get_payload())
                self.msgText = email2
            else:
                email3 = self.parse_email(self.emails[selected].get_payload())
                self.msgText = email3
        return
    
    def delemail (self, inbox, emailid):
        w = mailchecker.Checkemail(inbox, 0, emailid)
        w.deletemail()
        del w
        return        
        
    
    def getstatus( self ):
        s = self.tempStr.split('|')
        self.readstatus = s[0]
        self.time = s[1]
        self.date = s[2]
        self.mailid = s[3]
        self.emailbody = s[4]
        return
    
    def writestatus (self):  
        f = open(self.emfolder + MAILFOLDER + str(self.updateme) +".sss", "w")
        f.write(self.readstatus + "|" + self.time + "|" + self.date + "|" + self.mailid + "|" + self.emailbody)
        f.close()
        return
    
    def parse_email(self, email):
        self.parsemail = email
        return str(self.parsemail)
    
    def deletemail(self):
        dialog = xbmcgui.Dialog()
        ret = dialog.select( lang( 66 ), [ lang( 67 ), lang( 68 ), lang( 69 )])
        if ret == 0:
            os.remove(self.emfolder + MAILFOLDER + str(self.updateme)+".sss")
            self.listsize  = self.listsize - 1
            self.exitme()
        elif ret == 1:
            if self.box1 == 1:
                self.delemail(1, self.mailid)
            else:
                self.delemail(2, self.mailid)
            self.setFocus(self.delbutn)
        elif ret == 2:
            if self.box1 == 1:
                self.delemail(1, self.mailid)
            else:
                self.delemail(2, self.mailid)
            self.getemailinfo()
            os.remove(self.emfolder + MAILFOLDER + str(self.updateme)+".sss")
            self.listsize  = self.listsize - 1
            self.exitme()
        else:self.setFocus(self.delbutn)
