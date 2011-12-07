import Plot
from Plot import *
from data import reader

import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline

from model.Tech import PTM

import matplotlib.pyplot as plt

def normalize(data, vdd_nom):
    if vdd_nom in data['vdd']:
        # not need to curve-fitting
        vddList = data['vdd'].tolist()
        idx_nom = vddList.index(vdd_nom)

        freq_nom = data['freq'][idx_nom]
        dp_nom = data['dp'][idx_nom]
        sp_nom = data['sp'][idx_nom]


    else:
        # curve-fitting to get nominal values
        model = IUSpline(data['vdd'], data['freq'], k=3)
        freq_nom = model(vdd_nom)
        model = IUSpline(data['vdd'], data['dp'], k=3)
        dp_nom = model(vdd_nom)
        model = IUSpline(data['vdd'], data['sp'], k=3)
        sp_nom = model(vdd_nom)

    return {'vdd' : data['vdd'],
            'freq': data['freq']/freq_nom,
            'dp'  : data['dp']/dp_nom,
            'sp'  : data['sp']/sp_nom
           }

def plot(cktList, ttypeList, techList, normalize=False):
    num_of_ckts = len(cktList)
    num_of_techs = len(techList)

    for ttype in ttypeList:
        fig = plt.figure(figsize=(24,6*num_of_techs))
        fig.suptitle('Technology Type: %s' % (ttype,))
        plot_idx = 0

        for tech in techList:
            plot_idx = plot_idx + 1
            axes_freq = fig.add_subplot(num_of_techs, 3, plot_idx)

            plot_idx = plot_idx + 1
            axes_dp = fig.add_subplot(num_of_techs, 3, plot_idx)

            plot_idx = plot_idx + 1
            axes_sp = fig.add_subplot(num_of_techs, 3, plot_idx)

            for ckt in cktList:
                data = reader.readNormData(ckt, ttype, tech)
                if normalize:
                    d_norm = normalize(data, PTM.vdd[ttype][tech])
                else:
                    d_norm = data

                axes_freq.plot(d_norm['vdd'], d_norm['freq'])
                axes_dp.plot(d_norm['vdd'], d_norm['dp'])
                axes_sp.plot(d_norm['vdd'], d_norm['sp'])

            axes_freq.set_yscale('log')
            axes_freq.grid(True)
            axes_freq.legend(axes_freq.lines, cktList, loc='upper left')
            axes_dp.set_yscale('log')
            axes_dp.grid(True)
            axes_dp.legend(axes_dp.lines, cktList, loc='upper left')
            axes_sp.set_yscale('log')
            axes_sp.grid(True)
            axes_sp.legend(axes_sp.lines, cktList, loc='upper left')

        if normalize:
            fig.savefig('norm_%s.png' % ttype)
        else:
            fig.savefig('nonorm_%s.png' % ttype)

if __name__ == '__main__':
    plot(('inv','adder','adder16','adder8'),
         ('HKMGS', 'LP'),
         (45, 32, 22, 16))

    

