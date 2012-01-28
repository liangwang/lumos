import numpy as np
import matplotlib.pyplot as plt
from os.path import join as joinpath
from optparse import OptionParser
import os
from model.core import Core
from data import reader
import analysis
FIG_DIR=joinpath(analysis.FIG_DIR, 'errbar')

try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise

def plotWithErrbar(cktList, ttypeList, techList):
    num_of_techs = len(techList)
    colorList = ('blue', 'magenta', 'red', 'green')
    for ckt in cktList:
        for ttype in ttypeList:
            plot_idx = 0
            fig = plt.figure(figsize=(16,6*num_of_techs))
            fig.suptitle('Technology Type: %s, Corner Case: %s' % (ttype, 'TT'))
            for (tech,color) in zip(techList, colorList):
                data_norm = reader.readNormData(ckt, ttype, tech)
                data_mc = reader.readMCData(ckt, ttype, tech)
                plot_idx = plot_idx + 1
                axes_freq = fig.add_subplot(num_of_techs,2,plot_idx)
                
                yerr_max = data_mc['freq_max']-data_norm['freq']
                yerr_min = data_norm['freq'] - data_mc['freq_min']
                axes_freq.errorbar(data_norm['vdd'], data_norm['freq'], yerr=[yerr_min, yerr_max]) 
                axes_freq.set_yscale('log')
                axes_freq.set_title('Frequency Scaling, %snm' % (tech,))
                axes_freq.set_xlabel('Supply Voltage (V)')
                axes_freq.set_ylabel('Frequency (GHz)')
                axes_freq.set_xlim(0.2, 1.2)
                axes_freq.grid(True)
                
                plot_idx = plot_idx + 1
                axes_power = fig.add_subplot(num_of_techs,2,plot_idx)

                yerr_max = data_mc['dp_max']-data_norm['dp']
                yerr_min = data_norm['dp'] - data_mc['dp_min']
                axes_power.errorbar(data_norm['vdd'], data_norm['dp'], yerr=[yerr_min, yerr_max]) 
                yerr_max = data_mc['sp_max']-data_norm['sp']
                yerr_min = data_norm['sp'] - data_mc['sp_min']
                axes_power.errorbar(data_norm['vdd'], data_norm['sp'], yerr=[yerr_min, yerr_max]) 
                axes_power.set_yscale('log')
                axes_power.set_title('Power Scaling, %snm' % (tech,))
                axes_power.set_xlabel('Supply Voltage (V)')
                axes_power.set_ylabel('Power (W)')
                axes_power.set_xlim(0.2, 1.2)
                axes_power.grid(True)

            ofn = 'errbar_%s_%s.%s' % (ckt, ttype, suffix)
            ofile = joinpath(FIG_DIR, ofn)
            fig.savefig(ofile)



if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--plot-fmt', default='view')
    parser.add_option('--plot-errbar', action='store_true', default=True)
    (options,args) = parser.parse_args()

    if options.plot_fmt == 'view':
        suffix = 'png'
    elif options.plot_fmt == 'pub':
        suffix = 'pdf'
    else:
        print 'Unsupported plot format %s' % options.plot_fmt

    if options.plot_errbar:
        cktList = ('adder',)
        ttypeList = ('HKMGS', 'LP')
        techList = (45,32,22,16)
        plotWithErrbar(cktList, ttypeList, techList)
