'''
Created on Aug 11, 2011

@author: liang
'''
from Plot import Matplot
from model.Application import Application as App
import Plot
from model.System import System,SymSys
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from os.path import join as joinpath
import math

class PerfScalePlot(Matplot):
    '''
    Performance scaling to voltage
    '''


    def __init__(self, area, power, 
                 tech=45, mech='ITRS', ctype='IO', prefix='power', appf=0.99, appm=2):
        '''
            Constructor
        '''
        Matplot.__init__(self)


        self.format = 'pdf'
        
        self.power = power
        self.area = area
        self.tech = tech
        self.mech = mech
        self.ctype = ctype

        self.appf = appf
        self.appm = appm

        self.prefix = prefix
        
        self.sys = System(area=area, power=power,
                         ctype=ctype, mech=mech, tech=tech)

    def plot_multiple_area_with_utilization(self, area_list):
        v = [(0.05*i) for i in range(4,21)]
        #v = [(0.1*i) for i in range(2,11)]

        markers = ['o', '^', 's', '*', 'h', '+', 'x', 'D', 'p']
        
        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title('Speedup with VFS, TDP=%dW' % self.power)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(power=self.power)
        i = 0
        for area in area_list:
            self.sys.set_sys_prop(area=area)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.get_speedup(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        s_legend_labels = [ (r'Area=%d$mm^2$' % area) for area in area_list]
        #u_legend_labels = [ ('Utilization, area=%d' % area) for area in area_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc="center left")
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0, 1.1)

        nametag =  "%dnm_%s_%s_f%.2f" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s_%dw' % (self.prefix, nametag, self.power)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

    def plot_multiple_power_with_utilization(self, power_list):
        v = [(0.05*i) for i in range(4,21)]
        #v = [(0.1*i) for i in range(2,11)]

        markers = ['o', '^', 's', 'p', '*', 'h', '+', 'x', 'D']
        
        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title(r'Speedup with VFS, Area=%d$mm^2$' % self.area)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(area=self.area)
        i = 0
        for power in power_list:
            self.sys.set_sys_prop(power=power)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.get_speedup(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        s_legend_labels = [ (r'Power=%d$W$' % power) for power in power_list]
        #u_legend_labels = [ ('Utilization, power=%d' % power) for power in power_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc="center left")
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0, 1.1)

        nametag =  "%dnm_%s_%s_f%.2f" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s_%dmm' % (self.prefix, nametag, self.area)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

    def _area_bound(self, power):
        sys = self.sys

        sys.set_sys_prop(power=power)
        sys.set_core_prop(tech=self.tech, mech=self.mech, ctype=self.ctype)
        area_threshold = sys.core.area

        area_l = float(100) #left bound
        area_r = float(5000) # right bound

        # make sure the right bound is big enough
        sys.set_sys_prop(area=area_r)
        sys.probe2()
        while (math.fabs(sys.util-1) < 0.1):
            #print "area_r %d is not bigger enough, double" % area_r
            area_r = area_r * 2
            sys.set_sys_prop(area=area_r)
            sys.probe2()
        #print "area_r ends up with %d" % area_r

        while (area_r-area_l) > area_threshold:
            area_p = (area_l+area_r)/2

            sys.set_sys_prop(area=area_p)
            sys.probe2(app=App(f=self.appf))

            #print 'area_p: %f, area_r: %f, area_l: %f, util: %f' % (area_p,area_r, area_l, sys.util)
            if (math.fabs(sys.util-1) < 0.01):
                area_l = area_p
            else:
                area_r = area_p

        area = (area_r+area_l)/2
        sys.set_sys_prop(area=area)
        return (area, sys.volt, sys.speedup)

    def plot_area_bound(self, pmin=60, pmax=205, step=5, amin=100, amax=7000):

        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()

        ax3.spines["right"].set_position(("axes", 1.2))
        Plot.make_patch_spines_invisible(ax3)
        Plot.make_spine_invisible(ax3, "right")

        plt.subplots_adjust(right=0.75)

        ax1.set_title('Dark vs. Dim (%dnm)' % (self.tech,))
        ax1.set_ylabel(r'Area ($mm^2$)')
        ax2.set_ylabel('Supply voltage when system achieves the best speedup (V)')
        ax3.set_ylabel('Speedup over single baseline IO core')
        ax1.set_xlabel('Power (W)')

        plist = [(power) for power in xrange(pmin, pmax, step)]
        alist = []
        vlist = []
        slist = []

        for power in plist:
            #print "power=%d" % power
            area, vdd, speedup = self._area_bound(power)
            alist.append(area)
            vlist.append(vdd)
            slist.append(speedup)

        #print vlist

        Path = mpath.Path
        dark_pathdata = [
            (Path.MOVETO, (plist[0],amax)),
            (Path.LINETO, (plist[0],alist[0])),
            (Path.LINETO, (plist[-1],alist[-1])),
            (Path.LINETO, (plist[-1],amax)),
            (Path.CLOSEPOLY, (plist[0],amax)),
        ]
    
        dim_pathdata = [
            (Path.MOVETO, (plist[0],amin)),
            (Path.LINETO, (plist[0],alist[0])),
            (Path.LINETO, (plist[-1],alist[-1])),
            (Path.LINETO, (plist[-1],amin)),
            (Path.CLOSEPOLY, (plist[0],amin)),
        ]


        la, = ax1.plot(plist, alist, 'b-', linewidth=1)
        lv, = ax2.plot(plist, vlist, 'r--', linewidth=3)
        ls, = ax3.plot(plist, slist, 'm-.', linewidth=3)

        #ax1.legend([la,lv,ls], ['Area','Vdd','Speedup'], loc='upper left')
        ax1.grid(True)
        ax1.set_ylim(amin, amax)
        ax2.set_ylim(0, 1)

        codes, verts = zip(*dim_pathdata)
        dim_path = mpath.Path(verts, codes)
        dim_patch = mpatches.PathPatch(dim_path, facecolor='black', alpha=0.2)
        ax1.add_patch(dim_patch)
        index = plist.index(130)
        acord = alist[index]/2
        ax1.text(130,acord,'Dim silicon region')

        codes, verts = zip(*dark_pathdata)
        dark_path = mpath.Path(verts, codes)
        dark_patch = mpatches.PathPatch(dark_path, facecolor='black', alpha=0.5)
        ax1.add_patch(dark_patch)
        index = plist.index(80)
        acord = (alist[index]+7000)/2
        ax1.text(80,acord,'Dark silicon region')

        ax1.yaxis.label.set_color(la.get_color())
        ax2.yaxis.label.set_color(lv.get_color())
        ax3.yaxis.label.set_color(ls.get_color())

        ax1.tick_params(axis='y', colors=la.get_color())
        ax2.tick_params(axis='y', colors=lv.get_color())
        ax3.tick_params(axis='y', colors=ls.get_color())

        bbox_props = dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9)
        t = ax1.text(120,3000, "Speedup", ha="center", va="center", size="medium", rotation=35, color=ls.get_color(), bbox=bbox_props)
        t = ax2.text(170, 0.53, "Voltage", ha="center", va="center", size="medium", color=lv.get_color(), bbox=bbox_props)


        nametag =  "%dnm_%s_%s_f%.2f" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s' % (self.prefix, nametag)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)





    def do_plot(self):
        v = [(0.05*i) for i in range(4,21)]
        
        self.sys.build(area=self.area,power=self.power)
        s, = self.sys.get_speedup(v)
        
        
        fig = plt.figure(figsize=(9.5,6.9))
        fig.suptitle('%dmm, %dw' % (self.area,self.power))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title('Speedup with VFS, TDP=%dW' % self.power)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')

        ax1.plot(v,s)
#        ax1.set_ylim(0,55)
        
        figname = '%dw_%s_%dmm' % (self.power, self.prefix, self.area)
        fname = '.'.join([figname,self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)
                            
            

class PerfScalePlot2(Matplot):
    '''
    Performance scaling to voltage
    '''


    def __init__(self, area, power, 
                 tech=45, mech='HKMGS', ctype='IO', prefix='power2', appf=0.99, appm=2):
        '''
            Constructor
        '''
        Matplot.__init__(self)


        self.format = 'pdf'
        
        self.power = power
        self.area = area
        self.tech = tech
        self.mech = mech
        self.ctype = ctype

        self.appf = appf
        self.appm = appm

        self.prefix = prefix
        
        self.sys = SymSys()
        self.sys.set_sys_prop(area=area, power=power)
        self.sys.set_core_prop(ctype=ctype, mech=mech, tech=tech)

    def plot_speedup_util_with_area_series(self):
        '''
        Specific for ECE6332 presentation plot
        '''
        v = [(0.05*i) for i in range(6,23)]
        #v = [(0.1*i) for i in range(2,11)]

        area_list = (200, 400, 800, 1600, 3200, 6400)
        markers = ['o', '^', 's', '*', 'h', '+', 'x', 'D', 'p']
        
        fig = plt.figure(figsize=(11.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(power=100)
        i = 0
        for area in area_list:
            self.sys.set_sys_prop(area=area)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.speedup_by_vlist(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0, box.width*0.85, box.height])
        ax2.set_position([box.x0, box.y0, box.width*0.85, box.height])
        s_legend_labels = [ (r'%d$mm^2$' % area) for area in area_list]
        #u_legend_labels = [ ('Utilization, area=%d' % area) for area in area_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc=(1.10, 0), ncol=1, 
                              fancybox=True, shadow =True)
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax1.set_ylim(0, 40)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0.2, 1.2)

        nametag =  "%dnm_%s_%s_f%g" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s_%dw' % (self.prefix, nametag, self.power)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

    def ece6332_report_multiarea(self):
        '''
        Specific for ECE6332 report plot
        '''
        v = [(0.05*i) for i in range(6,23)]
        #v = [(0.1*i) for i in range(2,11)]

        area_list = (200, 400, 800, 1600, 3200, 6400)
        markers = ['o', '^', 's', '*', 'h', '+', 'x', 'D', 'p']
        
        fig = plt.figure(figsize=(11.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(power=100)
        i = 0
        for area in area_list:
            self.sys.set_sys_prop(area=area)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.speedup_by_vlist(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        #box = ax1.get_position()
        #ax1.set_position([box.x0, box.y0, box.width, box.height*0.95])
        #ax2.set_position([box.x0, box.y0, box.width, box.height*0.95])
        s_legend_labels = [ (r'%d$mm^2$' % area) for area in area_list]
        #u_legend_labels = [ ('Utilization, area=%d' % area) for area in area_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc='upper center', bbox_to_anchor=(0.5, 1.1),
                              ncol=3, fancybox=True, shadow =True)
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax1.set_ylim(0, 40)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0.2, 1.2)

        #nametag =  "%dnm_%s_%s_f%g" % (self.tech, self.mech, self.ctype, self.appf)
        #figname = '%s_%s_%dw' % (self.prefix, nametag, self.power)
        #fname = '.'.join([figname, self.format])
        #fullname = joinpath(self.outdir, fname)
        fig.savefig('ece6332_report_multiarea.pdf')

    def ece6332_report_multipower(self):
        '''
        Specific for ECE6332 report plot
        '''
        v = [(0.05*i) for i in range(6,23)]
        #v = [(0.1*i) for i in range(2,11)]

        power_list = (80,100,120,140,160,180)
        markers = ['o', '^', 's', '*', 'h', '+', 'x', 'D', 'p']
        
        fig = plt.figure(figsize=(11.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(area=400)
        i = 0
        for power in power_list:
            self.sys.set_sys_prop(power=power)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.speedup_by_vlist(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        #box = ax1.get_position()
        #ax1.set_position([box.x0, box.y0, box.width, box.height*0.95])
        #ax2.set_position([box.x0, box.y0, box.width, box.height*0.95])
        s_legend_labels = [ (r'%d$W$' % power) for power in power_list]
        #u_legend_labels = [ ('Utilization, area=%d' % area) for area in area_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc='upper center', bbox_to_anchor=(0.5, 1.1),
                              ncol=3, fancybox=True, shadow =True)
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax1.set_ylim(0, 32)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0.2, 1.2)

        #nametag =  "%dnm_%s_%s_f%g" % (self.tech, self.mech, self.ctype, self.appf)
        #figname = '%s_%s_%dw' % (self.prefix, nametag, self.power)
        #fname = '.'.join([figname, self.format])
        #fullname = joinpath(self.outdir, fname)
        fig.savefig('ece6332_report_multipower.pdf')

    def plot_multiple_area_with_utilization(self, area_list):
        v = [(0.05*i) for i in range(6,23)]
        #v = [(0.1*i) for i in range(2,11)]

        markers = ['o', '^', 's', '*', 'h', '+', 'x', 'D', 'p']
        
        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title('Speedup with VFS, TDP=%dW' % self.power)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(power=self.power)
        i = 0
        for area in area_list:
            self.sys.set_sys_prop(area=area)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.speedup_by_vlist(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        s_legend_labels = [ (r'Area=%d$mm^2$' % area) for area in area_list]
        #u_legend_labels = [ ('Utilization, area=%d' % area) for area in area_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc="center left")
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0.2, 1.2)

        nametag =  "%dnm_%s_%s_f%g" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s_%dw' % (self.prefix, nametag, self.power)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

    def plot_multiple_power_with_utilization(self, power_list):
        v = [(0.05*i) for i in range(6,23)]
        #v = [(0.1*i) for i in range(2,11)]

        markers = ['o', '^', 's', 'p', '*', 'h', '+', 'x', 'D']
        
        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title(r'Speedup with VFS, Area=%d$mm^2$' % self.area)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')
        ax1.set_xlabel('Supply Voltage (V)')

        self.sys.set_sys_prop(area=self.area)
        i = 0
        for power in power_list:
            self.sys.set_sys_prop(power=power)
            #s[area],u[area] = self.sys.get_speedup(v)
            s,u = self.sys.speedup_by_vlist(v)
            ax1.plot(v, s, '-', marker=self.markers[i])
            ax2.plot(v, u, '--', marker=self.markers[i])
            i = i + 1

        s_legend_labels = [ (r'Power=%d$W$' % power) for power in power_list]
        #u_legend_labels = [ ('Utilization, power=%d' % power) for power in power_list]
        s_legend = ax1.legend(ax1.lines, s_legend_labels, loc="center left")
        #u_legend = ax1.legend(ax2.lines, u_legend_labels, loc="lower right")
        #ax1.add_artist(s_legend)
        ax2.set_ylim(0, 110)
        ax1.set_xlim(0.2, 1.2)

        nametag =  "%dnm_%s_%s_f%g" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s_%dmm' % (self.prefix, nametag, self.area)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

    def _area_bound(self, power):
        sys = self.sys

        sys.set_sys_prop(power=power)
        sys.set_core_prop(tech=self.tech, mech=self.mech, ctype=self.ctype)
        area_threshold = sys.core.area

        area_l = float(100) #left bound
        area_r = float(5000) # right bound

        # make sure the right bound is big enough
        sys.set_sys_prop(area=area_r)
        sys.probe2()
        while (math.fabs(sys.util-1) < 0.1):
            #print "area_r %d is not bigger enough, double" % area_r
            area_r = area_r * 2
            sys.set_sys_prop(area=area_r)
            sys.probe2()
        #print "area_r ends up with %d" % area_r

        while (area_r-area_l) > area_threshold:
            area_p = (area_l+area_r)/2

            sys.set_sys_prop(area=area_p)
            sys.probe2(app=App(f=self.appf))

            #print 'area_p: %f, area_r: %f, area_l: %f, util: %f' % (area_p,area_r, area_l, sys.util)
            if (math.fabs(sys.util-1) < 0.01):
                area_l = area_p
            else:
                area_r = area_p

        area = (area_r+area_l)/2
        sys.set_sys_prop(area=area)
        return (area, sys.volt, sys.speedup)

    def plot_area_bound(self, pmin=60, pmax=205, step=5, amin=100, amax=7000):

        fig = plt.figure(figsize=(9.5,6.9))
        ax1 = fig.add_subplot(111)
        #ax2 = ax1.twinx()
        ax3 = ax1.twinx()

        #ax3.spines["right"].set_position(("axes", 1.2))
        #Plot.make_patch_spines_invisible(ax3)
        #Plot.make_spine_invisible(ax3, "right")

        plt.subplots_adjust(right=0.75)

        ax1.set_title('Dark vs. Dim (%dnm)' % (self.tech,))
        ax1.set_ylabel(r'Area ($mm^2$)')
        #ax2.set_ylabel('Supply voltage when system achieves the best speedup (V)')
        ax3.set_ylabel('Speedup over single baseline IO core')
        ax1.set_xlabel('Power (W)')

        plist = [(power) for power in xrange(pmin, pmax, step)]
        alist = []
        vlist = []
        slist = []

        for power in plist:
            #print "power=%d" % power
            area, vdd, speedup = self._area_bound(power)
            alist.append(area)
            vlist.append(vdd)
            slist.append(speedup)

        #print vlist

        Path = mpath.Path
        dark_pathdata = [
            (Path.MOVETO, (plist[0],amax)),
            (Path.LINETO, (plist[0],alist[0])),
            (Path.LINETO, (plist[-1],alist[-1])),
            (Path.LINETO, (plist[-1],amax)),
            (Path.CLOSEPOLY, (plist[0],amax)),
        ]
    
        dim_pathdata = [
            (Path.MOVETO, (plist[0],amin)),
            (Path.LINETO, (plist[0],alist[0])),
            (Path.LINETO, (plist[-1],alist[-1])),
            (Path.LINETO, (plist[-1],amin)),
            (Path.CLOSEPOLY, (plist[0],amin)),
        ]


        la, = ax1.plot(plist, alist, 'b-', linewidth=1)
        #lv, = ax2.plot(plist, vlist, 'r--', linewidth=3)
        ls, = ax3.plot(plist, slist, 'm-.', linewidth=3)

        #ax1.legend([la,lv,ls], ['Area','Vdd','Speedup'], loc='upper left')
        ax1.grid(True)
        ax1.set_ylim(amin, amax)
        #ax2.set_ylim(0, 1)

        codes, verts = zip(*dim_pathdata)
        dim_path = mpath.Path(verts, codes)
        dim_patch = mpatches.PathPatch(dim_path, facecolor='black', alpha=0.2)
        ax1.add_patch(dim_patch)
        index = plist.index(130)
        acord = alist[index]/2
        ax1.text(130,acord,'Dim silicon region')

        codes, verts = zip(*dark_pathdata)
        dark_path = mpath.Path(verts, codes)
        dark_patch = mpatches.PathPatch(dark_path, facecolor='black', alpha=0.5)
        ax1.add_patch(dark_patch)
        index = plist.index(80)
        acord = (alist[index]+7000)/2
        ax1.text(80,acord,'Dark silicon region')

        ax1.yaxis.label.set_color(la.get_color())
        #ax2.yaxis.label.set_color(lv.get_color())
        ax3.yaxis.label.set_color(ls.get_color())

        ax1.tick_params(axis='y', colors=la.get_color())
        #ax2.tick_params(axis='y', colors=lv.get_color())
        ax3.tick_params(axis='y', colors=ls.get_color())

        bbox_props = dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9)
        t = ax1.text(120,3000, "Speedup", ha="center", va="center", size="medium", rotation=35, color=ls.get_color(), bbox=bbox_props)
        #t = ax2.text(170, 0.53, "Voltage", ha="center", va="center", size="medium", color=lv.get_color(), bbox=bbox_props)


        nametag =  "%dnm_%s_%s_f%.2f" % (self.tech, self.mech, self.ctype, self.appf)
        figname = '%s_%s' % (self.prefix, nametag)
        fname = '.'.join([figname, self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)





    def do_plot(self):
        v = [(0.05*i) for i in range(6,23)]
        
        self.sys.build(area=self.area,power=self.power)
        s, = self.sys.get_speedup(v)
        
        
        fig = plt.figure(figsize=(9.5,6.9))
        fig.suptitle('%dmm, %dw' % (self.area,self.power))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        ax1.set_title('Speedup with VFS, TDP=%dW' % self.power)
        ax1.set_ylabel('Speedup normalized to baseline core')
        ax2.set_ylabel('Utilization (%)')

        ax1.plot(v,s)
#        ax1.set_ylim(0,55)
        
        figname = '%dw_%s_%dmm' % (self.power, self.prefix, self.area)
        fname = '.'.join([figname,self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)
                            
            

from optparse import OptionParser
if __name__=='__main__':

    # sel - select plot mode,
    #    0: do_plot
    #    1: multiple area
    #    2: multiple power
    #    3: boundary area plot
    parser = OptionParser()
    parser.add_option('--sys-area', type='int', default=400)
    parser.add_option('--sys-power', type='int', default=100)
    parser.add_option('--plot-fmt', type='string', default='png')
    parser.add_option('--plot-mode', type='int', default=3)
    parser.add_option('--use-sys2', dest='use_sys2', action='store_true', default=True)
    parser.add_option('--use-sys', dest='use_sys2', action='store_false', default=False)
    (options,args) = parser.parse_args()


    if options.use_sys2:
        plot=PerfScalePlot2(options.sys_area, options.sys_power)
    else:
        plot=PerfScalePlot(options.sys_area, options.sys_power)

    plot.set_prop(format=options.plot_fmt)
    index = 0
    area_list = (200, 400, 800, 1600, 3200, 6400)
    #area_list = (200,)
    power_list = (80,100,120,140,160,180)
    #power_list = (80,)

    if options.plot_mode == 0:
        # work with do_plot
        for p in power_list:
            if options.use_sys2:
                prefix = '%02d_power2' %(index,)
            else:
                prefix = '%02d_power' %(index,)
            plot.set_prop(prefix=prefix, power=p)
            for a in (100, 200, 300, 400, 500, 600,1000, 2000, 4000, 8000, 16000):
                if options.use_sys2:
                    prefix = '%02d_power2' %(index,)
                else:
                    prefix = '%02d_power' %(index,)
                plot.set_prop(prefix=prefix,area=a)
                plot.do_plot()
                
                index = index+1
    elif options.plot_mode == 1:
        # work with multiple area plot
        #area_list=(2000,3000,4000,5000,6000,7000)
        #area_list=(2000,3000,4000,5000)
        #power_list=(90,110,130,150,170)
        for p in power_list:
            if options.use_sys2:
                prefix = 'multiarea2_%02d' %(index,)
            else:
                prefix = 'multiarea_%02d' %(index,)
            plot.set_prop(prefix=prefix, power=p)
            plot.plot_multiple_area_with_utilization(area_list)
            index = index+1
    elif options.plot_mode == 2:
        # work with multiple power plot
        for a in area_list:
            if options.use_sys2:
                prefix = 'multipower2_%02d' % (index, )
            else:
                prefix = 'multipower_%02d' % (index, )
            plot.set_prop(prefix=prefix, area=a)
            plot.plot_multiple_power_with_utilization(power_list)
            index = index + 1
    elif options.plot_mode == 3:
        #for mech in ('ITRS', 'CONS'):
        for mech in ('LP','HKMGS'):
            #for appf in (0.99, 0.9, 0.5, 0.1):
            for appf in (0.99,):
                index = 0
                plot.set_prop(mech=mech, appf=appf) 
                #for tech in (45, 32, 22, 16, 11, 8):
                for tech in (45,32,22,16):
                    if options.use_sys2:
                        prefix = 'areabound2_%02d' % (index,)
                    else:
                        prefix = 'areabound_%02d' % (index,)
                    plot.set_prop(prefix=prefix,tech=tech)
                    plot.plot_area_bound()
                    index = index + 1
    elif options.plot_mode == 4:
        if options.use_sys2:
            prefix='ece6332_multiarea'
            plot.set_prop(prefix=prefix)
            plot.plot_speedup_util_with_area_series()
        else:
            print 'Must use with --use-sys2'

    elif options.plot_mode == 5:
        if options.use_sys2:
            plot.ece6332_report_multiarea()
            plot.ece6332_report_multipower()
        else:
            print 'Must use with --use-sys2'

    else:
        print 'Unknown plot mode %d' % (options.plot_mode,)
            


# old code for reference
#        area_list = (100, 200, 300, 400, 500, 1000, 2000, 3000, 4000)
#        sys = SymSys.SymSys()
#        index = 0
# 
#        for area in area_list:
#            sys.build(area=area,power=self.power)
#            s = sys.get_speedup(v)
#    
#            idstr = '%02d' % (index,)
#            figname = '_'.join([idstr, self.figname, str(area)+'mm'])
#
#            index = index + 1
#    
#            fig = plt.figure(figsize=(9.5,6.9))
#            fig.suptitle('%dmm, 80w' % area)
#            ax1 = fig.add_subplot(111)
#            ax1.plot(v,s)
#            ax1.set_ylim(0,55)
#        
#            fname = '.'.join([figname,self.format])
#            fullname = joinpath(self.outdir, fname)
#            fig.savefig(fullname)
