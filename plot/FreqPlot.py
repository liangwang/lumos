from data import reader
import matplotlib.pyplot as plt

def plot(suffix):
    techList = (45, 32, 22, 16)
    cktList = ('inv', 'adder')
    ttypeList = ('HKMGS', 'LP')
    colorList = ('blue', 'magenta', 'red', 'green')

    for ckt in cktList:
        fig = plt.figure(figsize=(16,12))
        fig.suptitle('Frequency Scaling, Circuit: %s' % ckt)
        plot_idx = 1
        for tech in techList:
            axes = fig.add_subplot(2,2,plot_idx)
            for ttype in ttypeList:
                data_norm = reader.readNormData(ckt, ttype, tech)
                axes.plot(data_norm['vdd'], data_norm['freq'])

            axes.set_yscale('log')
            axes.set_title('%dnm' % tech)
            axes.set_xlabel('Supply Voltage (V)')
            axes.set_ylabel('Frequency (Hz)')
            axes.set_xlim(0.2, 1.2)
            axes.grid(True)
            axes.legend(axes.lines, ttypeList, loc='upper left')

            plot_idx = plot_idx + 1

        fig.savefig('freq_nom_%s.%s' % (ckt,suffix))

def plotSep(suffix):
    techList = (45, 32, 22, 16)
    cktList = ('inv', 'adder')
    ttypeList = ('HKMGS', 'LP')
    colorList = ('blue', 'red')

    for ckt in cktList:
        for tech in techList:
            fig = plt.figure(figsize=(6, 4.5))
            axes = fig.add_subplot(111)
            for ttype,color in zip(ttypeList,colorList):
                data_norm = reader.readNormData(ckt, ttype, tech)
                axes.plot(data_norm['vdd'], data_norm['freq'], color=color)

            axes.set_yscale('log')
            #axes.set_title('%dnm' % tech)
            axes.set_xlabel('Supply Voltage (V)')
            axes.set_ylabel('Frequency (Hz)')
            axes.set_xlim(0.2, 1.2)
            axes.grid(True)
            axes.legend(axes.lines, ttypeList, loc='lower right')

            fig.savefig('freq_nom_%s_%dnm.%s' % (ckt,tech, suffix))

def plotErrorbar(suffix):
    techList = (45, 32, 22, 16)
    cktList = ('inv', 'adder')
    ttypeList = ('HKMGS', 'LP')
    colorList = ('blue', 'magenta', 'red', 'green')

    for ckt in cktList:
        fig = plt.figure(figsize=(16,12))
        fig.suptitle('Frequency Scaling, Circuit: %s' % ckt)
        plot_idx = 1
        for tech in techList:
            axes = fig.add_subplot(2,2,plot_idx)
            ebList = []
            for ttype in ttypeList:
                data_norm = reader.readNormData(ckt, ttype, tech)
                data_mc = reader.readMCData(ckt, ttype, tech)
                yerr_max = data_mc['freq_max']-data_norm['freq']
                yerr_min = data_norm['freq'] - data_mc['freq_min']
                eb,dummy,dummy2 = axes.errorbar(data_norm['vdd'], data_norm['freq'], yerr=[yerr_min, yerr_max])
                ebList.append(eb)

            axes.set_yscale('log')
            axes.set_title('%dnm' % tech)
            axes.set_xlabel('Supply Voltage (V)')
            axes.set_ylabel('Frequency (Hz)')
            axes.set_xlim(0.2, 1.2)
            axes.grid(True)
            axes.legend(ebList, ttypeList, loc='upper left')

            plot_idx = plot_idx + 1

        fig.savefig('freq_errbar_%s.%s' % (ckt,suffix))

def plotErrorbarSep(suffix):
    techList = (45, 32, 22, 16)
    cktList = ('inv', 'adder')
    ttypeList = ('HKMGS', 'LP')
    colorList = ('blue', 'red')

    for ckt in cktList:
        for tech in techList:
            fig = plt.figure(figsize=(6,4.5))
            axes = fig.add_subplot(111)
            ebList = []
            for ttype,color in zip(ttypeList,colorList):
                data_norm = reader.readNormData(ckt, ttype, tech)
                data_mc = reader.readMCData(ckt, ttype, tech)
                yerr_max = data_mc['freq_max']-data_norm['freq']
                yerr_min = data_norm['freq'] - data_mc['freq_min']
                eb,dummy,dummy2 = axes.errorbar(data_norm['vdd'], data_norm['freq'], yerr=[yerr_min, yerr_max])
                ebList.append(eb)

            axes.set_yscale('log')
            #axes.set_title('%dnm' % tech)
            axes.set_xlabel('Supply Voltage (V)')
            axes.set_ylabel('Frequency (Hz)')
            axes.set_xlim(0.2, 1.2)
            axes.grid(True)
            axes.legend(ebList, ttypeList, loc='upper left', fancybox=True, shadow=True)

            fig.savefig('freq_errbar_%s_%dnm.%s' % (ckt,tech, suffix))

#plot()
#plotErrorbar()
#plotSep('pdf')
plotErrorbarSep('pdf')
