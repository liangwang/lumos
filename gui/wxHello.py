# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 23:01:09 2011

@author: -
"""

try:
    import wx
except ImportError:
    raise ImportError, "The wxPython module is required to run this program"

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import numpy as np

class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a 
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)
        
        self.value = initval
        
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.radio_auto = wx.RadioButton(self, -1, 
            label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, -1,
            label="Manual")
        self.manual_text = wx.TextCtrl(self, -1, 
            size=(35,-1),
            value=str(initval),
            style=wx.TE_PROCESS_ENTER)
        
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)
        
        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
        sizer.Add(manual_box, 0, wx.ALL, 10)
        
        self.SetSizerAndFit(sizer)
        
    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())
    
    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()
    
    def is_auto(self):
        return self.radio_auto.GetValue()
        
    def manual_value(self):
        return self.value        


class simpleapp_wx(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.parent = parent
        self.initialize()
        
    def initialize(self):

        sizer_top = wx.BoxSizer(wx.VERTICAL)
        
        # Matplotlib widget
        self.fig = Figure((5,4), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
        self.init_plot_data()
        
        sizer_top.Add(self.canvas, wx.EXPAND)
        
        sizer_ctrl = wx.BoxSizer(wx.HORIZONTAL)
        sizer_top.Add(sizer_ctrl, wx.EXPAND)
        
        # Init control widgets
        self.type_ctrl = BoundControlBox(self, -1, 'Plot type', 20)
        sizer_ctrl.Add(self.type_ctrl, wx.EXPAND)
        

        
        #self.label = wx.StaticText(self, -1, label=u'Hello!')
        #self.label.SetBackgroundColour(wx.BLUE)
        #self.label.SetForegroundColour(wx.WHITE)
        #sizer.Add(self.label, (1,0),(1,2),wx.EXPAND)

#        sizer.Add(self.canvas, (1,0),(1,2),wx.EXPAND)
#        
#        sizer.AddGrowableCol(0)
        self.SetSizerAndFit(sizer_top)
        self.SetSizeHints(-1,self.GetSize().y,-1,self.GetSize().y)
#        self.entry.SetFocus()
#        self.entry.SetSelection(-1,-1)
        self.Show(True)      
        
    def OnButtonClick(self, event):
        #self.label.SetLabel(self.entry.GetValue() + " (You clicked the button)")
        self.entry.SetFocus()
        self.entry.SetSelection(-1,-1)
        
    def OnPressEnter(self,event):
        #self.label.SetLabel(self.entry.GetValue() + "(You pressed enter)")
        self.entry.SetFocus()
        self.entry.SetSelection(-1,-1)
        
    def init_plot_data(self):
        a = self.fig.add_subplot(111)
        self.x=np.arange(120.0)*2*np.pi/60.0
        self.y=np.sin(self.x)
        self.lines=a.plot(self.x,self.y,'ko')
        
if __name__ == "__main__":
    app = wx.App()
    frame = simpleapp_wx(None, -1, 'my application')
    app.MainLoop()
