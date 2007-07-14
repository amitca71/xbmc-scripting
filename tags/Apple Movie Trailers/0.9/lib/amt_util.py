import os

def getSettings():
    try:
        settings = {}
        f = open( os.path.join( os.getcwd(), 'data', 'settings.txt' ).replace( ';', '' ), 'r' )
        s = f.read().split('|')
        f.close()
        settings['trailer quality'] = int( s[0] )
        settings['mode'] = int( s[1] )
        settings['skin'] = s[2]
        settings['save folder'] = s[3]
        settings['startup category'] = int( s[4] )
        settings['thumbnail display'] = int( s[5] )
    except:
        settings = {'trailer quality' : 2, 'mode' : 0, 'skin' : 'Default', 'save folder' : 'f:\\', 'startup category' : 0, 'thumbnail display' : 1}
    return settings

def saveSettings( settings ):
    try:
        f = open( os.path.join( os.getcwd(), 'data', 'settings.txt' ).replace( ';', '' ), 'w' )
        strSettings = '%d|%d|%s|%s|%d|%d' % ( settings['trailer quality'], settings['mode'], settings['skin'], settings['save folder'], settings['startup category'], settings['thumbnail display'],)
        f.write(strSettings)
        f.close()
        return True
    except:
        return False

def setThumbnailDisplay():
    return ['Movie Poster', 'Generic Thumb', 'Off']

def setStartupCategory():
    return ['Newest', 'Exclusives', 'Genre']

def setQuality():
    return ['Low', 'Medium', 'High']

def setMode():
    return ['Stream', 'Download', 'Download & Save']

def setControllerAction():
    return {
                    216 : 'Remote Back Button',
                    247 : 'Remote Menu Button',
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