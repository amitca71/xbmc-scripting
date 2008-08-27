__scriptname__ = 'EvoxT-Trainers'
__author__ = 'bootsy'
__version__ = '0.97'
import xbmc, xbmcgui

dia = xbmcgui.Dialog()
dialog = xbmcgui.DialogProgress()
dialog.create(__scriptname__)
dialog.update(5, 'Importing modules & initializing...')

import sys, os, zipfile
dialog.update(10)
import urllib, re, time
dialog.update(25)

Main_URL = 'http://www.xboxtrainers.net'
Recent_URL = Main_URL + '/t-browse.php?section=recent'
Section0_URL = Main_URL + '/t-browse.php?section=0'
Section1_URL = Main_URL + '/t-browse.php?section=1'
Section2_URL = Main_URL + '/t-browse.php?section=2'
Section3_URL = Main_URL + '/t-browse.php?section=3'
Section4_URL = Main_URL + '/t-browse.php?section=4'
Section5_URL = Main_URL + '/t-browse.php?section=5'
Section6_URL = Main_URL + '/t-browse.php?section=6'
Section7_URL = Main_URL + '/t-browse.php?section=7'
Section8_URL = Main_URL + '/t-browse.php?section=8'

SCRIPTDIR = os.getcwd().replace(';','')+'\\'
RESOURCESDIR = os.path.join(SCRIPTDIR,'resources')
CACHEDIR = os.path.join(RESOURCESDIR,'cache')
DEFAULTTRAINERDIR = os.path.join(SCRIPTDIR,'trainers')
SETTINGSDIR = 'P:\\script_data\\'
SCRIPTSETDIR = SETTINGSDIR + __scriptname__ + '\\'

def setControllerAction(): #Thanks to AMT Team for this :-D
    return {
                61478 : 'Keyboard Up Arrow',
                61480 : 'Keyboard Down Arrow',
                61448 : 'Keyboard Backspace Button',
                61533 : 'Keyboard Menu Button',
                61467 : 'Keyboard ESC Button',
                    216 : 'Remote Back Button',
                    247 : 'Remote Menu Button',
                    229 : 'Remote Title',
                    195 : 'Remote Info',
                    207 : 'Remote 0',
                    166 : 'Remote Up',
                    167 : 'Remote Down',
                    256 : 'A Button',
                    257 : 'B Button',
                    258 : 'X Button',
                    259 : 'Y Button',
                    260 : 'Black Button',
                    261 : 'White Button',
                    274 : 'Start Button',
                    275 : 'Back Button',
                    270 : 'DPad Up',
                    271 : 'DPad Down',
                    272 : 'DPad Left',
                    273 : 'DPad Right'
                }

class EvoxTGUI( xbmcgui.WindowXML ):

    def onInit(self):
        self.make_dirs()
        self.getmycontrols()
        self.textarea.setVisible(False)
        self.resetlist()
        self.set_trainerpath()
        self.version.setLabel(__version__)
        self.control_action = setControllerAction()
        dialog.update(30, 'Fetching recently added trainers')
        try:
            trainer = self.get_trainers(Recent_URL)
        except:
            trainer = ["cant", "find", "recent", "trainers"]
        dialog.update(60)
        try:
            date = self.get_dates(Recent_URL)
        except:
            date = ["cant", "find", "recent", "dates"]
        dialog.update(70)
        try:
            dlcount = self.get_dlcount(Recent_URL)
        except:
            dlcount = ["cant", "find", "download", "counts"]
        dialog.update(80)
        self.set_section(Recent_URL)
        dialog.update(100)
        dialog.close()
        self.buildlists(trainer, date, dlcount)
        self.setFocus(self.trainerlist)

    def unzip(self, filename):
    #Unzips files to path
        file_ = os.path.join(CACHEDIR,filename + '.zip')
        tpath = self.TRAINERPATH
        dialog.update(75,'Unzipping file ...', filename + '.zip')
        try:
            zip = zipfile.ZipFile(file_, 'r')
            namelist = zip.namelist()
            for item in namelist:
                if item.endswith('.etm'):
                    root, name = os.path.split(item)
            if os.path.exists(os.path.join(tpath,name)):
                if dia.yesno('Overwrite?', 'The file ' + name + ' already exists.', 'Overwrite existing file?') != True:
                    zip.close()
                    os.remove(file_)
                    dialog.close()
                    return False, None
            dialog.update(90,'Copying ...', 'File: ' + name, 'Path: ' + tpath)
            for item in namelist:
                if item.endswith('.etm'):
                    directory = os.path.normpath(os.path.join(tpath))
                    file(os.path.join(directory,name),'wb').write(zip.read(item))
            zip.close()
            if os.path.exists(os.path.join(tpath,name)):
                os.remove(file_)
            dialog.update(100)
            dialog.close()
            dia.ok(__scriptname__,'Successesfully installed trainer:',name, 'to: ' + tpath)
            #namelist[0][0:-1] returns the name of the folder the script was installed into (root folder in zip).
            return True, namelist[0][0:-1]
        except:pass

    def view_nfo(self, nfo):
        self.textarea.setText(nfo)

    def get_nfo(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        data = data.replace('&nbsp;', ' ')
        data = data.replace('<br />', '')
        data = data.replace('</a>', '')
        data = data.replace('\r', '')
        data = data.replace('\n|', '|')
        data = data.replace('\n ', ' ')
        data = data.replace('\n!', '!')
        data = data.replace('\n.', '.')
        data = data.replace('\n_', '_')
        data = data.replace('   .                             __', '   .                             __')
        data = data.replace('\n' + ' ', '\n' + ' ')
        data = data.replace('class="code"><h6>NFO:</h6>', '\n' + 'Start nfo:\n')
        data = data.replace('</div><br/><div', '\n' + 'end nfo\n')
        data = data.replace('<a href="http://www.xboxtrainers.net/forum/" target="_blank">', '')
        data = data.replace('<a href="http://www.xboxtrainers.net" target="_blank">', '')
        data = data.replace('<a href="http://forums.evolutionx.info/" target="_blank">', '')
        data = data.replace('<a href="http://forums.maxconsole.com/" target="_blank">', '')
        data = data.replace('<a href="http://forums.maxconsole.net" target="_blank">', '')
        data = data.replace('<a href="http://forums.maxconsole.net/" target="_blank">', '')
        data = data.replace('<a href="http://forums.xbox-scene.com/" target="_blank">', '')
        data = data.replace('<a href="http://www.northfence.com" target="_blank">', '')
        data = data.replace('<a href="http://trainers.schuby.org" target="_blank">', '')
        data = data.replace('<a href="http://trainers.schuby.org/" target="_blank">', '')
        temp = re.compile('Start nfo:[\n](.*?)[\n]end nfo', re.DOTALL + re.MULTILINE + re.IGNORECASE)
        try:
            nf = re.findall(temp, data)
            nfo = nf[0]
        except:
            nfo = ["unable", "to", "create", "nfo"]
        return nfo

    def get_nfo_link(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        data = data.replace("&amp;", "&")
        temp = ('<a href=["](.*?)["]>View Details</a>')
        try:
            lin = re.findall(temp, data)
            nfolink = lin[0]
        except:
            nfolink = ["unable", "to", "find", "dl", "link"]
        return nfolink

    def get_dl_link(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        temp = ('<a href=["](.*?)["]>Download</a>')
        try:
            lin = re.findall(temp, data)
            dllink = lin[0]
        except:
            dllink = ["unable", "to", "find", "dl", "link"]
        return dllink

    def get_trainer_links(self, arg1):
        url = self.section
        data = urllib.urlopen(url)
        data = data.read()
        temp = ('<a href=["](.*?)["] class=["].*?["]>[\n]	.*?	</a>')
        try:
            lin = re.findall(temp, data)
            link = lin[ 0 : ]
        except:
            link = ["unable", "to", "find", "links"]
        url = Main_URL + '/' + link[arg1]
        return url

    def get_filename(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        temp = ('<dd>(.*?).zip</dd>')
        try:
            fil = re.findall(temp, data)
            file = fil[0]
        except:
            file = ["unable", "to", "find", "filename"]
        return file

    def dl_trainer(self, url, filename):
        dest = os.path.join(CACHEDIR,filename + '.zip')
        dialog.update(55,'Downloading Trainer...', 'File: ' + filename + '.zip', 'from: ' + url)
        try:
            urllib.urlretrieve(url,dest)
        except:pass

    def get_trainers(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        temp = ('<a href=["].*?["] class=["].*?["]>[\n]	(.*?)	</a>')
        try:
            trai = re.findall(temp, data)
            trainer = trai[ 0 : ]
        except:
            trainer = ["unable", "to", "find", "trainers"]
        return trainer

    def get_dates(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        data = data.replace("<b>", "*")
        temp = ('<a href=["].*?["] class=["].*?["]>[\n]	.*?	</a></td>[\n]	<td class=["].*?">[\n]	(.*?) .*?[.].*?</td>')
        try:
            dat = re.findall(temp, data)
            date = dat[ 0 : ]
        except:
            date = ["unable", "to", "find", "dates"]
        return date

    def get_dlcount(self, url):
        data = urllib.urlopen(url)
        data = data.read()
        temp = ('<td class=["].*?["]>(.*?)</td>')
        try:
            cou = re.findall(temp, data)
            count = cou[ 0 : ]
        except:
            count = ["unable", "to", "find", "dl count"]
        return count


    def set_trainerpath(self):
        if os.path.exists(os.path.join(SCRIPTSETDIR,'settings.txt')):
            data = open(os.path.normpath(os.path.join(SCRIPTSETDIR,'settings.txt')), 'r')
            settings = data.read().split('\n')
            settings.pop()
            data.close()
            tpath = settings[0]
        else:
            tpath = dia.browse(0,'Select Trainerpath:','files', '', False, False, DEFAULTTRAINERDIR)
            settings_file = open(os.path.join(SCRIPTSETDIR,'settings.txt'), 'w')
            settings_file.write(os.path.normpath(os.path.join(tpath + '\n')))
            settings_file.close()
            dia.ok(__scriptname__,'Actual Trainerpath:', tpath)
        self.TRAINERPATH = os.path.normpath(os.path.join(tpath))

    def get_trainerpath(self):
        dia.ok(__scriptname__,'Actual Trainerpath:', self.TRAINERPATH)

    def set_section(self, sec):
        self.section = sec

    def buildlist(self, array1, array2):
        for x in range (0, len(array1)):
            self.trainerlist.addItem(xbmcgui.ListItem(array1[x], array2[x]))

    def buildlists(self, array1, array2, array3):
        for x in range (0, len(array1)):
            self.trainerlist.addItem(xbmcgui.ListItem(array1[x], array2[x]))
            self.dlcountlist.addItem(array3[x])

    def resetlist(self):
        self.trainerlist.reset()
        self.dlcountlist.reset()

    def make_dirs(self):
        if not os.path.exists(SETTINGSDIR):
            os.mkdir(SETTINGSDIR)
        if not os.path.exists(SCRIPTSETDIR):
            os.mkdir(SCRIPTSETDIR)
        if not os.path.exists(DEFAULTTRAINERDIR):
            os.mkdir(DEFAULTTRAINERDIR)
        if not os.path.exists(CACHEDIR):
            os.mkdir(CACHEDIR)
        return

    def getmycontrols(self):
        self.version = self.getControl(83)
        self.textarea = self.getControl(5)
        self.trainerlist = self.getControl(81)
        self.dlcountlist = self.getControl(82)
        self.Recent_Button = self.getControl(71)
        self.Sec0_Button = self.getControl(72)
        self.Sec1_Button = self.getControl(73)
        self.Sec2_Button = self.getControl(74)
        self.Sec3_Button = self.getControl(75)
        self.Sec4_Button = self.getControl(76)
        self.Sec5_Button = self.getControl(77)
        self.Sec6_Button = self.getControl(78)
        self.Sec7_Button = self.getControl(79)
        self.Sec8_Button = self.getControl(80)

    def onAction(self, action):
        xbmcgui.lock()
        self.dlcountlist.selectItem(self.trainerlist.getSelectedPosition())
        xbmcgui.unlock()
        button_key = self.control_action.get( action.getButtonCode(), 'n/a' )
        actionID   =  action.getId()
        try:focusid = self.getFocusId()
        except:focusid = 0
        try:control = self.getFocus()
        except: control = 0
        if ( button_key == 'Keyboard ESC Button' or button_key == 'Back Button' or button_key == 'Remote Menu Button' ):
            if (focusid == 5):
                self.textarea.setVisible(False)
                self.trainerlist.setVisible(True)
                self.dlcountlist.setVisible(True)
                self.setFocus(self.trainerlist)
            elif dia.yesno(__scriptname__, 'Exit script?'):
                self.close()
        elif ( button_key == 'Y Button' or button_key == 'Keyboard Menu Button' or button_key == 'Remote Info' ):
            if (focusid == 81):
                try:
                    dialog.create(__scriptname__)
                    dialog.update(5, 'Fetching nfo...')
                    self.textarea.reset()
                    dialog.update(15)
                    url = self.get_trainer_links(self.trainerlist.getSelectedPosition())
                    dialog.update(30)
                    nfolink = self.get_nfo_link(url)
                    dialog.update(45)
                    nfo = self.get_nfo(nfolink)
                    dialog.update(60)
                    self.trainerlist.setVisible(False)
                    self.dlcountlist.setVisible(False)
                    dialog.update(85)
                    self.textarea.setVisible(True)
                    self.setFocus(self.textarea)
                    self.view_nfo(nfo)
                    dialog.update(100)
                    dialog.close()
                except:pass
        elif ( button_key == 'White Button' or button_key == 'Keyboard Backspace Button' or button_key == 'Remote Back Button' ):
            if (focusid != 5):
                try:
                    if dia.yesno(__scriptname__, 'Change Trainerpath?', 'Actual: ' + self.TRAINERPATH):
                        if os.path.exists(os.path.join(SCRIPTSETDIR,'settings.txt')):
                            os.remove(os.path.join(SCRIPTSETDIR,'settings.txt'))
                        self.set_trainerpath()
                except:pass

    def onClick(self, controlID):
        if ( controlID == 71):
            # Recent Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching recently added trainers')
            try:
                trainer = self.get_trainers(Recent_URL)
            except:
                trainer = ["cant", "find", "recent", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Recent_URL)
            except:
                date = ["cant", "find", "recent", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Recent_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Recent_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 72):
            # Section0 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching 0-9 trainers')
            try:
                trainer = self.get_trainers(Section0_URL)
            except:
                trainer = ["cant", "find", "0-9", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section0_URL)
            except:
                date = ["cant", "find", "0-9", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section0_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section0_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 73):
            # Section1 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching A-C trainers')
            try:
                trainer = self.get_trainers(Section1_URL)
            except:
                trainer = ["cant", "find", "A-C", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section1_URL)
            except:
                date = ["cant", "find", "A-C", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section1_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section1_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 74):
            # Section2 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching D-F trainers')
            try:
                trainer = self.get_trainers(Section2_URL)
            except:
                trainer = ["cant", "find", "D-F", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section2_URL)
            except:
                date = ["cant", "find", "D-F", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section2_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section2_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 75):
            # Section3 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching G-I trainers')
            try:
                trainer = self.get_trainers(Section3_URL)
            except:
                trainer = ["cant", "find", "G-I", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section3_URL)
            except:
                date = ["cant", "find", "G-I", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section3_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section3_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 76):
            # Section4 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching J-L trainers')
            try:
                trainer = self.get_trainers(Section4_URL)
            except:
                trainer = ["cant", "find", "J-L", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section4_URL)
            except:
                date = ["cant", "find", "J-L", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section4_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section4_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 77):
            # Section5 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching M-O trainers')
            try:
                trainer = self.get_trainers(Section5_URL)
            except:
                trainer = ["cant", "find", "M-O", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section5_URL)
            except:
                date = ["cant", "find", "M-O", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section5_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section5_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 78):
            # Section6 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching P-R trainers')
            try:
                trainer = self.get_trainers(Section6_URL)
            except:
                trainer = ["cant", "find", "P-R", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section6_URL)
            except:
                date = ["cant", "find", "P-R", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section6_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section6_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 79):
            # Section7 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching S-U trainers')
            try:
                trainer = self.get_trainers(Section7_URL)
            except:
                trainer = ["cant", "find", "S-U", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section7_URL)
            except:
                date = ["cant", "find", "S-U", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section7_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section7_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif ( controlID == 80):
            # Section8 Button
            self.resetlist()
            dialog.create(__scriptname__)
            dialog.update(5, 'Fetching V-Z trainers')
            try:
                trainer = self.get_trainers(Section8_URL)
            except:
                trainer = ["cant", "find", "V-Z", "trainers"]
            dialog.update(50)
            try:
                date = self.get_dates(Section8_URL)
            except:
                date = ["cant", "find", "V-Z", "dates"]
            dialog.update(70)
            try:
                dlcount = self.get_dlcount(Section8_URL)
            except:
                dlcount = ["cant", "find", "download", "counts"]
            self.set_section(Section8_URL)
            dialog.update(100)
            dialog.close()
            self.buildlists(trainer, date, dlcount)
            self.setFocus(self.trainerlist)

        elif (controlID == 81):
            # trainerlist
            if dia.yesno(__scriptname__, 'Download selected trainer?'):
                dialog.create(__scriptname__)
                dialog.update(5,'Fetching trainer url...')
                try:
                    url = self.get_trainer_links(self.trainerlist.getSelectedPosition())
                    dialog.update(15, 'Fetching download url...')
                    dllink = self.get_dl_link(url)
                    dialog.update(30, 'Fetching filename...')
                    filename = self.get_filename(url)
                    dialog.update(40, 'Downloading Trainer...')
                    self.dl_trainer(dllink, filename)
                    self.unzip(filename)
                except:pass

    def onFocus(self, controlID):
        pass
    
evt = EvoxTGUI("EvoxT_Main.xml",SCRIPTDIR,"DefaultSkin")
evt.doModal()
del evt