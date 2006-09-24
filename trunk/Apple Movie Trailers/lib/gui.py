import xbmc, xbmcgui
import sys, os
import cachedhttp_mod as cachedhttp
import trailers

fetcher = cachedhttp.CachedHTTP()
fetcher_with_dialog = cachedhttp.CachedHTTPWithProgress()

class GUI( xbmcgui.Window ):
    def __init__( self ):
        self.setupGUI()
        if ( not self.SUCCEEDED ): self.close()
        else:
            #########################################
            self.controls['Settings Button']['control'].setEnabled(False)
            #########################################
            #self.initVariables()
            self.setupConstants()
            self.trailers = trailers.Trailers()
            self.showCategories()
            self.setGenre( 'Newest' )
            self.getTrailerInfo(  self.controls['Newest List']['control'].getSelectedItem() )

    def setupGUI(self):
        import guibuilder
        skinPath = os.path.join( os.getcwd(), 'skins' ).replace( ';', '' ) # workaround apparent xbmc bug - os.getcwd() returns an extraneous semicolon (;) at the end of the path
        self.skinPath = os.path.join( skinPath, self.getSkin( skinPath ) )
        self.imagePath = os.path.join( self.skinPath, 'gfx' )
        guibuilder.GUIBuilder( self, os.path.join( self.skinPath, 'skin.xml' ), self.imagePath, useDescAsKey=True, debug=False )
        del guibuilder

    def getSkin( self, skinPath ):
        try:
            f = open( os.path.join( skinPath, 'currentskin.txt' ) )
            skin = f.read()
            f.close()
        except:
            skin = 'Default'
        return skin

    #def initVariables( self ):
        #self.currentList = 'Newest List'
        #self.previousList = self.currentList
        #self.genre = 'Newest'

    def setupConstants( self ):
        self.controllerAction = {
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

    def createConf( self, filename ):
        try:
            if ( not os.path.isfile( filename + '.conf' ) ):
                f = open( filename + '.conf' , 'w' )
                f.write( 'nocache=1' )
                f.close()
        except: pass

    def showVideo( self, title ):
        filename = self.trailers.get_video( self.genre, title )
        #self.setCategoryLabel('G:%s T:%s' % (self.genre, title,))
        #xbmc.output('Apple Movie Trailers: url = %s' % ( filename, ) )
        if filename:
            ## don't create conf file for streaming
            #    self.createConf( filename )
            xbmc.Player( xbmc.PLAYER_CORE_MPLAYER ).play( filename )

    def showTrailerInfo( self, title ):
        thumbnail, description = self.trailers.get_trailer_info( self.genre, title )
        # Trailer Thumbnail
        self.controls['Trailer Thumbnail']['control'].setImage( thumbnail )
        # Trailer Description
        self.controls['Trailer Title']['control'].setLabel( title )
        self.controls['Trailer Info']['control'].reset()
        if description:
            self.controls['Trailer Info']['control'].setText( description )

    def showTrailers( self, genre ):
        self.controls['Trailer List']['control'].reset()
        self.controls['Exclusives List']['control'].reset()
        self.controls['Newest List']['control'].reset()
        if ( genre == 'Newest' ):
            titles = self.trailers.get_newest_list()
            for title in titles: # now fill the list control
                thumbnail, description = self.trailers.get_trailer_info( genre, title )
                l = xbmcgui.ListItem( title, '', thumbnail )
                self.controls['Newest List']['control'].addItem( l )
        
        elif ( genre == 'Exclusives' ):
            titles = self.trailers.get_exclusives_list()
            for title in titles: # now fill the list control
                thumbnail, description = self.trailers.get_trailer_info( genre, title )
                l = xbmcgui.ListItem( title, '', thumbnail )
                self.controls['Exclusives List']['control'].addItem( l )
        
        elif ( genre != 'Genre' ):
            titles = self.trailers.get_trailer_list( genre )
            for title in titles: # now fill the list control
                thumbnail, description = self.trailers.get_trailer_info( genre, title )
                l = xbmcgui.ListItem( title, '', thumbnail )
                self.controls['Trailer List']['control'].addItem( l )
    
    def showCategories( self ):
        self.controls['Genre List']['control'].reset()
        for genre in self.trailers.get_genre_list():
            l = xbmcgui.ListItem( genre )
            self.controls['Genre List']['control'].addItem( l )

    def exitScript(self):
        self.close()
    
    def showList( self, key ):
        #self.previousList = self.currentList
        #self.currentList = key
        self.controls['Exclusives List']['control'].setVisible( key == 'Exclusives List' )
        self.controls['Exclusives List']['control'].setEnabled( key == 'Exclusives List' )
        self.controls['Newest List']['control'].setVisible( key == 'Newest List' )
        self.controls['Newest List']['control'].setEnabled( key == 'Newest List' )
        #self.controls['Featured HD List']['control'].setVisible( key == 'Featured HD List' )
        self.controls['Genre List']['control'].setVisible( key == 'Genre List' )
        self.controls['Genre List']['control'].setEnabled( key == 'Genre List' )
        self.controls['Trailer List']['control'].setVisible( key == 'Trailer List' )
        self.controls['Trailer List']['control'].setEnabled( key == 'Trailer List' )
        # until initial visibilty is solved just hardcode them
        #self.controls['Trailer Thumbnail']['control'].setVisible(xbmc.getCondVisibility( self.controls['Trailer Thumbnail']['visible'] ) )
        #self.controls['Trailer Title']['control'].setVisible(xbmc.getCondVisibility( self.controls['Trailer Title']['visible'] ) )
        #self.controls['Trailer Info']['control'].setVisible(xbmc.getCondVisibility( self.controls['Trailer Info']['visible'] ) )
        self.controls['Trailer Thumbnail']['control'].setVisible( key != 'Genre List' )
        self.controls['Trailer Title']['control'].setVisible( key != 'Genre List' )
        self.controls['Trailer Info']['control'].setVisible( key != 'Genre List' )
        self.controls['Trailer Info']['control'].setEnabled( key != 'Genre List' )
        #if ( key != 'Trailer List' ):
        #    self.setCategoryLabel( key[:-5] )
        #else:
        self.setCategoryLabel( self.genre )    
        self.setFocus(self.controls[key]['control'])
        
    def setGenre( self, genre ):
        self.genre = genre
        self.showTrailers( genre )
        self.showList( '%s List' % (genre,) )
        
    def setGenreLabel( self, genre ):
        self.controls['Genre Label']['control'].setLabel( '<%s>' % (genre,) )
        
    def setCategoryLabel( self, category ):
        self.controls['Category Label']['control'].setLabel( category )
            
    def setListNavigation( self, button ):
        self.controls['Exclusives List']['control'].controlLeft( self.controls[button]['control'] )
        self.controls['Trailer Info']['control'].controlRight( self.controls[button]['control'] )
        
    def getTrailerInfo( self, choice ):
        #genre = self.controls['Category Label']['control'].getLabel()
        title = choice.getLabel()
        self.showTrailerInfo( title )
    
    def getTrailer( self, choice ):
        title = choice.getLabel()
        self.showVideo( title )
        
    def getTrailerGenre( self, choice ):
        self.genre = choice.getLabel()
        self.showTrailers( self.genre )
        self.setGenreLabel( self.genre )
        self.setCategoryLabel( self.genre )
        self.showList( 'Trailer List' )
    
    def onControl( self, control ):
        try:
            if ( control is self.controls['Newest Button']['control'] ):
                self.setGenre( 'Newest' )
            elif ( control is self.controls['Exclusives Button']['control'] ):
                self.setGenre( 'Exclusives' )
            # elif ( control == self.controls['Featured HD Button']['control'] ):
                # self.showList( 'Featured HD List' )
            elif ( control is self.controls['Genre Button']['control'] ):
                self.setGenre( 'Genre' )
            elif ( control is self.controls['Genre List']['control'] ):
                self.getTrailerGenre( control.getSelectedItem() )
            elif ( control is self.controls['Exclusives List']['control'] or\
                control is self.controls['Newest List']['control'] or\
                control is self.controls['Trailer List']['control'] ):
                self.getTrailer( control.getSelectedItem() )
        except: print 'ERROR: in onControl'
            
    def onAction( self, action ):
        try:
            buttonDesc = self.controllerAction.get(action.getButtonCode(), 'n/a')
            if ( buttonDesc == 'Back Button' or buttonDesc == 'Remote Menu Button' ): self.exitScript()
            elif (buttonDesc == 'B Button' or buttonDesc == 'Remote Back Button' ):
                if ( self.genre != 'Newest' and self.genre != 'Exclusives' and self.genre != 'Genre'):
                    self.setGenre( 'Genre' )
            else:
                control = self.getFocus()
                if ( 
                        control is self.controls['Exclusives List']['control'] or
                        control is self.controls['Newest List']['control'] or
                        control is self.controls['Trailer List']['control']
                    ):
                    self.getTrailerInfo( control.getSelectedItem() )
                elif ( control is self.controls['Exclusives Button']['control'] ):
                    self.setListNavigation('Exclusives Button')
                elif ( control is self.controls['Newest Button']['control'] ):
                    self.setListNavigation('Newest Button')
                elif ( control is self.controls['Genre Button']['control'] ):
                    self.setListNavigation('Genre Button')
                elif ( control is self.controls['Settings Button']['control'] ):
                    self.setListNavigation('Settings Button')
        except: print 'ERROR: in onAction'
