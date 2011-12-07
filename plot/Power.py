import numpy as np
import matplotlib.pyplot as plt

from model.Freq import FreqScale,FreqScale2
from model.Tech import Base as techbase, Scale as techscl
from plot.Plot import Matplot

from os.path import join as joinpath

class PowerPlot(Matplot):
    ''' This class plot dynamic and static power scaled to voltage. '''
    def __init__(self):
        Matplot.__init__(self)
        
        self.prefix = 'power'
        self.format='png'
        
    def do_plot(self):
        scaler = FreqScale(0.5,1.0,4.2)

        volts=np.linspace(0.2,1,100) #from 0.2 to 1
        freqs = scaler.get_freqs(volts)

        dp0=np.ones_like(volts)*6.14 # base dynamic power
        dp = dp0*volts**2*freqs/4.2

        sp0=np.ones_like(volts)*1.06 # base static power
        # @FIXME: make sure the formula is right
        slope = scaler.sp_slope
        sp=sp0*10**(volts*slope)/10**(1*slope)

        power=dp+sp
        
        fig=plt.figure(figsize=(8,6))
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

    def do_plot2(self, ckt, ttype, tech, mech):
        v0 = techbase.vdd * techscl.vdd[mech][tech]
        f0 = techbase.freq['IO']*techscl.freq[mech][tech]

        scaler = FreqScale2(ckt, ttype, tech, v0, f0)

        volts = np.linspace(0.3, 1.1, 50)
        freqs = scaler.get_freqs(volts)

        _dp0 = techbase.dp['IO'] * techscl.power[mech][tech]
        dp0 = np.ones_like(volts)*_dp0
        dp = dp0*volts**2*freqs/f0

        _sp0 = techbase.sp['IO'] * techscl.freq[mech][tech]
        sp0 = np.ones_like(volts)*_sp0
        sp = sp0*10**(volts*slope)/10**(v0*slope)

        power=dp+sp
if __name__=='__main__':
    p = PowerPlot()
    p.do_plot()
