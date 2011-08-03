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

class PlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent, -1)
        self.fig = Figure((5,4), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        self.SetSizerAndFit(sizer)

    def init_plot_data(self):
        a = self.fig.add_subplot(111)
        self.x=np.arange(120.0)*2*np.pi/60.0
        self.y=np.sin(self.x)
        self.lines=a.plot(self.x,self.y,'ko')
    
    def draw_plot(self):
        #TODO: remove this class, instantiate matplotpanel directly in main frame        
        pass

class simpleapp_wx(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.parent = parent
        self.initialize()
        
    def initialize(self):
        sizer = wx.GridBagSizer()
        
        self.entry = wx.TextCtrl(self, -1, value=u"Enter text here.")
        sizer.Add(self.entry, (0,0),(1,1),wx.EXPAND)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnPressEnter, self.entry)
        
        button = wx.Button(self, -1, label="Click me!")
        sizer.Add(button, (0,1))
        self.Bind(wx.EVT_BUTTON, self.OnButtonClick, button)
        
        #self.label = wx.StaticText(self, -1, label=u'Hello!')
        #self.label.SetBackgroundColour(wx.BLUE)
        #self.label.SetForegroundColour(wx.WHITE)
        #sizer.Add(self.label, (1,0),(1,2),wx.EXPAND)
        self.plotpanel = PlotPanel(self)
        self.plotpanel.init_plot_data()
        sizer.Add(self.plotpanel, (1,0),(1,2),wx.EXPAND)
        
        sizer.AddGrowableCol(0)
        self.SetSizerAndFit(sizer)
        self.SetSizeHints(-1,self.GetSize().y,-1,self.GetSize().y)
        self.entry.SetFocus()
        self.entry.SetSelection(-1,-1)
        self.Show(True)
        
    def OnButtonClick(self, event):
        #self.label.SetLabel(self.entry.GetValue() + " (You clicked the button)")
        self.entry.SetFocus()
        self.entry.SetSelection(-1,-1)
        
    def OnPressEnter(self,event):
        #self.label.SetLabel(self.entry.GetValue() + "(You pressed enter)")
        self.entry.SetFocus()
        self.entry.SetSelection(-1,-1)
        
if __name__ == "__main__":
    app = wx.App()
    frame = simpleapp_wx(None, -1, 'my application')
    app.MainLoop()
