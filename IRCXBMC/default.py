#!/usr/bin/env python
# IRC-XBMC - Instant Relay Chat for Xbox Media Center.
# Author: Donno
# Web: None
# Email: Donno (donno45989@yahoo.com.au
# Copyright:    IRC-XBMC by Copyright (C) 2005 Donno
#               The IRCLIB Copyright (C) 1999--2002  Joel Rosdahl


## TODO  (These are the Most Priorty things to do
# Track/Handle Parts/Leaves etc (by Other people)

# CONTROLS
# On Channel View
    # White/Title == Shows User Conext Menu
    # Display == Type/Change Message

"""
Copyright (C) 1989, 1991 Free Software Foundation, Inc.
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.
Full License at http://www.gnu.org/copyleft/gpl.html
"""

#More Help (really need to move this in another file some day)
"""
Thanks to Alex and Alexpoet for the great TUTORIAL and script template. Keep up the great work
Especially for the emulator it is a pure life saver. (Now Ive made mods to the emu to get it working with my other scripts projects :P No way i could have done it from scractch thou :P

People who have has worked on this script
    Donno - donno45989@yahoo.com.au

Testers
    skamm: Tested it also pointed out the Change Channel bug.
    Griever33: the second tester

Others who helped
    hed420: keeping me sane/discussion in #xbmc
    xoop: skinner/gfx designer (tried to help :P)

If you are a develop and the file exist please read IRCX_BOOK.doc which is pretty much everythign i written down.
Sorry about the comments but I feel u can never comment too much. (well u can but its better then nothing :P

Next Features
    -- To User List Sub menu Add Vocie+Op+Kick
    -- Store/Display MOTD
    -- Handle Leaving and Parting Users

Added but buggy/needs little bit of work
    - Set and Get Topic  [ might need to to use another variable so when u go to setopic it will set _changetopic, fucntion to get topic then when it receives it if changetopic = 1 then run the change topic code

Future Features when the project becomes worth it
    - Need a config file so we can set real name, secondary nickname, etc a.
    - I'll try to make a mobile phone SMS libary/some easy way of typing messages
    - Add a shortcut key button/ auto replace so example   hru would become how are you (using a pre simple list)
"""

# // Version History  \\
""" Version History
    14 - Jun - Recoded - Fixed quite a few stupid bugs, started improving it
    24 - Jan - Added: On Kick (basic Kicking supprot not tested too much), Improved: On Topic
    22 - Jan -  Updated the irclib version from 0.4.5 to 0.4.6
    10 - Dec - Worked on rewritting some things/fixed code stuff - Started adding framework-[mainly GUI based] for more stuff - MOTD - Worked on USER Context - Live Testing on Freenode -- Clear all the comments  on Channel Window Inital code
    4 - Dec got it working (sometimes) --- needs tweaking
    3 - Decmember resumed dev
    28 of March - It works on a xbox (sort of)
    8:33am mytime 4th of March I got threading working which means you can now receive and send without the GUI being frozen
    8:05pm 10th of March I fixed the bug with selecting the server from the GUI""
"""

import xbmc, xbmcgui
import irclib, string, os
from time import sleep
from threading import Thread
try: Emulating = xbmcgui.Emulating
except: Emulating = False
from irclib import nm_to_n
#from ircxbmcdic import IRCDict needs more dev/testing (big job but should be worth it) [If i get time i might write my own way of doing this]

__title__ = 'IRC-XBMC'
__author__ = 'Donno'
__credits__ = 'SCRIPTER: Donno \nIRC Libary: Joel Rosdahl\nFirst Tester: skamm \nOther Thanks to Griever33,hed420,xoop'
__version__ = '2.9'

#CHANGE THIS ONLY if u need too -  ONE DAY HOPE these will be change able thorugh the Settings Menu
YOURNICK = "XBMC|User"    #Sets Default NickName
realname = "XBMC"
usrname = "IRCXBMC"
bot_mode = 0            #This enables/disables weather bot mod is enabled (response to certain messages)

themessage = "Hello, Everyone"          #The default message
quitmsg = "Cya, 'I was using " + __title__ + "'" #Quit message

initial_server = "irc.freenode.net"     #Sets Default Server
initial_port = 6667                     #Sets Default Port
#_curchannel = "#xbmc"   #Sets Default Channel
_curchannel = "#xbmc-scripting"   #Sets Default Channel
_curtopic = ""

pm_usrname = "donno"    #Sets default username to PM

DEBUG = 1
irclib.DEBUG = 0
BETA = 0
RootDir = os.getcwd().replace(";","")+"\\"
#RootDir = "Q:\\scripts\\"   #Sets Location to script directory (where this file is located)
#ScriptDir = "IRCXBMC\\"          #Sets Location to extra files for scripts (like background, configs)
ScriptHome =  os.getcwd().replace(";","")+"\\" 

PC_dir = ""

ACTION_Y_BUTTON = 259		# Think it is Y
ACTION_Y_BUTTON = 34		# Think it is Y
ACTION_UNKNOWN = 0			#'Y', black
ACTION_MOVE_LEFT = 1		#Dpad Left
ACTION_MOVE_RIGHT = 2		#Dpad Right
ACTION_MOVE_UP = 3			#Dpad Up
ACTION_MOVE_DOWN = 4		#Dpad Down
ACTION_SKIP_NEXT = 5 		#Left trigger
ACTION_SKIP_PREVIOUS = 6 	#Right trigger
ACTION_SELECT = 7			#'A'
ACTION_BACK = 9				#'B'
ACTION_MENU = 10			#'Back'
ACTION_SHOW_INFO    = 11
ACTION_PAUSE		= 12
ACTION_STOP     = 13		#'Start'
ACTION_DISPLAY  = 18		#'X'
ACTION_WHITE    = 117
ACTION_SELECT_ITEM		= 7
ACTION_HIGHLIGHT_ITEM		= 8
ACTION_PARENT_DIR		= 9

ACTION_NEXT_ITEM		= 14
ACTION_PREV_ITEM		= 15

ACTION_BUTTON_0			= 58
ACTION_BUTTON_1			= 59
ACTION_BUTTON_2			= 60
ACTION_BUTTON_3			= 61
ACTION_BUTTON_4			= 62

#Set now used later
_motd = ""
_requestingmotd = 0

# Varibles
## Mainly For Multi Channel Mantaining
ch_topics = {}    # Eg call about by ch_topics["#xbmc"]  etc :P
ch_userslist = {}    # Eg call about by ch_userslist ["#xbmc"]  etc :P
ch_messages = {}    # Eg call about by ch_messages["#xbmc"]  etc :P

pm_messages = {}    # Eg call about by pm_messages["Username"]  etc :P

if Emulating: RootDir = PC_dir # If emulating then sets root dir to PC_DIR


# Start of New IRC MangagmentClass
class IrcMagamentClass:
    #__int__
    def __init__(self,server,port,nickname,ch,pmusrname):
        print "Inializing IRC Mangement Class"
        self.server = server
        self.port = port
        self.current_channel = ch
        self.nickname = nickname
        self.pm_usrname = pmusrname
        self.connection = ""
        
        print "UserName: %s   Server: %s    Port: %s" % (nickname,server,port)
    def setConnection(self,theconnection):
        self.connection = theconnection
    def getConnection(self):
        return self.connection
class Channel:
    def __init__(self,name,topic,userlist,basemsg):
        print "__init__: Channel Magament"
        self.name = name
        self.topic = topic
        self.userlist = userlist
        self.messages = basemsg

# End of New IRC MangagmentClass
class Splash(xbmcgui.WindowDialog):
    """
        The opening splash screen
    """
    def __init__(self):
        if Emulating: xbmcgui.WindowDialog.__init__(self)
        self.scaleY = ( float(self.getHeight()) / float(480) )
        self.addControl(xbmcgui.ControlImage(0,0,0,0, ScriptHome + "ircx_splash.png"))
        if BETA:
            self.addControl(xbmcgui.ControlImage(0,0,0,0, ScriptHome  + "beta.png"))
    def onAction(self, action):
        if action != "":
            self.close()

class Irc_client(xbmcgui.Window):
    """
        The main window - Server Selection/Basic Options
    """
    def __init__(self):
        if Emulating: xbmcgui.Window.__init__(self)
        xbmcgui.lock()
        self.servernames = []
        self.serveraddress = []
        self.serverports = []
        global ircmg2
        self.ircmg = ircmg2
        self.setCoordinateResolution(6)
        # GUI Start
        self.addControl(xbmcgui.ControlImage(0,0,720,576, ScriptHome  + "background.png"))
        self.addControl(xbmcgui.ControlImage((720 / 2 - 185) , 45, 0, 0, ScriptHome + "ircx_logo.png")) #(screen witdht / 2 - (image widht / 2))

        # Control Decarlation Start
        self.serverlist = xbmcgui.ControlList(250, 130, 200, 225,itemTextXOffset=-5)
        self.addControl(self.serverlist)
        self.lblserver = xbmcgui.ControlLabel(150, 130, 70, 30, "Server:")
        self.addControl(self.lblserver)
        self.lblselserver = xbmcgui.ControlLabel(170, 380, 400, 30, "Selected Server: %s:%s" % (self.ircmg.server,self.ircmg.port))
        self.addControl(self.lblselserver)
        self.lblchannel = xbmcgui.ControlLabel(100, 420, 200, 30, "Channel: " + self.ircmg.current_channel)
        self.addControl(self.lblchannel)
        self.but_change_ch = xbmcgui.ControlButton(350, 420, 200, 30, "Change Channel")
        self.addControl(self.but_change_ch)
        self.lblnick = xbmcgui.ControlLabel(100, 450, 250, 30, "Nickname: " + self.ircmg.nickname)
        self.addControl(self.lblnick)
        self.but_change_nk = xbmcgui.ControlButton(350, 450, 200, 30, "Change Nickname")
        self.addControl(self.but_change_nk)

        SetupButtons(self, 500,200, 90, 30, "Vert",gap=10)
        self.but_connect = AddButon(self,"Connect")
        self.but_help = AddButon(self,"About")
        self.but_quit = AddButon(self,"Quit")

        # Navigation Code Start
        self.but_connect.controlDown(self.but_help)
        self.but_help.controlDown(self.but_quit)
        self.but_quit.controlDown(self.but_change_ch)
        self.but_change_ch.controlDown(self.but_change_nk)
        self.but_change_nk.controlDown(self.but_connect)

        self.but_connect.controlUp(self.but_change_nk)
        self.but_help.controlUp(self.but_connect)
        self.but_quit.controlUp(self.but_help)
        self.but_change_ch.controlUp(self.but_quit)
        self.but_change_nk.controlUp(self.but_change_ch)

        self.serverlist.controlRight(self.but_connect)
        self.but_connect.controlLeft(self.serverlist)
        self.but_help.controlLeft(self.serverlist)
        self.but_quit.controlLeft(self.serverlist)
        # Navigation Code End

        self.loadserverlist()
        self.setFocus(self.serverlist)
        xbmcgui.unlock()

    def onAction(self, action):
        #print "DEBUG: Action button:", action #for emu
        if action == ACTION_Y_BUTTON:
            self.connects()
        if action == ACTION_MENU:
            self.quitstuff() # run the quitting code

    def onControl(self, control):
        if control == self.but_change_ch:
            temp = self.unikeyboard(self.ircmg.current_channel)
            self.lblchannel.setLabel("Channel:  " + temp)
            self.ircmg.current_channel = temp
            global _curchannel
            _curchannel = self.ircmg.current_channel
        if control == self.but_change_nk:
            temp = self.unikeyboard("IRCXBMC")
            global YOURNICK
            self.ircmg.nickname = temp
            self.lblnick.setLabel("Nickname: " + temp)
            YOURNICK = temp
        if control == self.but_quit:
            self.quitstuff() # run the quitting code
        if control == self.but_help:
            # Bring up the help window
            print "Opening About Window"
            childabout = TheAbout()
            childabout.doModal()
        if control == self.but_connect:
            self.connects()
        if control == self.serverlist:
            # The user has select a new server on in the list. Set up the varibles.
            if self.serverlist.getSelectedPosition() != -1:
                selserv = self.servernames[self.serverlist.getSelectedPosition()]
                self.ircmg.port = int(self.serverports[self.serverlist.getSelectedPosition()])
                self.ircmg.server = self.serveraddress[self.serverlist.getSelectedPosition()]
                lbltxt = "Selected Server: " + selserv + ':' + str(self.ircmg.port)
                self.lblselserver.setLabel(lbltxt)

    def unikeyboard(self, default):
        # Open the Virutal Keyboard.
        keyboard = xbmc.Keyboard(default)
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            return keyboard.getText()
        else:
            return default

    def loadserverlist(self):
        self.serverlist.reset()
        self.servernames = self.loadfile()
        self.serveraddress = self.getServerAdresses()
        for i in range(0, len(self.servernames)):
            self.serverlist.addItem(self.servernames[i]) # add the server names to the lsit
        self.setFocus(self.serverlist) #Gives focus(selects) the server list in the GUI

    def loadfile(self):
        # This loades a text file with the server list in.
        inputtxt = open(ScriptHome + 'Servers.txt',"r")
        #Copy the read in data to another varible so we can close the open file
        inputdat = inputtxt.read()
        inputtxt.close()
        servlst = inputdat.split("\n") #This is so each new server is on a different line.
        for l in servlst:
            if l != "":
                item = l.split("=")
                self.servernames.append(item[0])
                self.serveraddress.append(item[1])
                self.serverports.append(item[2])
        return self.servernames
    def getServerAdresses(self):
        return self.serveraddress
    def connects(self):
        global _theconnection
        print "Connecing to %s on port %s " % (self.ircmg.server,self.ircmg.port)
        if self.ircmg.server != "":
            msgok("Connecting " + str(self.ircmg.server) + ":" + str(self.ircmg.port) )
            self.ircmg.connection = Irc_connect(self.ircmg.server, int(self.ircmg.port), YOURNICK)
            _theconnection = self.ircmg.connection
            print  self.ircmg.connection
            try:
                if self.ircmg.connection == "Failed":
                    got_connection = False
                    print "Connection Failed"
                else:
                    print "Connection Established"
                    got_connection = True
            except:
                pass
            if got_connection == True:
                global chanwin
                chanwin = Channel_Win()
                chanwin.doModal()
        else:
            xbmcgui.Dialog().ok(__title__, "You Didn't Select a Server.") # this should never happen but just in case
    def quitstuff(self):
        # Kill the IRC connection. if we have one
        try:
            if not self.ircmg.connection is None:
                print "Connection = Yes"
                got_connection = True
        except:
            got_connection = False
        if got_connection == True:
            if xbmcgui.Dialog().yesno(__title__, "You are still connected do you want to disconnect?"):
                #User selected yes
                #THESE NEEDS TO BE DEBUGED i think disconnect die and close do all same thing
                try:
                    irc.disconnect_all(quitmsg)  # works shows message
                    msgok("You have disconnected from IRC \n Thanks for using " + __title__)
                except:
                    print "Either Connection is not established else we have big error"
                    return
        else:
            msgok("Thanks for using " + __title__)
        self.close()


class Channel_Win(xbmcgui.Window):
    def __init__(self):
        if Emulating: xbmcgui.Window.__init__(self)
        xbmcgui.lock()
        self.setCoordinateResolution(6)
        self.addControl(xbmcgui.ControlImage(0,0,0,0, ScriptHome  + "background.png"))
        self.addControl(xbmcgui.ControlImage(50, 50, 0, 0,ScriptHome + "ircx_logo.png"))
        self.chan_topic = xbmcgui.ControlFadeLabel(60, 530,720-60*2, 30)
        self.addControl(self.chan_topic)
        self.chan_topic.addLabel("")

        self.curmsgline = 0
        # Control Decarlation Start
        self.usrlist = xbmcgui.ControlList(500, 130, 150, 300,itemTextXOffset=-5)
        self.addControl(self.usrlist)
        self.msgbox = xbmcgui.ControlList(40, 130, 460, 300,itemTextXOffset=-5)
        self.addControl(self.msgbox)
        global themessage
        global ircmg2
        self.ircmg = ircmg2
        self.themessage = themessage
        self.mymsg = xbmcgui.ControlLabel(60, 450, 370, 30, self.themessage)
        self.addControl(self.mymsg)

        SetupButtons(self, 520,450, 70, 30, "Hori",gap=10)
        self.but_sendmsg = AddButon(self,"Send")
        self.but_changemsg = AddButon(self,"Type MSG")
        self.but_sendmsg2usr = AddButon(self,"PM USR")

        self.but_chtopic = xbmcgui.ControlButton(500, 50, 150, 30, "Change Topic")
        self.addControl(self.but_chtopic)
        self.but_joinchan = xbmcgui.ControlButton(420, - 50, 150, 30, "Join Chan") # was y = 50
        self.addControl(self.but_joinchan)
        # Control Decarlation End

        # Navigation Code Start
        self.setFocus(self.but_sendmsg)

        self.but_sendmsg.controlRight(self.but_changemsg)
        self.but_changemsg.controlRight(self.but_sendmsg2usr)
        self.but_sendmsg2usr.controlRight(self.usrlist)
        #self.but_joinchan.controlRight(self.msgbox)
        self.but_chtopic.controlRight(self.msgbox)
        self.msgbox.controlRight(self.but_changemsg)
        #self.usrlist.controlRight(self.but_joinchan)
        self.usrlist.controlRight(self.but_chtopic)

        self.but_changemsg.controlLeft(self.but_sendmsg)
        self.but_sendmsg.controlLeft(self.msgbox) #usrlist
        #self.msgbox.controlLeft(self.but_joinchan)
        self.msgbox.controlLeft(self.but_chtopic)
        self.usrlist.controlLeft(self.but_sendmsg2usr)
        self.but_sendmsg2usr.controlLeft(self.but_changemsg)
        #self.but_joinchan.controlLeft(self.usrlist)
        self.but_chtopic.controlLeft(self.usrlist)
        self.but_sendmsg.controlUp(self.usrlist)
        self.msgbox.controlDown(self.but_sendmsg)
         # Navigation Code End

        xbmcgui.unlock()
        self.startircthread() # Executing Function to Create a thread

    def startircthread(self):
        global th
        self.th = ircthread(80)
        self.th.start()

    def enterMessage(self):
        #Opens the keyboard so the user can type the message they want to send.
        self.themessage  = self.unikeyboard(self.themessage )
        self.mymsg.setLabel(self.themessage)

    def unikeyboard(self, default,title=""):
        #Open the Virutal Keyboard.
        theOSK = xbmc.Keyboard(default,title)
        theOSK.doModal()
        if (theOSK.isConfirmed()):
            return theOSK.getText()
        else:
            return default

    def show_hide_usermenu(self,act):
        if self.getFocus() == self.usrlist:
            if (act == 1):
                del self.usm
            else:
                self.usm = UserSubMenu(self)
                self.usm.doModal()

    def onAction(self, action):
        if action == ACTION_MENU:
            self.quitstuffchan()
        if action == ACTION_SHOW_INFO:
            mdv = MOTD_Viewer()
            mdv.doModal()
            del mdv
        if action == ACTION_WHITE:
            self.show_hide_usermenu(0)
        if action == ACTION_DISPLAY:
            # The X button it will bring up the Virtual Keyboard/ enter the message
            self.enterMessage()

    def addLine(self, txt):
        self.msgbox.addItem(txt)
        #self.curmsgline = self.curmsgline + 1
        #self.msgbox.selectItem(curmsgline)
        #Should jump to the new line :P

    def onControl(self, control):
        if control == self.but_sendmsg:
            Send_MSG2Chan(self.ircmg.connection, self.ircmg.current_channel, self.themessage)
        if control == self.usrlist:
            self.show_hide_usermenu()
        if control == self.but_sendmsg2usr:
            self.ircmg.pm_usrname = self.unikeyboard(self.ircmg.pm_usrname)
            Send_PM(self.ircmg.connection, self.ircmg.pm_usrname,self.themessage)
        if control == self.but_joinchan:
            print "The Join Channel Button has Been Disabled"
            #_theconnection.join(_curchannel)
        if control == self.but_changemsg:
            self.enterMessage()
        if control == self.but_chtopic:
            thenewtopic = self.unikeyboard(_curtopic)
            SetTopic(self.ircmg.connection, self.ircmg.current_channel , thenewtopic)

    def addusr(self, username,ch):
        self.usrlist.addItem(username)
        #self.channels[ch].add_user(username) # new feature

    def quitstuffchan(self):
        if xbmcgui.Dialog().yesno(__title__, "Do you want to disconnect?"):
            self.disconn()  # Calls a function that disconnect from the server
            self.close()    # Closes the channel window
        else:
            self.close()    # Closes the the channel window

    def disconn(self):
        self.th.stop()
        sleep(5)
        print "Thread Stopped"
        self.ircmg.connection.disconnect(quitmsg)
        Dprnt("IRC: Disconnect")
        print "Thread Stopped and Connection should be dead" #Could add a check here to see if connection is close
        msgok("You have disconnected from IRC \n Thanks for using " + __title__)

class TheAbout(xbmcgui.WindowDialog):
    # The About Window. Nothing Major here just show it and quit it.
    def __init__(self):
        if Emulating: xbmcgui.WindowDialog.__init__(self)
        self.isaboutplaying = 0
        self.setCoordinateResolution(6)
        self.bgpanel = xbmcgui.ControlImage(720-505, 70, 0,0, 'panel2.png')

        #self.addControl(xbmcgui.ControlImage((screenwidht / 2 - 185) , 45, 0, 0, ScriptHome + "ircx_logo.png")) #(screen witdht / 2 - (image widht / 2))
        self.abouttitle = xbmcgui.ControlLabel(340, 135, 300, 30, __title__ + " - Help")
        self.itemhelpbody = (xbmcgui.ControlTextBox(720-460 ,160,350,280))
        self.quit_help = xbmcgui.ControlLabel(315, 435, 300, 30, "Press BACK to close About.")
        # After a lot of trial and error / guess the position where i wanted it to sit i finnally go it.
        self.addControl(self.bgpanel)
        self.addControl(self.abouttitle)
        self.addControl(self.quit_help)
        self.addControl(self.itemhelpbody)
        #self.itemhelpbody.setText("Welcome to " + __title__ + ". \n Version: " + __version__ + " \n Credits: Donno,  \n Thanks to Alex for the great tutorial and ThreeZee. \n Special Thanks to my First tester: skamm/skam0 not sure where i would be without him. Lifesaver. \n Others: Griever33, hed420 and Tusse \n Thanks to TeknoJuce who got me to revive this project")
        self.itemhelpbody.setText("Welcome to " + __title__ + ". \n Version: " + __version__ + " \n "  +__credits__ +"\n Thanks to TeknoJuce who got me to revive this project \n About Music: Her7 by Paradogs")
        self.setFocus(self.itemhelpbody)
        if xbmc.Player().isPlaying() == 1:
            Dprnt("XBMC: Player: System is Busy")
        else:
            Dprnt("XBMC: Player: System is Idle")
            self.isaboutplaying = 1
            xbmc.Player().play(ScriptHome + "her7.mod")

    def onAction(self, action):
        if action == ACTION_MENU:
            # Something is playing
            if (self.isaboutplaying == 1):
                xbmc.Player().stop() # About Music is playing so stop it :P
            self.CloseMe()
    def CloseMe(self):
        #hmm im hopeinf the using removeControl will try to fix the problem with python when u make to much stuff
        self.removeControl(self.bgpanel)
        self.removeControl(self.abouttitle)
        self.removeControl(self.quit_help)
        self.removeControl(self.itemhelpbody)
        del self.bgpanel
        del self.quit_help
        del self.itemhelpbody
        self.close()

class TheSettings(xbmcgui.Window):
    """
        Aim: Show and Edit the Settings
        TODO: Needs to be totally made
    """
    # This window is for editing the settings such as real name, user name (not nickname), other stuff
    def __init__(self):
      if Emulating: xbmcgui.Window.__init__(self)
      self.setCoordinateResolution(6)
      self.addControl(xbmcgui.ControlImage(0,0, 0,0,  ScriptHome + "background.png"))
      self.addControl(xbmcgui.ControlImage(60,65, 0,0,  ScriptHome + "overlay1.png"))
      screenwidht =  float(self.getWidth())
      self.addControl(xbmcgui.ControlImage((screenwidht / 2 - 185) , 45, 0, 0, ScriptHome + "ircx_logo.png")) #(screen witdht / 2 - (image widht / 2))

      self.abouttitle = xbmcgui.ControlLabel(195, 480, 300, 30, __title__ + " - Config/Settings") #Srets the main title - Text across bottom
      self.itemhelpbody = xbmcgui.ControlTextBox(90, 100, 520, 320)
      self.quit_help = xbmcgui.ControlLabel(220, 420, 300, 30, "Press BACK to goto main screen.") #Srets the main title - Text across top
      # After a lot of trial and error / guess the position where i wanted it to sit i finnally go it.
      self.addControl(self.abouttitle)
      self.addControl(self.quit_help)
      self.addControl(self.itemhelpbody)
      self.itemhelpbody.setText("You can set the settings for " + __title__ + " on this screen.")

    def onAction(self, action):
        if action == ACTION_MENU:
            self.close()

class MOTD_Viewer(xbmcgui.WindowDialog):
    """
        MOTD_Viewer
        Aim: Show the Message of the Day from the Server
        TODO: Needs to be Made
        ADV/FUTURE: Send a /motd for a more up to date copy (some servers send a diff one on first connect)
    """
    def __init__(self):
        if Emulating: xbmcgui.WindowDialog.__init__(self)
        #really need a xbox test
        mywidth = int(self.getWidth())
        self.addControl(xbmcgui.ControlImage((mywidth / 2)  - (543 / 2) ,100,0,400, 'background-filebrowser.png')) # declare up top with rest of gui
        self.motdbox = xbmcgui.ControlTextBox(mywidth / 2 - (543 / 2) + 50, 125, 520 , 400 - 100,)
        msgok("Requesting MOTD")
        _theconnection.motd()
        global _requestingmotd
        _requestingmotd = 1
        print _motd
        self.motdbox.setText(_motd) # just set the motd till the new one comes

    def onAction(self, action):
        if action == ACTION_WHITE:
            self.close()

    def showMOTD(self):
        self.motdbox.setText(_motd)

class UserSubMenu(xbmcgui.WindowDialog):
    """
        UserSubMenu
        Aim: Show a small overlay menu with commands based on selected user
        TODO: Needs Work
    """
    def __init__(self,w):
        if Emulating: xbmcgui.WindowDialog.__init__(self)
        mywidth = int(self.getWidth())
        self.cw = w
        self.addControl(xbmcgui.ControlImage(mywidth - 395 ,25,0,0, ScriptHome  + "usrsubmnu.png")) # declare up top with rest of gui
        SetupButtons(self, 325,130, 210, 30, "Vert",gap=0)
        self.butSendPM = AddButon(self,"Send PM")
        self.butattach = AddButon(self,"Attach")
        self.addControl(xbmcgui.ControlLabel(mywidth - 350 ,200,210,30, "Operation Actions"))
        SetupButtons(self, 360,230, 210, 30, "Vert",gap=0)
        self.but_op = AddButon(self,"Op")
        self.but_vocie = AddButon(self,"Vocie")
        self.but_kick = AddButon(self,"Kick")

        # Navigation Code Start
        self.setFocus(self.butSendPM)
        self.butSendPM.controlDown(self.butattach)
        self.butattach.controlDown(self.but_op)
        self.but_op.controlDown(self.but_vocie)
        self.but_vocie.controlDown(self.but_kick)
        self.but_kick.controlDown(self.butSendPM)

        self.butSendPM.controlUp(self.but_kick)
        self.butattach.controlUp(self.butSendPM)
        self.but_op.controlUp(self.butattach)
        self.but_vocie.controlUp(self.but_op)
        self.but_kick.controlUp(self.but_vocie)
        # Navigation Code End

    def onAction(self, action):
        if action == ACTION_WHITE: #Might make this Black :P
            self.close()

    def onControl(self, control):
        if control == self.butSendPM:
            Dprnt("GUI: Send Message to User")
            un = self.cw.usrlist.getSelectedItem().getLabel()
            if un[0] == "@":
                un = un[1:]
            if un[0] == "+":
                un = un[1:]
            Send_PM(_theconnection, un, self.cw.themessage)
        elif control == self.butattach:
            Dprnt("GUI: Adding Name to front of message")
            un = chanwin.usrlist.getSelectedItem().getLabel()
            if un[0] == "@":
                un = un[1:]
            if un[0] == "+":
                un = un[1:]
            self.cw.themessage = "%s: %s" % (un,self.cw.themessage)
            chanwin.mymsg.setLabel(self.cw.themessage)
        elif control == self.but_op:
            #not yet coded
            #chanwin.usrlist.getSelectedItem().getLabel()  is name of selected user
            Dprnt("GUI: Op the selected user")
        elif control == self.but_vocie:
            #not yet coded
            Dprnt("DEBUG: GUI: Give the selected user Vocie")
        elif control == self.but_kick:
            Dprnt("DEBUG: GUI: Kick the selected user vocie")
        else:
            Dprnt("GUI: New Button with no onControl set yet")

class ircthread(Thread):
    """
        ircthread
        Aim: Create a Thread in order to run the irc checking function
        TODO: Needs some tweaking
    """
    def __init__ (self,time_out):
        Thread.__init__(self)
        self.time_out=time_out
        self.running = 0
    def run(self):
        self.running = 1
        while self.running:
            #irc.process_forever() oringal (that just does a while of process once so it was crap
            irc.process_once()
            sleep(3)
        print "Thread should be Stopped"
    def stop(self):
        print "IRC Thread Stopping"
        self.running = 0

def Irc_connect(serv, tport, nick):
    """
    Function: Irc_connect
    Aim/What it Does: Connects to irc
    """
    global irc
    irc = irclib.IRC()
    try:
        print "Just about to connect"
        #c = irc.server().connect(serv, tport, nick, None, usrname, realname)
        c = irc.server().connect(serv, tport, nick, None, usrname)
        sleep(3) # sleep some time just to make sure everything gets done.
        c.add_global_handler("welcome", on_connect)

        c.add_global_handler("join", on_join)
        c.add_global_handler("motd", on_motd)
        c.add_global_handler("endofmotd",on_motdend)

        c.add_global_handler("currenttopic", on_curtopic)
        c.add_global_handler("topic", on_topic)
        c.add_global_handler("privmsg", on_privmsg)
        c.add_global_handler("ctcp", on_ctcpmsg)
        c.add_global_handler("pubmsg", on_pubmsg)
        c.add_global_handler("namreply", on_getnicklist) #not quite working
        c.add_global_handler("kick", on_kick) #not quite working

        return c
    except irclib.ServerConnectionError, x:
        msgok("Error: Could not connect to server. %s" % x)
        return "Failed"


def Send_PM(connection, user, msg):
    connection.privmsg(user, msg)
    chanwin.addLine("You PMed <" + user + ">: " + msg)

def SetTopic(connection, channel, msg):
    connection.topic(channel, msg)
    chanwin.addLine("You changed the topic of " + channel + " to " + msg)

def Send_MSG2Chan(connection, chan, msg):
    connection.privmsg(chan, msg)
    chanwin.addLine("You: " + msg)

def msgok(msg):
    # This function is used to call generic message box
    dialog = xbmcgui.Dialog()
    dialog.ok(__title__, msg)

def SetupButtons(win,x,y,w,h,a="Vert",f="button-focus.png",nf="button-nofocus.png",gap=0):
    win.numbut  = 0
    win.butx = x
    win.buty = y
    win.butwidth = w
    win.butheight = h
    win.butalign = a
    win.butfocus_img = f
    win.butnofocus_img = nf
    win.gap = gap

def AddButon(w,text):
    if w.butalign == "Hori":
        c =  xbmcgui.ControlButton(w.butx + (w.numbut * w.butwidth + w.gap * w.numbut),w.buty,w.butwidth,w.butheight,text,w.butfocus_img,w.butnofocus_img)
        w.addControl(c)
    elif w.butalign == "Vert":
        c = xbmcgui.ControlButton(w.butx ,w.buty + (w.numbut * w.butheight + w.gap* w.numbut) ,w.butwidth,w.butheight,text,w.butfocus_img,w.butnofocus_img)
        w.addControl(c)
    else:
        c = xbmcgui.ControlButton(w.butx ,w.buty + (w.numbut * w.butheight + w.gap* w.numbut) ,w.butwidth,w.butheight,text,w.butfocus_img,w.butnofocus_img)
        w.addControl(c)
    w.numbut += 1
    return c

def on_connect(connection, event):
    Dprnt("DEBUG: IRC: [Event] On Connect")# Add stuff here if u want somethign to happen when it connects.
    connection.join (_curchannel)
    #connection.topic(_curchannel) # Get topic for channel
    Dprnt("DEBUG: Should have joined Channel " + _curchannel)

def on_kick(connection, event):
    # nm_to_n(event.source())== Person who did it (eg OP), event.arguments()[1] == reason   event.arguments()[0]=person kick,  event.target() == channel
    Dprnt("DEBUG: IRC: [Event] On Kicked")
    # For now easy to shut down app then try to rejoin/maintain connection for another days work
    # Better having some kicking handling then none. (possible Bugs here may be if no reason was said)
    if event.arguments()[0] == YOURNICK:
        chanwin.addLine("You have Kicked from the channel by " +nm_to_n(event.source())+  "(" + event.arguments()[1] + ")")
        msgok("You have been Kicked \n Might be easiy to Reboot XBMC now")
    else:
        #Donno has kicked DonnoII from #xbmc (bye)
        chanwin.addLine(nm_to_n(event.source()) + " has kicked " + event.arguments()[0] + " from " + event.target() +  " ("  + event.arguments()[1] + ")" )

def on_join(connection, event):
    #These means that you or someone else has joined the channel.
    #add the user to the list of usrs in the channel thus draw them on the XBMC gui as a list.
    # Here is where the script should go get the list off all the users and addd them to the GUI
    #self.channels[ch].add_user(nick) # add the usr to the channel usr lst and gui.

    # event.target() == Channel Named
    nick = nm_to_n(event.source()) # changes from nickname!username@hostmask to just nick name
    if YOURNICK == nick:
        Dprnt("IRC: You joined a channel")
        chanwin.addLine("You have joined " + event.target())
        #NEED CODE HERE - Priorty Low  (NOTE can't remember what this was here for)
        return
    else:
        Dprnt("IRC: " + nick + " has joined " + event.target())
        ch = event.target()
        chanwin.addusr(nick,ch)
        chanwin.addLine(nick + " has joined " + event.target())
        #good idea to store a list with all users and add to user list on gui
        return

def on_privmsg (connection, event):
    nick = nm_to_n(event.source()) # this converts form some crap into a string.
    # <<USER>> (PMed) The message goes here.
    #ChannelWin.displaytext(self, "<<" + nick + ">> (PM): " + event.arguments()[0])
    print "<" + nick + "> (PM): " + event.arguments()[0]
    chanwin.addLine("<" + nick + "> (PM): " + event.arguments()[0])
    Notifcate("Private Message","PMed By " + nick)
    #May what to write bot script in another function
    #if bot_mode == 1: #for now ill leave this as another script
        #if event.arguments()[0] = "info":
            # display some nice info :P
            #self.send_someinfo(connection, nick)

def on_motd (connection, event):
    global _motd
    _motd = _motd + event.arguments()[0] #+ "\n"   #adds old motd to new one

def on_motdend (connection, event):
    Dprnt("IRC: MOTD FINSHED")
    if _requestingmotd == 1: # menas the MOTD_VIEWER send a MOTD request so we will tell it we got the MOTD
        MOTD_Viewer.showMOTD()

def on_ctcpmsg (connection, event):
    nick = nm_to_n(event.source()) # this converts form some crap into a string.
    print "<" + nick + "> (CTCP) " + event.arguments()[0]
    global chanwin
    if (event.arguments()[0] == "KILLME"):
        connection.disconnect(quitmsg)
    elif (event.arguments()[0] == "TIME"):
        #connection.ctcp(nick, "TIME" + )
        pass # send time infomation
    elif (event.arguments()[0] == "VERSION"):
        print "We Received VERSION REQUEST"
        connection.ctcp_reply(nick, "VERSION " + get_version())

        try:chanwin.addLine("Received a CTCP VERSION from " + nick)
        except: pass
    else:
        try:
            chanwin.addLine("<" + nick + "> (CTCP): " + event.arguments()[0])
        except: pass
def on_pubmsg (connection, event):
    nick = nm_to_n(event.source())
    print "<" + nick + "> " + event.arguments()[0]
    if  _curchannel == event.target():
        chanwin.addLine("<" + nick + "> : " + event.arguments()[0])
    else:
        # SAVE LINE TO BUFFER/Var (for MultiChan Support)
        pass
    if YOURNICK in event.arguments()[0]:
        Notifcate("Alert (Name)","Msg By " + nick)

def on_topic (connection, e):
    global _curtopic
    # Source == User, Target = Channel  Argument == Topic
    nick = nm_to_n(e.source())
    ch = e.target()
    topic = e.arguments()[0]
    _curtopic = topic
    #ch_topics[str(event.target())] = event.arguments()[0]  # For MultiChannel Support
    if  _curchannel == e.target():
        chanwin.chan_topic.addLabel(_curtopic)
        chanwin.addLine(nick + " changed topic in " + ch + " was changed to " + topic)
    else:
        Dprnt("NOT In Channel with channel change, Note in that Channel")
        ## something like this for multi chan supprot (nick + " changed topic in " + str(event.target()) + " was changed to "   + event.arguments()[0])
    Dprnt("IRC: "+ nick + " changed topic in " + ch + " was changed to "   + topic)

def on_curtopic(c,e):
    #ch_topics[str(event.target())] = event.arguments()[0]  # For MultiChannel Support
    nick = e.target()
    ch = e.arguments()[0]
    topic = e.arguments()[1]
    global _curtopic
    _curtopic = topic
    if _curchannel ==e.arguments()[0]:
        chanwin.chan_topic.addLabel(_curtopic)
        chanwin.addLine("Topic for " + ch + " is changed to " + topic + " set by" + nick)

def on_getnicklist( c, e):
    Dprnt("IRC: EVENT: Receive Nick List")
    ch = e.arguments()[1]
    usrlst = string.split(e.arguments()[2])
    #usrlst.sort
    for nick in usrlst:
        chanwin.addusr(nick,ch)
        if nick[0] == "@":
            nick = nick[1:]
            #self.channels[ch].set_mode("o", nick)
        elif nick[0] == "+":
            nick = nick[1:]
            #self.channels[ch].set_mode("v", nick)
        #self.channels[ch].add_user(nick)
        #ch_userslist[ch].append(nick) # NASTY

def send_someinfo(connection, nick,mynick):
    myinfo = "NickName: %s" % mynick
    connection.privmsg(nick, myinfo)     #send nickname
    # maybe send what listening to (at moment aim is another fork(sub/litte program) xbmc_ircbot.py should be able to do that) (doesn't work at teh moment

def get_version():
    return ">< IRC-XBMC >< - The Instant Relay chat for XBMC by Donno, V:" + str(__version__)

def Notifcate(header,message):
    xbmc.executebuiltin('XBMC.Notification(%s,%s)' % (header,message))

def first_timerun():
    """
    Lets do some basic settings like
    --- ask to be added into submenudialog.xml :P
    """
    pass

def Dprnt(text,minlvl=1):
    if DEBUG: print "DEBUG: " + text

def ShowSplash():
    spl = Splash()
    spl.doModal()
    del spl

def main():
    print "Starting " + __title__
    global ircmg2
    ircmg2 = IrcMagamentClass(initial_server,initial_port,YOURNICK,_curchannel,pm_usrname)
    """
    if Emulating:
        print "Can't Show Splash on PC" # probley with TK (doesn't like killing the first window or some crap)
    else:
         ShowSplash()
    """
    win = Irc_client()
    win.doModal()
    del win
    print __title__ + " has been exited"

if __name__ == "__main__":
    main()



