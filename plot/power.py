import numpy as np
import matplotlib.pyplot as plt

from model.Freq import FreqScale
from plot.Plot import Matplot

from os.path import join as joinpath

class PowerPlot(Matplot):
    ''' This class plot dynamic and static power scaled to voltage. '''
    def __init__(self):
        Matplot.__init__(self)
        
        self.prefix = 'power'
        self.format='png'
        
    def do_plot(self):
        scaler = FreqScale(0.45,1.0,4.2)

        volts=np.linspace(0.2,1,81) #from 0.2 to 1
        freqs=scaler.get_freqs_in_mhz(volts)
        freqs = freqs / 4200

        dp0=np.ones_like(volts)*6.14 # base dynamic power
        dp = dp0*volts**2*freqs

        sp0=np.ones_like(volts)*1.06 # base static power
        # @FIXME: make sure the formula is right
        sp=sp0*volts*10**(volts/2.5)/10**(1/2.5)

        power=dp+sp
        
        fig=plt.figure(figsize=(6,8))
        axes = fig.add_subplot(111)
        axes.set_xlabel('Supply Voltage(V)')
        axes.set_ylabel('Power (W)')
        
        axes.plot(volts,dp,volts,sp,volts,power)
        
        axes.set_xlim(0,1.1)
        axes.set_yscale('log')
        axes.legend(axes.lines, ['Dynamic Power','Static Power','Overall'], 'upper left', prop=dict(size='medium'))
        axes.grid(True)
        
        fname = '.'.join([self.prefix,self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

if __name__=='__main__':
    p = PowerPlot()
    p.do_plot()