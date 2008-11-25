'''
This script allows you to control your SmartXX V3 RGB Ambient Light controller.

B-Button			- toggles demo on/off.
X-Button			- toggles pointer.
A-Button			- toggles XBMC.system.pwmcontrol() command on/off. A 'no' sign appears when off.
Y-Button			- toggles pointer step mode on/off. (the pointers move in slow motion) Steps appear when on.
L-Thumbstick		- Controls the pointers.
DPad Up				- Increases time
DPad Down			- Decreases time
Dpad Left			- Changes Mode
Dpad Right			- Changes Mode

Credits:
 - This script was imagined by Pike from Team Xbox Media Center and made possible,
 - by the creative minds of Team Xbox Media Center and Team SmartXX.
'''
__scriptname__ = 'Ambient Light Control Pad'
__author__ = 'Nuka1195'
__url__ = 'http://code.google.com/p/xbmc-scripting/'
__credits__ = 'XBMC TEAM, freenode/#xbmc-scripting'
__version__ = '1.0'


import os, sys
import xbmcgui, xbmc
import threading

resourcesPath = os.path.join(os.getcwd().replace( ";", "" ), 'resources')
sys.path.append(os.path.join(resourcesPath, 'lib'))
sys.path.append(os.path.join(resourcesPath, 'lib', '_PIL.zip'))
from PIL import Image

class windowOverlay(xbmcgui.WindowDialog):
    def __init__(self):
        xbmcgui.WindowDialog.__init__(self)
        self.setupGUI()
        if (not self.SUCCEEDED): self.close()
        else:
            self.loadColorWheel(os.path.join(self.ImagePath, 'color-wheel.png'))
            self.setConstants()
            self.setDefaults()
            self.getSettings()
            self.initPointers()
            self.setOptionLabels()
            self.toggleDemoPad()
            
    def setupGUI(self):
        import guibuilder
        self.ImagePath = os.path.join(resourcesPath, 'images')
        skin = os.path.join(resourcesPath, 'skins', xbmc.getSkinDir(), 'skin.xml')
        if (not os.path.isfile(skin)): skin = os.path.join(resourcesPath, 'skins', 'Project Mayhem III', 'skin.xml')
        guibuilder.GUIBuilder(self,  skin, self.ImagePath, fastMethod=True)
        del guibuilder
        
    def loadColorWheel(self, image):
        self.imgColorWheel = Image.open(image).load()

    def setDefaults(self):
        self.pausedTimer             = None # timer for pointer paused
        self.color                     = [(255, 255, 255), (255, 255, 255)] # color of pointers
        self.mousePos             = [[0, 0], [249, 0]] # x,y coordinate of pointers
        self.method                 = 2 # {0 : 'fade', 1 : 'fadeloop', 2 : 'faderepeat', 3 : 'blink', 4 : 'switch', 5 : 'none'}
        self.time                     = 1000 # msec time of effect
        self.autoPWM                 = True # True == send pwmcommand on pointer paused
        self.pointer                 = False # True == end color pointer / False == start color pointer
        self.stepMovement         = False # True == pointers move in slow stepped increments
        self.patch                    = True # True == setColorDiffuse() method patch exists
        self.demoRunning         = False # True if a demo is running
        self.demoPadClosed        = True # True if the demo pad is closed
        self.demoPadToggling     = False # True while the demo pad is moving
        self.switch                    = True # True == 'switch' method is end color
        
    def setConstants(self):
        self.increment = 10
        self.methods = {0 : 'fade', 1 : 'fadeloop', 2 : 'faderepeat', 3 : 'blink', 4 : 'switch', 5 : 'none'}
        self.fromTo = ('start', 'end')
        self.controllerAction = {
            256 : 'A Button',
            257 : 'B Button',
            258 : 'X Button',
            259 : 'Y Button',
            260 : 'Black Button',
            261 : 'White Button',
            274 : 'Start Button',
            275 : 'Back Button',
            264 : 'Left ThumbStick',
            276 : 'Left ThumbStick Button',
            280 : 'Left ThumbStick Up',
            281 : 'Left ThumbStick Down',
            282 : 'Left ThumbStick Left',
            283 : 'Left ThumbStick Right',
            265 : 'Right ThumbStick',
            277 : 'Right ThumbStick Button',
            266 : 'Right ThumbStick Up',
            267 : 'Right ThumbStick Down',
            268 : 'Right ThumbStick Left',
            269 : 'Right ThumbStick Right',
            262 : 'Left Trigger Button',
            278 : 'Left Trigger Analog',
            263 : 'Right Trigger Button',
            279 : 'Right Trigger Analog',
            270 : 'DPad Up',
            271 : 'DPad Down',
            272 : 'DPad Left',
            273 : 'DPad Right'
        }

    def saveSettings(self):
        try:
            fname = os.path.join(resourcesPath, 'settings.txt')
            f = open(fname, 'w')
            s = '%d|%d|%d|%d|%d|%d' % (self.mousePos[0][0], self.mousePos[0][1], self.mousePos[1][0], self.mousePos[1][1], self.method, self.time,)
            f.write(s)
        except: print "Error: Saving settings file!"
        else: f.close()

    def getSettings(self):
        try:
            fname = os.path.join(resourcesPath, 'settings.txt')
            if (os.path.isfile(fname)):
                f = open(fname, 'r')
                v = f.read().split('|')
                f.close()
                self.mousePos = [[float(v[0]), float(v[1])], [float(v[2]), float(v[3])]]
                self.method = int(v[4])
                self.time = int(v[5])
        except: pass

    def initPointers(self):
        for c in range(2): 
            self.pointer = (c != 1)
            self.movePointer((0, 0))

    def changeMethod(self, v):
        self.method += v
        if (self.method < 0): self.method = len(self.methods) - 1
        elif (self.method > (len(self.methods) - 1)): self.method = 0
        self.setOptionLabels()
        if (self.autoPWM): self.timerPWMCommand()

    def changeTime(self, v):
        self.time += (v * self.increment)
        if (self.time < 0): self.time = 0
        self.setOptionLabels()
        if (self.autoPWM): self.timerPWMCommand()

    def getColor(self, pos):
        self.color[self.pointer] = self.imgColorWheel[int(pos[0]), int(pos[1])]
        self.setControls()
        
    def setControls(self):    
        self.controls[250 + self.pointer].setLabel('%s color: #%02x%02x%02x' % (self.fromTo[self.pointer], self.color[self.pointer][0], self.color[self.pointer][1], self.color[self.pointer][2]), 'special12', '0xFF%02x%02x%02x' % (self.color[self.pointer][0], self.color[self.pointer][1], self.color[self.pointer][2]))
        self.controls[110 + self.pointer].setLabel('%s: #%02x%02x%02x' % (self.fromTo[self.pointer], self.color[self.pointer][0], self.color[self.pointer][1], self.color[self.pointer][2],))
        try:
            self.controls[40 + self.pointer].setColorDiffuse('0xFF%02x%02x%02x' % (self.color[self.pointer][0], self.color[self.pointer][1], self.color[self.pointer][2],))
        except: self.patch = False

    def setOptionLabels(self):
        self.controls[200].setLabel('change method: %s' % (self.methods[self.method],))
        self.controls[201].setLabel('time msec: %d' % (self.time,))

    def execCommand(self):
        #self.controls[12].setLabel('c: (#%02x%02x%02x,#%02x%02x%02x,%s,%d)' % (self.color[0][0], self.color[0][1], self.color[0][2], self.color[1][0], self.color[1][1], self.color[1][2], self.methods[self.method], self.time,))
        self.pausedTimer = None
        xbmc.sleep(20)
        xbmc.executebuiltin('XBMC.system.pwmcontrol(#%02x%02x%02x,#%02x%02x%02x,%s,%d)' % (self.color[0][0], self.color[0][1], self.color[0][2], self.color[1][0], self.color[1][1], self.color[1][2], self.methods[self.method], self.time,))

    def movePointer(self, arg):
        try:
            xbmcgui.lock()
            for c in range(2):
                self.mousePos[self.pointer][c] += (arg[c] * (0.2 + (0.8 * (self.stepMovement == False))))
                if (self.mousePos[self.pointer][c] < 0): self.mousePos[self.pointer][c] = 0
                elif (self.mousePos[self.pointer][c] > 249): self.mousePos[self.pointer][c] = 249
            self.controls[100 + self.pointer].setPosition(int(self.mousePos[self.pointer][0]) + self.coordinates[0] + self.positions[50][0], int(self.mousePos[self.pointer][1]) + self.coordinates[1]    + self.positions[50][1])
            self.controls[110 + self.pointer].setPosition(int(self.mousePos[self.pointer][0]) + self.coordinates[0] + self.positions[50][0] + (self.positions[110 + self.pointer][0] - self.positions[100 + self.pointer][0]), int(self.mousePos[self.pointer][1]) + self.coordinates[1] + self.positions[50][1] + (self.positions[110 + self.pointer][1] - self.positions[100 + self.pointer][1]))
            self.getColor(self.mousePos[self.pointer])
        except: pass
        xbmcgui.unlock()
        if (self.autoPWM): self.timerPWMCommand()

    def timerPWMCommand(self):
        try:
            if (self.pausedTimer): self.pausedTimer.cancel()
        except: pass
        self.pausedTimer = threading.Timer(0.3, self.execCommand, ())
        self.pausedTimer.start()

    def cancelStepMovement(self):
        self.stepTimer = None
        self.stepTimerRunning = False
    
    def toggleAutoPWM(self):
        self.autoPWM = not self.autoPWM
        self.controls[300].setVisible(not self.autoPWM)
        if (self.autoPWM): self.execCommand()

    def toggleStepMovement(self):
        self.stepMovement = not self.stepMovement
        self.controls[310].setVisible(self.stepMovement)

    def togglePointer(self):
        self.controls[100 + (self.pointer)].setImage(os.path.join(self.ImagePath, 'pointer-nofocus.png'))
        self.pointer = not self.pointer
        self.controls[100 + (self.pointer)].setImage(os.path.join(self.ImagePath, 'pointer-focus.png'))
        self.cancelStepMovement()

    def exitScript(self):
        self.saveSettings()
        self.stopDemo()
        if (self.pausedTimer): self.pausedTimer.cancel()
        for thread in threading.enumerate():
            if (thread.isAlive() and thread != threading.currentThread()):
                thread.join(1)
        self.close()

    def toggleDemoPad(self):
        self.demoPadClosed = not self.demoPadClosed
        if (not self.demoPadToggling): 
            self.padThread = threading.Thread(target=self.slideDemoPad, args=())
            self.padThread.start()

    def slideDemoPad(self):
        self.demoPadToggling = True
        # set starting positions of pad elements
        posx = []
        for x in range(6):
            posx.append(self.positions[500 + x][0] - (180 * (self.demoPadClosed == True)))
        # pad is opening start the demo
        if (not self.demoPadClosed): self.startDemo()
        # slide pad open/closed
        while (posx[0] <= (self.positions[500][0]) and posx[0] >= (self.positions[500][0] - 180)):
            if (self.demoHalt): break
            try:
                xbmcgui.lock()
                step = (self.demoPadClosed - 1) + (self.demoPadClosed == True)
                for x in range(6):
                    posx[x] += step
                    self.controls[500 + x].setPosition(posx[x] + self.coordinates[0], self.positions[500 + x][1] + self.coordinates[1])
            except: pass
            xbmcgui.unlock()
            xbmc.sleep(5)
        self.demoPadToggling = False
        if (self.demoPadClosed): self.stopDemo()

    def onControl(self, control):
        pass

    def onAction(self, action):
        buttonDesc = self.controllerAction.get(action.getButtonCode(), 'n/a')
        if (buttonDesc == 'Back Button'): self.exitScript()
        elif (buttonDesc == 'DPad Left'): self.changeMethod(-1)
        elif (buttonDesc == 'DPad Right'): self.changeMethod(1)
        elif (buttonDesc == 'DPad Up'): self.changeTime(1)
        elif (buttonDesc == 'DPad Down'): self.changeTime(-1)
        elif (buttonDesc == 'B Button'): self.toggleDemoPad()
        elif (buttonDesc == 'A Button'): self.toggleAutoPWM()
        elif (buttonDesc == 'X Button'): self.togglePointer()
        elif (buttonDesc == 'Y Button'): self.toggleStepMovement()
        elif (buttonDesc == 'Left ThumbStick'):
            self.movePointer((action.getAmount1(), -1*action.getAmount2()))

    def startDemo(self):
        if (self.patch):
            self.demoHalt = False
            self.demoThread = demo(self)
        
    def stopDemo(self):
        self.demoHalt = True
        while self.demoRunning:
            xbmc.sleep(50)

class demo(threading.Thread):
    def __init__(self, win):
        threading.Thread.__init__(self)
        self.win         = win
        self.switch     = False
        self.start()

    def run(self):
        self.win.demoRunning = True
        while (not self.win.demoHalt):
            if (self.win.methods[self.win.method] == 'fade'): self.demoFade(0)
            elif (self.win.methods[self.win.method] == 'fadeloop'): self.demoFade(1)
            elif (self.win.methods[self.win.method] == 'faderepeat'): self.demoFade(2)
            elif (self.win.methods[self.win.method] == 'blink') : self.demoBlink()
            elif (self.win.methods[self.win.method] == 'switch'): self.demoSwitch()
            elif (self.win.methods[self.win.method] == 'none'): self.demoNone()
        self.win.demoRunning = False
        
    def demoNone(self):
        self.win.controls[503].setVisible(False)
        self.win.controls[504].setVisible(False)
        while (self.win.methods[self.win.method] == 'none' and not self.win.demoHalt):
            xbmc.sleep(100)
        
    def demoSwitch(self):
        self.switch = not self.switch
        self.win.controls[503].setVisible(self.switch == 0)
        self.win.controls[504].setVisible(self.switch == 1)
        while (self.win.methods[self.win.method] == 'switch' and not self.win.demoHalt):
            self.win.controls[503 + self.switch].setColorDiffuse('0xFF%02x%02x%02x' % (self.win.color[self.switch][0], self.win.color[self.switch][1], self.win.color[self.switch][2],))
            xbmc.sleep(100)
            
    def demoBlink(self):
        ambient = True
        while (self.win.methods[self.win.method] == 'blink' and self.win.time and not self.win.demoHalt):
            stime = int(float(self.win.time) / float(10))
            ambient = not ambient
            self.win.controls[503].setVisible(ambient == 0)
            self.win.controls[504].setVisible(ambient == 1)
            for i in xrange(stime):
                if (self.win.methods[self.win.method] != 'blink' or self.win.demoHalt or not self.win.time): break
                self.win.controls[503 + ambient].setColorDiffuse('0xFF%02x%02x%02x' % (self.win.color[ambient][0], self.win.color[ambient][1], self.win.color[ambient][2],))
                xbmc.sleep(10)

    def demoFade(self, fade): # fade, fadeloop or faderepeat method
        fadeloop = False
        runonce = False
        while (self.win.method == fade and self.win.time and not self.win.demoHalt):
            while (self.win.method == fade and self.win.time and not self.win.demoHalt and not runonce):
                stime = int(float(self.win.time) / float(256))
                runonce = (fade == 0)
                if (fade == 2): fadeloop = not fadeloop
                else: fadeloop = True
                self.win.controls[503].setVisible(True)
                self.win.controls[504].setVisible(True)
                for alpha in xrange(256):
                    if (self.win.method != fade or self.win.demoHalt or not self.win.time): break
                    self.win.controls[503 + fadeloop].setColorDiffuse('0x%02x%02x%02x%02x' % (255 - alpha, self.win.color[fadeloop == False][0], self.win.color[fadeloop == False][1], self.win.color[fadeloop == False][2],))
                    self.win.controls[504 - fadeloop].setColorDiffuse('0x%02x%02x%02x%02x' % (alpha, self.win.color[fadeloop == True][0], self.win.color[fadeloop == True][1], self.win.color[fadeloop == True][2],))
                    xbmc.sleep(stime)
            xbmc.sleep(50)


def main():
    MyDisplay = windowOverlay()
    if (MyDisplay.SUCCEEDED): MyDisplay.doModal()
    del MyDisplay

if (__name__ == '__main__'):
    main()
    sys.modules.clear()
