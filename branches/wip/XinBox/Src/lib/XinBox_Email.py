

import xbmc, xbmcgui, time, sys, os,email, string,shutil,re,zipfile
import XinBox_Util
TEMPFOLDER = "P:\\script_data\\XinBox\\Temp\\"
from sgmllib import SGMLParser

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__(self,strXMLname, strFallbackPath,strDefaultName,bforeFallback=0,emailsetts=False,lang=False):
        self.language = lang
        self.emailsettings = emailsetts
   
    def onInit(self):
        self.setupvars()
        self.setupemail()
        self.setupcontrols()

      
    def setupvars(self):
        self.ziplist = []
        self.subject = self.emailsettings[1].get('subject').replace("\n","")
        self.emfrom = self.emailsettings[1].get('from').replace("\n","")
        self.to = self.emailsettings[1].get('to').replace("\n","")
        self.cc = self.emailsettings[1].get('Cc')
        if self.cc == None:
            self.cc = ""
        else:self.cc = self.cc.replace("\n","")
        date = self.emailsettings[1].get('date')
        if date == None:
            mytime = time.strptime(xbmc.getInfoLabel("System.Date") + xbmc.getInfoLabel("System.Time"),'%A , %B %d, %Y %I:%M %p')
            self.sent = time.strftime('%a, %d %b %Y %X +0000',mytime).replace("\n","")
        else:self.sent = str(date).replace("\n","")
        self.attachments = []
        self.replyvalue = 0
        self.click = 0
        self.curpos = 0
        self.showing = False
        self.deleserv = False
        self.returnvalue = "-"
        self.control_action = XinBox_Util.setControllerAction()
        self.attachlist = False
        xbmcgui.lock()
        xbmc.executebuiltin("Skin.SetBool(attachlistnotempty)")
        xbmc.executebuiltin("Skin.ToggleSetting(attachlistnotempty)")
        xbmcgui.unlock()

    def setupemail(self):
        self.getControl(73).addLabel(self.subject + "  " + self.language(260) + "   " + self.emfrom)
        self.settextbox()
        self.getControl(74).addLabel(self.language(261) + self.emailsettings[4] + "-" + self.emailsettings[5])
        self.getControl(80).setImage("XBXinBoXLogo.png")
        self.getControl(90).setLabel("")
        

    def setupcontrols(self):
        self.getControl(50).setEnabled(False)
        self.getControl(80).setImage("XBXinBoXLogo.png")
        self.getControl(81).setEnabled(False)
        self.getControl(89).setLabel(self.language(266))
        self.animating = True
        xbmc.executebuiltin("Skin.SetBool(emaildialog)")
        time.sleep(0.9)
        self.animating = False
        if self.emailsettings[2] == 0:
            self.getControl(64).setEnabled(False)
        else:
            self.getattachments()
            self.getControl(64).setEnabled(True)
        self.setFocusId(61)
        
    def getattachments(self):
        if self.emailsettings[1].is_multipart():
            for part in self.emailsettings[1].walk():
                if part.get_content_type() != "text/plain" and part.get_content_type() != "text/html" and part.get_content_type() != "multipart/mixed" and part.get_content_type() != "multipart/alternative":
                    filename = part.get_filename()
                    if filename != None:
                        try:
                            f=open(TEMPFOLDER + filename, "wb")
                            f.write(part.get_payload(decode=1))
                            f.close()
                            self.attachments.append([filename,TEMPFOLDER + filename,os.path.getsize(TEMPFOLDER + filename)])
                        except:pass
                else:
                    filename = part.get_filename()
                    if filename != None:
                        try:
                            if part.get_content_type() == "text/plain":f=open(TEMPFOLDER + filename, "w")
                            else:f=open(TEMPFOLDER + filename, "wb")
                            f.write(part.get_payload(decode=1))
                            f.close()
                            self.attachments.append([filename,TEMPFOLDER + filename,os.path.getsize(TEMPFOLDER + filename)])
                        except:pass
        if len(self.attachments) != 0:
            for attachment in self.attachments:
                self.getControl(81).addItem(attachment[0])
            self.goattachlist()
                   
    def settextbox(self):
        if self.emailsettings[1].is_multipart():
            for part in self.emailsettings[1].walk():
                if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                    self.body = self.parse_email(part.get_payload())
                    self.getControl(72).setText(self.body)
                    break
        else:
            self.body = self.parse_email(self.emailsettings[1].get_payload())
            self.getControl(72).setText(self.body)

    def parse_email(self, email):
        email = email.replace("\t","          ")
        parser = html2txt()
        parser.reset()
        parser.feed(email)
        parser.close()
        return parser.output()

    def getem(self, myfrom):
        myre = re.search('<([^>]*)>',myfrom).group(1)
        if myre == None:
            return myfrom
        else:return myre

    def goattachlist(self):
        self.animating = True
        self.attachlist = not self.attachlist
        xbmc.executebuiltin("Skin.ToggleSetting(attachlistnotempty)")
        time.sleep(0.9)
        self.click = 0
        self.resetemail()
        self.getControl(81).setEnabled(self.attachlist)
        self.animating = False        
        
    def onClick(self, controlID):
        if not self.animating:
            if controlID == 50:
                self.savezip(self.getCurrentListPosition())
            if controlID == 64:
                self.goattachlist()
            elif controlID == 61:
                self.replyvalue = [self.getem(self.emfrom),"","",self.language(318) + " " + self.subject,self.getreply(self.body),self.attachments]
                self.exitme()
            elif controlID == 62:
                self.replyvalue = ["","","",self.language(319) + " " + self.subject,self.getreply(self.body),self.attachments]
                self.exitme()
            elif controlID == 81:
                self.openattach(self.getControl(81).getSelectedPosition())
            elif controlID == 63:
                dialog = xbmcgui.Dialog()
                if self.emailsettings[6] == "-" or self.deleserv:
                    ret = dialog.select( self.language(271), [self.language(272)])
                else:ret = dialog.select( self.language(271), [ self.language(272), self.language(273), self.language(274)])
                if ret == 0:
                    if self.deleserv:
                        self.returnvalue = 2
                    else:self.returnvalue = 0
                    self.exitme()
                elif ret == 1:
                    self.deleserv = True
                    self.returnvalue = 1
                elif ret == 2:
                    self.returnvalue = 2
                    self.exitme()

    def getreply (self, body):
        newbody = self.language(316) + "\n"
        newbody = newbody + self.language(260) + " " + self.emfrom + "\n"
        newbody = newbody + self.language(310) + " " + self.to + "\n"
        if self.cc != "":newbody = newbody + self.language(311) + " " + self.cc + "\n"
        newbody = newbody + self.language(317) + " " + self.sent + "\n"
        newbody = newbody + self.language(313) + " " + self.subject + "\n\n"
        for line in body.split("\n"):
            newbody = newbody + "> " + line + "\n"
        return newbody
        

    def getsizelabel (self, size):
        if size >= 1024:
            size = size/1024.0
            sizeext = "KB"
            if size >= 1024:
                size = size/1024.0
                sizeext = "MB"
        else:sizeext = "bytes"
        return "%.1f %s" % (size,  sizeext)

    def openattach(self, pos):
        if self.filebel == "Unknown":
            self.saveattachment(pos)
        elif self.filebel == "Text":
            self.showing = True
            if self.click == 0:
                self.click = 1
                self.showtext(pos)
            else:self.saveattachment(pos)
        elif self.filebel == "Audio":
            if self.click == 0:
                xbmc.playSFX(TEMPFOLDER + self.attachments[pos][0])
                self.click = 1
            else:self.saveattachment(pos)
        elif self.filebel == "Video":
            if self.click == 0:
                self.click = 1
                xbmc.Player().play(TEMPFOLDER + self.attachments[pos][0])
            else:self.saveattachment(pos)
        elif self.filebel == "Image":
            self.showing = True
            if self.click == 0:
                self.click = 1
                self.showimage(pos)
            else:self.saveattachment(pos)
        elif self.filebel == "Archive":
            self.showing = True
            if self.click == 0:
                self.click = 1
                self.showzip(pos)
            else:self.saveattachment(pos)

    def showzip(self,pos):
        self.getControl(73).reset()
        self.getControl(73).addLabel(self.language(320) + " " + self.attachments[pos][0])
        self.getControl(74).reset()
        self.getControl(72).setVisible(False)
        self.getControl(63).setEnabled(False)
        self.getControl(62).setEnabled(False)
        self.getControl(61).setEnabled(False)
        self.zippath = TEMPFOLDER + self.attachments[pos][0]
        self.unzip("",True,False)
        if len(self.ziplist) == 0:self.addItem(self.language(279))
        else:
            self.getControl(50).setEnabled(True)
            self.setFocusId(50)

    def saveattachment(self,pos):
        dialog = xbmcgui.Dialog()
        ret = dialog.browse(0, self.language(268) % self.attachments[pos][0], 'files')
        if ret:
            try:
                shutil.copy(TEMPFOLDER + self.attachments[pos][0], ret)
                di = dialog.ok(self.language(49), self.attachments[pos][0],self.language(269), ret)
            except:di = dialog.ok(self.language(93),self.attachments[pos][0],self.language(270), ret)

    def savezip(self, pos):
        dialog = xbmcgui.Dialog()
        ret = dialog.browse(0, self.language(268) % self.ziplist[pos], 'files')
        if ret:
            try:
                self.unzip(ret,False,self.ziplist[pos])
                di = dialog.ok(self.language(49), self.ziplist[pos],self.language(269), ret)
            except:di = dialog.ok(self.language(93),self.ziplist[pos],self.language(270), ret)
        
    def unzip(self, path, listing, myzipfile):
        zip = zipfile.ZipFile(self.zippath, 'r')
        namelist = zip.namelist()
        for item in namelist:
            if listing:
                self.ziplist.append(str(item))
                self.addItem(str(item))
            else:
                if str(item) == myzipfile:
                    file(path + str(item),'wb').write(zip.read(item))
        zip.close()

    def showimage(self, pos):
        self.getControl(73).reset()
        self.getControl(73).addLabel(self.language(320) + " " + self.attachments[pos][0])
        self.getControl(74).reset()
        self.getControl(91).setImage(TEMPFOLDER + self.attachments[pos][0])
        self.getControl(72).setVisible(False)
        self.getControl(63).setEnabled(False)
        self.getControl(62).setEnabled(False)
        self.getControl(61).setEnabled(False)
        
        

    def showtext(self, pos):
        self.getControl(73).reset()
        self.getControl(73).addLabel(self.language(320) + " " + self.attachments[pos][0])
        self.getControl(74).reset()
        f = open(TEMPFOLDER + self.attachments[pos][0], "r")
        self.getControl(72).setText(f.read().replace("\t",""))
        f.close()
        self.getControl(63).setEnabled(False)
        self.getControl(62).setEnabled(False)
        self.getControl(61).setEnabled(False)
        self.setFocusId(72)


    def showattach(self, pos):
        filetype = string.lower(string.split(self.attachments[pos][0], '.').pop())
        self.filebel = XinBox_Util.getfiletypes(filetype)
        self.getControl(90).setLabel(self.language(267) + self.getsizelabel(self.attachments[pos][2]))
        if self.filebel == "Unknown":self.getControl(80).setImage("XBattachfile.png")
        elif self.filebel == "Text":self.getControl(80).setImage("XBattachtext.png")
        elif self.filebel == "Audio":self.getControl(80).setImage("XBattachaudio.png")
        elif self.filebel == "Video":self.getControl(80).setImage("XBattachvideo.png")
        elif self.filebel == "Image":self.getControl(80).setImage("XBattachimage.png")
        elif self.filebel == "Archive":self.getControl(80).setImage("XBattacharchive.png")
            
    def onAction( self, action ):
        if not self.animating:
            button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
            actionID   =  action.getId()
            try:focusid = self.getFocusId()
            except:focusid = 0
            try:control = self.getFocus()
            except: control = 0
            if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu Button' ):
                self.exitme()
            elif focusid == 81:
                if self.curpos != self.getControl(81).getSelectedPosition():
                    self.click = 0
                    if self.showing:
                        self.resetemail()
                self.curpos = self.getControl(81).getSelectedPosition()
                self.showattach(self.getControl(81).getSelectedPosition())

    def resetemail(self):
        self.ziplist = []
        self.getControl(50).setEnabled(False)
        self.showing = False
        self.clearList()
        self.getControl(91).setImage("-")
        self.getControl(72).setVisible(True)
        self.getControl(63).setEnabled(True)
        self.getControl(62).setEnabled(True)
        self.getControl(61).setEnabled(True)
        self.getControl(73).reset()
        self.getControl(74).reset()
        self.setupemail()
               
    def onFocus(self, controlID):
        pass

    def exitme(self):
        self.animating = True
        if self.attachlist:
            xbmc.executebuiltin("Skin.ToggleSetting(attachlistnotempty)")
            time.sleep(0.9)
        xbmc.executebuiltin("Skin.SetBool(emaildialog)")
        xbmc.executebuiltin("Skin.ToggleSetting(emaildialog)")
        time.sleep(0.9)
        self.close()

    def removefiles(self,mydir):
        for root, dirs, files in os.walk(mydir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name)) 

class html2txt(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.pieces = []
        
    def handle_data(self, text):
        self.pieces.append(text)

    def handle_entityref(self, ref):
        if ref=='amp':
            self.pieces.append("&")

    def output(self):
        return " ".join(self.pieces)