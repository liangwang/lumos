import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate as itpl

volts=np.arange(0.2,1.1,0.1) #from 0.2 to 1
freqs=np.array([0.00017,0.00241,0.02977,0.25342,0.99234,2.01202,2.91069,3.60153,4.2])
model=itpl.InterpolatedUnivariateSpline(volts,freqs,k=2)
vnew = np.arange(0.2, 1.01, 0.01)
fnew = model(vnew)
fnew = fnew / 4.2

dp0=np.ones_like(vnew)*6.14 # base dynamic power
dp = dp0*vnew**2*fnew

sp0=np.ones_like(vnew)*1.06 # base static power
# @TODO
sp=sp0*vnew*10**(vnew/0.8)/10**(1/0.8)

power=dp+sp

fig=plt.figure()
axes = fig.add_subplot(111)
axes.set_xlabel('Supply Voltage(V)')
axes.set_ylabel('Power (W)')

axes.plot(vnew,dp,vnew,sp,vnew,power)

axes.set_xlim(0,1.1)
axes.set_yscale('log')
axes.legend(axes.lines, ['Dynamic Power','Static Power','Overall'], 'upper left', prop=dict(size='medium'))

fig.savefig('dyn_st_power.png')
