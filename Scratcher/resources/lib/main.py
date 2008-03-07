# official python modules
import os
# official xbmc modules
import xbmcgui
# script modules
import common

class ScriptWindow( common.gui.BaseScriptWindow ):
    def __init__( self, xmlFile, resourcePath ):
        self.file = None
        self.changed_lines = {
            # line_num: new_text,
        }
        self.controls_map = {
            1: { # LABEL: script name
                'label': common.scriptname,
            },
            50: { # LIST: text area
                'onClick': self.change_line,
            },
            101: { # BUTTON: open
                'onClick': self.open_new_file,
            },
            102: { # BUTTON: save
                'onClick': None,
            },
        }
        common.gui.BaseScriptWindow.__init__( self, xmlFile, resourcePath )

    def change_line( self ):
        try:
            # find the current id and ListItem object
            id = self.getCurrentListPosition()
            item = self.getListItem( id )
            try:
                # get text from the ListItem
                original_text = item.getLabel()
            except:
                # text missing, default to empty string
                original_text = str()
            # show keyboard for user to change the text
            new_text = common.gui.dialog.keyboard( original_text, 'Edit this text:' )
            if new_text is not original_text:
                try:
                    item.setLabel( new_text )
                    self.changed_lines[id] = new_text
                except:
                    print 'unable to set the new text'
        except:
            print 'error changing the line of text'

    def close( self ):
        # close the file
        self.file.close()
        # close the window
        common.gui.BaseScriptWindow.close( self )

    def open_new_file( self ):
        # get a path to the file 
        filepath = common.gui.dialog.browse( heading = common.localize( 1001 ) )
        if len( filepath ):
            # open the file in read only mode
            # TODO: check for write access here?
            self.file = open( filepath, 'r' )
            # ensure that the changed_lines dictionary is blank
            # TODO: if not blank already, ask to save changes to last file
            self.changed_lines = dict()
            # clear the list before adding new items
            self.clearList()
            # function to beautify each line of text for display
            def line_cleanup( line ):
                end_of_line_chars = [ '\r', '\n' ]
                for char in end_of_line_chars: line = line.replace( char, '' )
                return line
            # add a new item to the list for each line of text in the file
            line_number = 0
            for line in self.file:
                line = line_cleanup( line )
                line_number = line_number + 1
                item = xbmcgui.ListItem( line, str( line_number ) )
                self.addItem( item )

# construct the xml filename
xmlFile = 'script-%s-window.xml' % common.scriptname.replace( ' ', '_' )
# init the window instance
window = ScriptWindow( xmlFile, common.resource_path )
# browse for a file to open
window.open_new_file()
# turn over control to the window
window.doModal()