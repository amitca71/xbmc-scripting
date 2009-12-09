# official python modules
import sys
# official xbmc modules
import xbmcgui
# script modules
import codes

# script variables
common = sys.modules['common']

def __internal_base_onInit__( self ):
    '''
        sets each control to it's corresponding label from strings.xml
    '''
    for id, callbacks in self.parent_class.controls_map.iteritems():
        try:
            # get the control object for this id
            try:
                control = self.getControl( id )
            except TypeError:
                # usually occurs when the control is not supported in the 
                #   current skin
                continue
            try:
                # see if there is a label set in the code
                #   callback is a string or variable (see below) 
                #   for the label
                callback = callbacks['label']
            except: callback = None
            if callback:
                try:
                    # there may be data in strings.xml also, check with
                    #   a strict (error throwing) lookup
                    label = common.localize( id, strict = True )
                except:
                    # nothing in strings.xml
                    label = ''
                try:
                    # try to use the data from strings.xml as a format for
                    #   assigning data from the callback variable
                    label = label % callback
                except:
                    # if that doesn't work, treat callback as a string and
                    #   concatenate to the data from strings.xml
                    label = label + callback
            else:
                # no label information was set in the code, so use the 
                #   strings.xml lookup alone
                label = common.localize( id )
            if hasattr( control, 'setLabel' ):
                # make sure that this control can even accept a label!
                control.setLabel( label )
            # explicitly delete the control object for the next loop pass
            del control
        except:
            # something horrible occurred
            import traceback
            print '-' * 79
            print 'error setting label for', id
            traceback.print_exc()

def __internal_base_onAction__( self, action ):
        for i in [ action.getId(), action.getButtonCode() ]:
            # this would work nicer here in standard python, but xbmc has 
            #   problems with it
            # if i in codes.EXIT_SCRIPT:
            for j in codes.EXIT_SCRIPT:
                if i == j:
                    if hasattr( self.parent_class, 'close' ):
                        self.parent_class.close()
                    else:
                        self.close()
                    break

def __internal_base_onClick__( self, controlID ):
    for id, callbacks in self.parent_class.controls_map.iteritems():
        if controlID == id:
            try:
                callback = callbacks['onClick']
            except: callback = None
            if callback: callback()

def __internal_base_onFocus__( self, controlID ):
    for id, callbacks in self.parent_class.controls_map.iteritems():
        if controlID == id:
            try:
                callback = callbacks['onFocus']
            except: callback = None
            if callback: callback()

class __internal_base_classWindow__( xbmcgui.WindowXML ):
    '''
        Base class for a BaseScriptWindow window. Do not call this directly.
    '''
    def __init__( self, xmlFile, resourcePath, defaultName = 'Default', forceFallback = False, parentClass = None ):
        if not parentClass:
            raise AttributeError, 'Must specify a parent class.'
        self.parent_class = parentClass
        # call the super class __init__
        xbmcgui.WindowXML.__init__( self, xmlFile, resourcePath, defaultName, forceFallback )
    def onInit( self ):
        return __internal_base_onInit__( self )
    def onAction( self, action ):
        return __internal_base_onAction__( self, action )
    def onClick( self, controlID ):
        return __internal_base_onClick__( self, controlID )
    def onFocus( self, controlID ):
        return __internal_base_onFocus__( self, controlID )

class __internal_base_classDialog__( xbmcgui.WindowXMLDialog ):
    '''
        Base class for a BaseScriptDialog window. Do not call this directly.
    '''
    def __init__( self, xmlFile, resourcePath, defaultName = 'Default', forceFallback = False, parentClass = None ):
        if not parentClass:
            raise AttributeError, 'Must specify a parent class.'
        self.parent_class = parentClass
        # call the super class __init__
        xbmcgui.WindowXMLDialog.__init__( self, xmlFile, resourcePath, defaultName, forceFallback )
    def onInit( self ):
        return __internal_base_onInit__( self )
    def onAction( self, action ):
        return __internal_base_onAction__( self, action )
    def onClick( self, controlID ):
        return __internal_base_onClick__( self, controlID )
    def onFocus( self, controlID ):
        return __internal_base_onFocus__( self, controlID )

class __internal_base_classPopupMenu__( xbmcgui.WindowXMLDialog ):
    '''
        Base class for a dialogs.popupmenu window. Do not call this directly.
    '''
    def __init__( self, xmlFile, resourcePath, defaultName = 'Default', forceFallback = False, parentClass = None ):
        if not parentClass:
            raise AttributeError, 'Must specify a parent class.'
        self.parent_class = parentClass
        # call the super class __init__
        xbmcgui.WindowXMLDialog.__init__( self, xmlFile, resourcePath, defaultName, forceFallback )
    def onInit( self ):
        '''
            adds menu items to the window list according to values provided
        '''
        # set the coordinate resolution for all positioning commands below
        self.setCoordinateResolution( 6 )
        # get the controls from the skin xml
        background = self.getControl(999)
        background_top = self.getControl(997)
        background_bottom = self.getControl(998)
        popuplist = self.getControl(1000)
        # determine center screen coords; resolution 6 is 720x576
        center_screen_x = 720 / 2
        center_screen_y = 576 / 2
        # add the menu items
        for id, callbacks in self.parent_class.controls_map.iteritems():
            try:
                try: # get the label, or blank string
                    label = callbacks['label']
                    if not label: raise
                except: label = str()
                try: # get label2, or blank string
                    label2 = callbacks['label2']
                    if not label2: raise
                except: label2 = str()
                try: # get icon image, or blank string
                    icon = callbacks['icon']
                    if not icon: raise
                except: icon = str()
                try: # get thumbnail image, or blank string
                    thumb = callbacks['thumb']
                    if not thumb: raise
                except: thumb = str()
                # create the ListItem
                item = xbmcgui.ListItem( label, label2, icon, thumb )
                # add it to the window list
                self.addItem( item )
                # add it to the special ControlList
                popuplist.addItem( item )
            except:
                # something horrible occurred
                import traceback
                print '-' * 79
                print 'error setting label for', id
                traceback.print_exc()
        # determine height in screen pixels of list
        # height of each item multiplied by number of items
        list_height = popuplist.getHeight() * self.getListSize()
        # figure out where the list position should be
        list_position = (
            # x pos is center screen minus half the width of the background 
            #   image
            center_screen_x - ( background.getWidth() / 2 ),
            # y pos is center screen minus half the height of the list
            center_screen_y - ( list_height / 2 )
        )
        # add any xml positioning values to the list position, allowing 
        #   controls to be offset
        # background top
        temp_position = (
            list_position[0] + background_top.getPosition()[0],
            list_position[1] + background_top.getPosition()[1],
        )
        background_top.setPosition( int( temp_position[0] ), int( temp_position[1] ) )
        # background
        temp_position = (
            list_position[0] + background.getPosition()[0],
            list_position[1] + background.getPosition()[1],
        )
        background.setPosition( int( temp_position[0] ), int( temp_position[1] ) )
        background.setHeight( list_height )
        # popuplist
        temp_position = (
            list_position[0] + popuplist.getPosition()[0],
            list_position[1] + popuplist.getPosition()[1],
        )
        popuplist.setPosition( int( temp_position[0] ), int( temp_position[1] ) )
        popuplist.setHeight( list_height )
        # background bottom
        temp_position = (
            list_position[0] + background_bottom.getPosition()[0],
            list_position[1] + background_bottom.getPosition()[1] + list_height,
        )
        background_bottom.setPosition( int( temp_position[0] ), int( temp_position[1] ) )
    def onAction( self, action ):
        return __internal_base_onAction__( self, action )
    def onClick( self, controlID ):
        # we need to get the current list position instead of using the 
        #   controlID passed to us
        controlID = self.getControl(1000).getSelectedPosition() + 1 # zero-based
        # close the window before returning
        self.close()
        return __internal_base_onClick__( self, controlID )
    def onFocus( self, controlID ):
        # we need to get the current list position instead of using the 
        #   controlID passed to us
        controlID = self.getControl(1000).getSelectedPosition() + 1 # zero-based
        return __internal_base_onFocus__( self, controlID )
