import xbmc
import xbmcgui
import os

class GUI(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self.defineControls()
        
    def onClick(self, controlId):
        pass

    def onAction(self, action):
        if action in self.action_cancel_dialog:
            self.closeDialog()

    def closeDialog(self):
        self.close()

    def onFocus(self, controlId):
        pass

    def defineControls(self):
        self.action_cancel_dialog = (9, 10)
        self.control_heading_label_id       = 2
        self.control_list_label_id          = 3
        self.control_list_id                = 10
        self.control_modifySet_button_id    = 11
        self.control_add_button_id          = 13
        self.control_remove_button_id       = 14
        self.control_ok_button_id           = 18
        self.control_cancel_button_id       = 19
        self.heading_label      = self.getControl(self.control_heading_label_id)
        self.list_label         = self.getControl(self.control_list_label_id)
        self.list               = self.getControl(self.control_list_id)
        self.add_button         = self.getControl(self.control_add_button_id)
        self.remove_button      = self.getControl(self.control_remove_button_id)
        self.modifySet_button   = self.getControl(self.control_modifySet_button_id)
        self.ok_button          = self.getControl(self.control_ok_button_id)
        self.cancel_button      = self.getControl(self.control_cancel_button_id)
