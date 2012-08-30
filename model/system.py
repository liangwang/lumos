#!/usr/bin/env python

import logging
from core import IOCore, O3Core, PERF_BASE
from ucore import UCore, ASIC, FPGA
from application import App

VMIN = 0.3
VMAX = 1.1
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 0.001  # 1mV
PROBE_PRECISION = 0.0001


from conf import misc as miscConfig
DEBUG = miscConfig.debug


class HeteroSys(object):
    """Heterogenous system composed by regular cores, accelerators
    such as ASICs, FPGA, and GPU"""

    def __init__(self, budget, mech=None, tech=None,
                 serial_core=None):
        """Initialize system with budget

        :budget: @todo

        """
        self.sys_area = budget.area
        self.sys_power = budget.power
        self.sys_bw = budget.bw

        self.mech = mech
        self.tech = tech

        self.asic_dict = {}
        self.gp_acc = FPGA()
        self.use_gpacc = False

        self.thru_core = IOCore(mech=mech, tech=tech)
        self.dim_perf = None

        if serial_core:
            self.serial_core = serial_core
            self.thru_core_area = self.sys_area - serial_core.area
        else:
            self.serial_core = IOCore(mech=mech,tech=tech)
            self.thru_core_area = self.sys_area

    def set_asic(self, kid, area_ratio):
        area = self.sys_area * area_ratio

        if kid not in self.asic_dict:
            if self.thru_core_area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False
            self.thru_core_area = self.thru_core_area - area
            self.asic_dict[kid] = ASIC(kid=kid, area=area, mech=self.mech, tech=self.tech)

            self.dim_perf = None # need to update dim_perf later
            return True
        else:
            asic_core = self.asic_dict[kid]

            if self.thru_core_area + asic_core.area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False

            self.thru_core_area = self.thru_core_area + asic_core.area - area
            asic_core.config(area=area)

            self.dim_perf = None # need to update dim_perf later
            return True


    # replaced by set_asic
    #def add_asic(self, kid, area_ratio):
        #"""Add a ASIC with certain area (in persentage of total system area)

        #:kid: @todo
        #:area: @todo
        #:returns: @todo

        #"""
        #area = self.sys_area * area_ratio

        #if self.core_area < area:
            #logging.error('not enough area for this ASIC %s' % kid)
            #return False

        #self.core_area = self.core_area - area
        #self.asic_dict[kid] = ASIC(kid=kid, area=area, mech=self.mech, tech=self.tech)

        #return True

    # replaced by set_asic
    #def realloc_asic(self, kid, area_ratio):
        #"""Set the area ratio of a asic kernel

        #:kid: @todo
        #:area_ratio: @todo
        #:returns: @todo

        #"""
        #if kid not in self.asic_dict:
            #logging.error('kernel %s has not been registered' % kid)
            #return False

        #asic_core = self.asic_dict[kid]

        #area = self.sys_area * area_ratio
        #if self.core_area + asic_core.area < area:
            #logging.error('not enough area for this ASIC %s' % kid)
            #return False

        #self.core_area = self.core_area + asic_core.area - area
        #asic_core.config(area=area)

        #return True

    def del_asic(self, kid):
        if kid not in self.asic_dict:
            logging.error('kernel %s has not been registered' % kid)
            return False

        asic_core = self.asic_dict[kid]
        self.thru_core_area = self.thru_core_area + asic_core.area

        del self.asic_dict[kid]

        self.dim_perf = None # need ot update dim_perf later
        return True

    def del_asics(self):
        for kid in self.asic_dict.keys():
            self.del_asic(kid)

    def realloc_gpacc(self, area_ratio, ctype='FPGA'):
        """Add a general-purpose accelerator with certain area

        :ctype: @todo
        :area_ratio: @todo
        :returns: @todo

        """
        area = self.sys_area * area_ratio
        if self.thru_core_area + self.gp_acc.area < area:
            logging.error('not enough area for this GP accelerator %s' % ctype)
            return False

        self.thru_core_area = self.thru_core_area + self.gp_acc.area - area
        self.gp_acc.config(area=area, mech=self.mech, tech=self.tech)

        self.dim_perf = None # need to update dim_perf later
        return True

    def set_mech(self, mech):
        """Set the mech of all cores and ucores

        :mech: @todo
        :returns: @todo

        """
        self.thru_core.config(mech=mech)
        self.serial_core.config(mech=mech)
        self.gp_acc.config(mech=mech)

        for k in self.asic_dict:
            self.asic_dict[k].config(mech=mech)

        self.mech = mech

        self.dim_perf = None # need to update dim_perf later

    def set_tech(self, tech):
        """Set the technology node of all cores and ucores

        :tech: @todo
        :returns: @todo

        """
        self.thru_core.config(tech=tech)
        self.serial_core.config(tech=tech)
        self.gp_acc.config(tech=tech)

        for k in self.asic_dict:
            self.asic_dict[k].config(tech=tech)

        self.tech = tech
        self.sys_bandwidth = self.sys_bw[tech]

        self.dim_perf = None # need to update dim_perf later

    def set_core_pv(self, pv):
        """Whether consider process variations

        :pv: @todo
        :returns: @todo

        """
        self.thru_core.config(pv=pv)
        self.serial_core.config(pv=pv)

        self.dim_perf = None # need to update dim_perf later

    def _dim_perf_cnum(self, cnum, vmin=VMIN):
        """Get the performance of Dim silicon with given active number of cores

        :cnum: @todo
        :app: @todo
        :returns: @todo

        """
        core = self.thru_core

        cnum_max = int(self.thru_core_area / core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.thru_core_power / float(cnum)

        if vmin > VMIN:
            core.dvfs_by_volt(vmin)
            if core.power > cpower:
                active_cnum = min(int(self.thru_core_area / core.area),
                                  int(self.core_power / core.power))

                perf = active_cnum * core.perf
                return {'perf': perf / PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'util': float(100 * active_cnum) / float(cnum_max)}
        else:
            vmin = VMIN

        vl = vmin
        vr = core.v0 * VSF_MAX
        vm = (vl + vr) / 2

        while (vr - vl) > V_PRECISION:
            vm = (vl + vr) / 2
            core.dvfs_by_volt(vm)

            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.dvfs_by_volt(vr)
        rpower = core.power

        if rpower <= cpower:
            rperf = cnum * core.perf
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}
        else:
            core.dvfs_by_volt(vl)
            lperf = cnum * core.perf
            return {'perf': lperf / PERF_BASE,
                    'vdd': vl,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

    def _dim_perf_opt(self):
        """Get the performance of Dim silicon subsystem

        :returns: @todo

        """
        core = self.thru_core
        cnum_max = int(self.thru_core_area / core.area)
        cnum_list = range(1, cnum_max + 1)

        perf = 0
        for cnum in cnum_list:
            r = self._dim_perf_cnum(cnum)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                opt_cnum = cnum

        return {'cnum': opt_cnum,
                'vdd': vdd,
                'util': util,
                'perf': perf}

    def calc_dim_perf(self, thru_core_power=None):
        if thru_core_power:
            self.thru_core_power = thru_core_power
        else:
            self.thru_core_power = self.sys_power

        ret = self._dim_perf_opt()

        self.dim_perf = ret['perf']
        self.opt_cnum = ret['cnum']
        self.opt_vdd = ret['vdd']

    def get_perf(self, app):
        """The overall performance

        :app: @todo
        :returns: @todo

        """
        #thru_core = self.thru_core
        serial_core = self.serial_core
        gp_acc = self.gp_acc

        asics = self.asic_dict

        serial_core.dvfs_by_factor(VSF_MAX)
        serial_perf = serial_core.perf / PERF_BASE

        if not self.dim_perf:
            # need to update dim_perf
            self.thru_core_power = self.sys_power
            ret = self._dim_perf_opt()
            self.dim_perf = ret['perf']
            self.opt_cnum = ret['cnum']
            self.opt_vdd = ret['vdd']

        dim_perf = self.dim_perf
        perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf

        for kernel in app.kernels:
            if self.use_gpacc:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / (gp_acc.perf(kernel, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
            else:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / dim_perf

        return {'perf': 1 / perf,
                'cnum': self.opt_cnum,
                'vdd': self.opt_vdd}


class HeteroSys_old(object):
    """Heterogenous system composed by regular cores, accelerators
    such as ASICs, FPGA, and GPU"""

    def __init__(self, budget, mech=None, tech=None):
        """Initialize system with budget

        :budget: @todo

        """
        self.sys_area = budget.area
        self.sys_power = budget.power
        self.sys_bw = budget.bw

        self.mech = mech
        self.tech = tech

        self.core_area = self.sys_area
        self.asic_dict = {}
        self.gp_acc = FPGA()
        self.use_gpacc = False
        self.core = IOCore()

    def set_asic(self, kid, area_ratio):
        area = self.sys_area * area_ratio

        if kid not in self.asic_dict:
            if self.core_area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False
            self.core_area = self.core_area - area
            self.asic_dict[kid] = ASIC(kid=kid, area=area, mech=self.mech, tech=self.tech)

            return True
        else:
            asic_core = self.asic_dict[kid]

            if self.core_area + asic_core.area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False

            self.core_area = self.core_area + asic_core.area - area
            asic_core.config(area=area)

            return True

    def add_asic(self, kid, area_ratio):
        """Add a ASIC with certain area (in persentage of total system area)

        :kid: @todo
        :area: @todo
        :returns: @todo

        """
        area = self.sys_area * area_ratio

        if self.core_area < area:
            logging.error('not enough area for this ASIC %s' % kid)
            return False

        self.core_area = self.core_area - area
        self.asic_dict[kid] = ASIC(kid=kid, area=area, mech=self.mech, tech=self.tech)

        return True

    def realloc_asic(self, kid, area_ratio):
        """Set the area ratio of a asic kernel

        :kid: @todo
        :area_ratio: @todo
        :returns: @todo

        """
        if kid not in self.asic_dict:
            logging.error('kernel %s has not been registered' % kid)
            return False

        asic_core = self.asic_dict[kid]

        area = self.sys_area * area_ratio
        if self.core_area + asic_core.area < area:
            logging.error('not enough area for this ASIC %s' % kid)
            return False

        self.core_area = self.core_area + asic_core.area - area
        asic_core.config(area=area)

        return True

    def del_asic(self, kid):
        if kid not in self.asic_dict:
            logging.error('kernel %s has not been registered' % kid)
            return False

        asic_core = self.asic_dict[kid]
        self.core_area = self.core_area + asic_core.area

        del self.asic_dict[kid]
        return True

    def del_asics(self):
        for kid in self.asic_dict.keys():
            self.del_asic(kid)

    def realloc_gpacc(self, area_ratio, ctype='FPGA'):
        """Add a general-purpose accelerator with certain area

        :ctype: @todo
        :area_ratio: @todo
        :returns: @todo

        """
        area = self.sys_area * area_ratio
        if self.core_area + self.gp_acc.area < area:
            logging.error('not enough area for this GP accelerator %s' % ctype)
            return False

        self.core_area = self.core_area + self.gp_acc.area - area
        self.gp_acc.config(area=area, mech=self.mech, tech=self.tech)

    def set_mech(self, mech):
        """Set the mech of all cores and ucores

        :mech: @todo
        :returns: @todo

        """
        self.core.config(mech=mech)
        self.gp_acc.config(mech=mech)

        for k in self.asic_dict:
            self.asic_dict[k].config(mech=mech)

        self.mech = mech

    def set_tech(self, tech):
        """Set the technology node of all cores and ucores

        :tech: @todo
        :returns: @todo

        """
        self.core.config(tech=tech)
        self.gp_acc.config(tech=tech)

        for k in self.asic_dict:
            self.asic_dict[k].config(tech=tech)

        self.tech = tech
        self.sys_bandwidth = self.sys_bw[tech]

    def set_core_pv(self, pv):
        """Whether consider process variations

        :pv: @todo
        :returns: @todo

        """
        self.core.config(pv=pv)

    def _dim_perf_cnum(self, cnum, vmin=VMIN):
        """Get the performance of Dim silicon with given active number of cores

        :cnum: @todo
        :app: @todo
        :returns: @todo

        """
        core = self.core

        cnum_max = int(self.core_area / core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.core_power / float(cnum)

        if vmin > VMIN:
            core.dvfs_by_volt(vmin)
            if core.power > cpower:
                active_cnum = min(int(self.core_area / core.area),
                                  int(self.core_power / core.power))

                perf = active_cnum * core.perf
                return {'perf': perf / PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'util': float(active_cnum * 100) / float(cnum_max)}
        else:
            vmin = VMIN

        vl = vmin
        vr = core.v0 * VSF_MAX
        vm = (vl + vr) / 2

        while (vr - vl) > V_PRECISION:
            vm = (vl + vr) / 2
            core.dvfs_by_volt(vm)

            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.dvfs_by_volt(vr)
        rpower = core.power

        if rpower <= cpower:
            rperf = cnum * core.perf
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}
        else:
            core.dvfs_by_volt(vl)
            lperf = cnum * core.perf
            return {'perf': lperf / PERF_BASE,
                    'vdd': vl,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

    def _dim_perf_opt(self):
        """Get the performance of Dim silicon subsystem

        :returns: @todo

        """
        core = self.core
        cnum_max = int(self.core_area / core.area)
        cnum_list = range(1, cnum_max + 1)

        perf = 0
        for cnum in cnum_list:
            r = self._dim_perf_cnum(cnum)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                opt_cnum = cnum

        return {'cnum': opt_cnum,
                'vdd': vdd,
                'util': util,
                'perf': perf}

    def get_perf(self, app):
        """The overall performance

        :app: @todo
        :returns: @todo

        """
        core = self.core
        gp_acc = self.gp_acc

        asics = self.asic_dict

        core.dvfs_by_factor(VSF_MAX)
        serial_perf = core.perf / PERF_BASE

        self.core_power = self.sys_power
        ret = self._dim_perf_opt()
        dim_perf = ret['perf']
        opt_cnum = ret['cnum']
        opt_vdd = ret['vdd']

        perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf

        for kernel in app.kernels:
            if self.use_gpacc:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / (gp_acc.perf(kernel, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
            else:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / dim_perf

        return {'perf': 1 / perf,
                'cnum': opt_cnum,
                'vdd': opt_vdd}


class AsymSys(object):
    """Asymmetric system composed by IO cores, O3 cores, FPGAs, GPUs, and ASICs (or UCores)"""

    def __init__(self, budget):
        """Initialize the budget of the system

        :area: @todo
        :power: @todo

        """
        self.sys_area = budget.area
        self.sys_power = budget.power
        self.bw = budget.bw

        self.core = IOCore()
        self.ucore = UCore()

    def set_sys_prop(self, **kwargs):
        """Set system properties

        :**kwargs: @todo
        :returns: @todo

        """
        for k, v in kwargs.items():
            k = k.lower()
            setattr(self, k, v)

    def set_core_prop(self, **kwargs):
        """Set core properties

        :**kwargs: @todo
        :returns: @todo

        """
        self.core.config(**kwargs)

    def set_tech(self, tech):
        self.core.config(tech=tech)
        self.ucore.config(tech=tech)
        self.sys_bandwidth = self.bw[tech]

    def set_mech(self, mech):
        self.core.config(mech=mech)
        self.ucore.config(mech=mech)

    def set_ucore_type(self, uctype):
        self.ucore.config(ctype=uctype)

    def set_ucore_prop(self, **kwargs):
        """Set u-core properties

        :**kwargs: @todo
        :returns: @todo

        """
        self.ucore.config(**kwargs)

    def set_core_pv(self, pv):
        """Set process variation to core

        :pv: True: process variation, False: no variation
        :returns: @todo

        """
        self.core.config(pv=pv)

    def _dim_perf_cnum(self, cnum, app, vmin=VMIN):
        """Get the performance of Dim silicon with given active number of cores

        :cnum: @todo
        :app: @todo
        :returns: @todo

        """
        core = self.core
        #f = app.f - app.f_acc

        cnum_max = int(self.core_area / core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.core_power / float(cnum)

        if vmin > VMIN:
            core.dvfs_by_volt
            if core.power > cpower:
                active_cnum = min(int(self.core_area / core.area),
                                  int(self.core_power / core.power))

                perf = active_cnum * core.perf
                return {'perf': perf / PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'util': float(active_cnum * 100) / float(cnum_max)}
        else:
            vmin = VMIN

        vl = vmin
        vr = core.v0 * VSF_MAX
        vm = (vl + vr) / 2

        while (vr - vl) > V_PRECISION:
            vm = (vl + vr) / 2
            core.dvfs_by_volt(vm)

            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.dvfs_by_volt(vr)
        rpower = core.power

        if rpower <= cpower:
            rperf = cnum * core.perf
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}
        else:
            core.dvfs_by_volt(vl)
            lpower = core.power
            lperf = cnum * core.perf
            return {'perf': lperf / PERF_BASE,
                    'vdd': vl,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

    def _dim_perf_opt(self, app):
        """Get the performance of Dim silicon subsystem

        :app: @todo
        :returns: @todo

        """
        core = self.core
        cnum_max = int(self.core_area / core.area)
        cnum_list = range(1, cnum_max + 1)

        perf = 0
        for cnum in cnum_list:
            r = self._dim_perf_cnum(cnum, app)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                opt_cnum = cnum

        return {'cnum':opt_cnum,
                'vdd': vdd,
                'util': util,
                'perf': perf}

    def get_perf(self, area=None, power=None, app=App()):
        """Get the performance of the system on a certain app

        :area: @todo
        :power: @todo
        :app: @todo
        :returns: @todo

        """
        core = self.core
        ucore = self.ucore

        self.core_power = self.sys_power

        core.dvfs_by_factor(VSF_MAX)
        serial_perf = core.perf / PERF_BASE

        ret = self._dim_perf_opt(app)
        dim_perf = ret['perf']
        opt_cnum = ret['cnum']
        opt_vdd = ret['vdd']

        ucore_perf = ucore.perf(app, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE

        #logging.debug('ucore.area %f' % ucore.area )

        if ucore.area != 0:
            perf = 1 / (
                    (1 - app.f) / serial_perf +
                    (app.f - app.f_acc) / dim_perf +
                    app.f_acc / ucore_perf)
        else:
            perf = 1 / (
                    (1 - app.f) / serial_perf +
                    app.f / dim_perf )


        #logging.debug('tech: %d, dim_perf: %f, ucore_perf: %f, perf: %f, cnum: %d, vdd: %f' 
                #% (core.tech, dim_perf, ucore_perf, perf, opt_cnum, opt_vdd))

        return {'perf': perf,
                'cnum': opt_cnum,
                'vdd': opt_vdd}

    def ucore_alloc(self, area=None, per=None, cnum=None):
        """allocate area budget for ucores

        :area: specify ucore area budget by absolute area value (mm^2)
        :per: specify ucore area budget by percentage
        :cnum: specify ucore area by the number of IO cores
        :returns: True for succeed, False for failure

        """
        alloc_ok = False

        if area is not None:
            ucore_area = area
            self.core_area = self.sys_area - ucore_area
            alloc_ok = True
        elif per is not None:
            if alloc_ok:
                alloc_ok = False
                logging.error('can not specify area and percentage at the same time')
            else:
                # TODO sanity check on per
                ucore_area = self.sys_area * per
                self.core_area = self.sys_area - ucore_area
                alloc_ok = True
        elif cnum is not None:
            if alloc_ok:
                alloc_ok = False
                logging.error('can no specify percentage and core number at the same time')
            else:
                # TODO sanity check on cnum
                ucore_area = self.core.area * cnum
                self.core_area = self.sys_area - ucore_area
                alloc_ok = True
        else:
            logging.error('no area specified')

        if alloc_ok:
            self.ucore.config(area=ucore_area)

        return alloc_ok

class SymSys(object):
    """
    Symmetric many core system
    """
    def __init__(self, area=None, power=None):
        if area:
            self.area = area
        else:
            self.area = 0

        if power:
            self.power = power
        else:
            self.power = 0

    def set_core_prop(self, **kwargs):
        self.core.config(**kwargs)

    def set_sys_prop(self, **kwargs):
        for k, v in kwargs.items():
            k = k.lower()
            setattr(self, k, v)

    def get_core_num(self):
        core = self.core
        return int(self.area / core.area)

    def perf_by_vfs(self, vfs, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0 * core.freq
        sperf = core.perf

        core.dvfs_by_factor(vfs)
        active_num = min(int(self.area / core.area),
                         int(self.power / core.power))
        #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        perf = 1 / ((1 - f) / sperf + f / (active_num * core.perf))
        core_num = int(self.area / core.area)
        util = float(100 * active_num) / float(core_num)
        return {'perf': perf / PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'freq' : core.freq,
                'util': util}

    def perf_by_vdd(self, vdd, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf=core.perf0*core.freq
        sperf=core.perf

        core.dvfs_by_volt(vdd)
        active_num = min(int(self.area / core.area),
                         int(self.power / core.power))
        #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        perf = 1/ ((1 - f) / sperf + f / (active_num * core.perf))
        core_num = int(self.area / core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util}

    def perf_by_cnum(self, cnum, app=App(f=0.99), vmin=VMIN):

        core = self.core
        f = app.f

        cnum_max = int(self.area/core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.power/float(cnum)
        #print cpower

        # Serial performance is achieved by the highest vdd
        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf=core.perf0*core.freq
        sperf=core.perf
        #logging.debug( 'sperf: %g, freq: %g' % (sperf, core.freq))

        # Check whether vmin can meet the power requirement
        if vmin > VMIN:
            core.dvfs_by_volt(vmin)
            if core.power > cpower:
                # Either vmin is too high or active_cnum is too large
                # so that the system could not meet the power budget even
                # with the minimum vdd. Return the active core number with vmin
                # Users can capture the exception by comparing the active_cnum
                # and the returned active_cnum
                active_cnum = min(int(self.area/core.area),
                                 int(self.power/core.power))
                #perf = 1/((1-f)/sperf + f/(active_cnum*core.perf0*core.freq))
                perf = 1/((1-f)/sperf + f/(active_cnum*core.perf))
                util = float(100*active_cnum)/float(cnum)
                return {'perf': perf/PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'freq': core.freq,
                        'util': util}
        else:
            vmin = VMIN


        vl = vmin
        vr = core.v0 * VSF_MAX
        vm = (vl+vr)/2

        while (vr-vl)>V_PRECISION:
            vm = (vl+vr)/2
            core.dvfs_by_volt(vm)


            #print '[Core]\t:vl:%f, vr: %f, vm: %f, freq: %f, power: %f, area: %f' % (vl, vr, vm, core.freq, core.power, core.area)
            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.dvfs_by_volt(vl)
        lpower = core.power
        lfreq = core.freq
        lcnum = min(int(self.area/core.area),
                    int(self.power/lpower))
        #lperf = 1/((1-f)/sperf + f/(cnum*core.perf0*core.freq))
        lperf = 1/((1-f)/sperf + f/(cnum*core.perf))

        core.dvfs_by_volt(vr)
        rpower = core.power
        rfreq = core.freq
        rcnum = min(int(self.area/core.area),
                    int(self.power/rpower))
        #rperf = 1/((1-f)/sperf + f/(cnum*core.perf0*core.freq))
        rperf = 1/((1-f)/sperf + f/(cnum*core.perf))

        if rpower <= cpower:
            # right bound meets the power constraint
            return {'perf': rperf/PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'freq': rfreq,
                    'util': float(100*cnum)/float(cnum_max)}
        else:
            return {'perf': lperf/PERF_BASE,
                    'vdd': vl,
                    'freq': lfreq,
                    'cnum': cnum,
                    'util': float(100*cnum)/float(cnum_max)}


        #if vr == vm:
            #core.dvfs_by_volt(vl)

        ## debug use only
        ##if active_cnum == cnum:
            ##print 'freq: %g, vdd: %g, perf_base: %g' % (core.freq, core.vdd, PERF_BASE)
        ## end debug
        #perf = 1/((1-f)/sperf + f/(active_cnum*core.perf0*core.freq))
        #util = float(100*active_cnum)/float(cnum)
        #return {'perf': perf/PERF_BASE,
                #'vdd': vm,
                #'cnum': active_cnum,
                #'util': util}


    def probe2(self, app=App(f=0.99)):
        core = self.core
        f = app.f

        v0 = core.v0
        vleft = VMIN
        vright = v0 * VSF_MAX
        vpivot = (vleft+vright)/2

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0*core.freq
        sperf = core.perf

        while (vpivot-vleft) > (PROBE_PRECISION/2) :
            vl = vpivot - PROBE_PRECISION / 2
            vr = vpivot + PROBE_PRECISION / 2

            core.dvfs_by_volt(vl)
            active_num = min(self.area/core.area, self.power/core.power)
            l_num = active_num
            #sl = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))
            sl = 1/ ( (1-f)/sperf + f/(active_num*core.perf))

            core.dvfs_by_volt(vpivot)
            active_num = min(self.area/core.area, self.power/core.power)
            p_num = active_num
            #sp = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))
            sp = 1/ ( (1-f)/sperf + f/(active_num*core.perf))
            core_num = active_num

            core.dvfs_by_volt(vr)
            active_num = min(self.area/core.area, self.power/core.power)
            r_num = active_num
            #sr = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))
            sr = 1/ ( (1-f)/sperf + f/(active_num*core.perf))

            #print 'lv: %f, lc: %f, rv: %f, rc: %f, pv: %f, pc: %f' % (vl, l_num, vr, r_num, vpivot, p_num)
            if sl<sp<sr:
                vleft=vpivot
                vpivot = (vleft+vright)/2
            elif sl>sp>sr:
                vright = vpivot
                vpivot = (vleft+vright)/2
            elif sp > sl and sp > sr:
                # vpivot is the optimal speedup point
                break

        self.volt = vpivot
        self.speedup = sp/PERF_BASE
        self.util = core_num*core.area/self.area

    def speedup_by_vfslist(self, vfs_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0*core.freq
        sperf = core.perf

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for vfs in vfs_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_factor(vfs)
            active_num = min(self.area/core.area, self.power/core.power)
            #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
            speedup_list.append(perf/PERF_BASE)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)

    def speedup_by_vlist(self, v_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0*core.freq
        sperf = core.perf

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for v in v_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_volt(v)
            active_num = min(self.area/core.area, self.power/core.power)
            #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
            speedup_list.append(perf/PERF_BASE)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)

    def opt_core_num(self, app=App(f=0.99), vmin=VMIN):

        cnum_max = self.get_core_num()
        cnumList = range(1, cnum_max+1)

        perf = 0
        for cnum in cnumList:
            r = self.perf_by_cnum(cnum, app, vmin)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                freq = r['freq']
                optimal_cnum = cnum

        return {'cnum': optimal_cnum,
                'vdd' : vdd,
                'freq': freq,
                'util': util,
                'perf': perf}


    def perf_by_dark(self, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf=core.perf0*core.freq
        sperf=core.perf

        #vdd = min(core.v0*1.3, VMAX)
        vdd = core.v0 * VSF_MAX
        #core.dvfs_by_volt(vdd)
        #print 'Area:%d, Power: %d, tech: %d, mech: %s, vdd: %g, freq: %g, power: %g' % (self.area, self.power, core.tech, core.mech, core.vdd, core.freq, core.power)
        active_num = min(int(self.area/core.area),
                         int(self.power/core.power))
        #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util,
                'vdd': vdd}

class System(object):


    PROBE_PRECISION = 0.0001
    VSF_MIN = 0.2
    VSF_MAX = 1.0


    def __init__(self, area=0, power=0,
                 ctype='IO', mech='ITRS', tech=45):

        self.numIO = 0
        self.numO3 = 0

        self.area = 0
        self.power= 0

        # Performance of IO core at nominal frequency, according to Pollack's Rule
        self.perf_base = PERF_BASE

        if ctype == 'IO':
            self.core = IOCore(mech=mech, tech=tech)
        else:
            self.core = O3Core(mech=mech, tech=tech)

        self.ctype = ctype
        self.mech = mech
        self.tech = tech

        self.active_num = 0
        self.perf_max = 0
        self.speedup = 0
        self.util = 0
        self.volt = 0

    def set_core_prop(self, **kwargs):
        self.core.config(**kwargs)

    def set_sys_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)

    def build(self,type='sym-io',area=200,power=80):
        self.area = area
        self.power = power

        #if type=='sym-io':
            #iocore = Core45nmCon()
            #self.numIO = area / iocore.area


    def probe(self, app = App(f=0.99)):
        """"
        Sweep voltage (by core.dvfs) to get the best performance for a given app
        """
        #core = Core45nmCon()
        if self.ctype == 'IO':
            core = IOCore(mech=self.mech, tech=self.tech)
        else:
            core = O3Core(mech=self.mech, tech=self.tech)

        #para_ratio = 0.99
        para_ratio = app.f

        #perf_base = core.perf0 * core.f0
        perf_base = core.perf
        perf_max = perf_base
        core_num = min(self.area/core.area, self.power/core.power)
        util = core_num*core.area/self.area
        volt = core.vdd

        for vsf in [(1-0.0001*i) for i in range(1,10000)]:
            # FIXME: consider dvfs_by_volt for future technology
            core.dvfs_by_factor(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            #perf = 1/ ( (1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))
            perf = 1/ ( (1-para_ratio)/perf_base + para_ratio/(active_num*core.perf))

            if perf > perf_max:
                perf_max = perf
                core_num = active_num
                util = core_num*core.area/self.area
                volt = core.vdd
            else :
                break

        self.active_num = core_num
        self.perf_max = perf_max
        self.speedup = perf_max / perf_base
        self.util = util
        self.volt = volt

    def probe2(self, app=None):
        """"
        A fast version of probe, using binary search
        """
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        if app is None:
            app = App(f=0.99)


        core = self.core
        para_ratio = app.f

        perf_base = self.perf_base

        v0 = core.v0
        vleft = v0 * self.VSF_MIN
        vright = v0 * self.VSF_MAX
        vpivot = (vleft+vright)/2

        # FIXME: assum v0/f0 is the highest v/f
        #sperf=core.perf0*core.f0
        sperf=core.perf
        while (vpivot-vleft) > (self.PROBE_PRECISION/2) :
            vl = vpivot - self.PROBE_PRECISION / 2
            vr = vpivot + self.PROBE_PRECISION / 2

            core.dvfs_by_volt(vl)
            active_num = min(self.area/core.area, self.power/core.power)
            l_num = active_num
            #sl = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))
            sl = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf))

            core.dvfs_by_volt(vpivot)
            active_num = min(self.area/core.area, self.power/core.power)
            p_num = active_num
            #sp = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))
            sp = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf))
            core_num = active_num

            core.dvfs_by_volt(vr)
            active_num = min(self.area/core.area, self.power/core.power)
            r_num = active_num
            #sr = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))
            sr = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf))

            #logging.debug('lv: %f, lc: %f, rv: %f, rc: %f, pv: %f, pc: %f' % (vl, l_num, vr, r_num, vpivot, p_num))
            if sl<sp<sr:
                vleft=vpivot
                vpivot = (vleft+vright)/2
            elif sl>sp>sr:
                vright = vpivot
                vpivot = (vleft+vright)/2
            elif sp > sl and sp > sr:
                # vpivot is the optimal speedup point
                break

        self.volt = vpivot
        self.speedup = sp/perf_base
        self.util = core_num*core.area/self.area



    def get_speedup(self, vsf_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        para_ratio = app.f

        #perf_base = core.perf0 * core.freq
        # FIXME: use highest vdd as sperf, other than perf_base
        perf_base = self.perf_base

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for vsf in vsf_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_factor(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ((1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))
            speedup_list.append(perf/perf_base)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)

if __name__ == '__main__':
    sys = SymSys(area=600, power=120)
    sys.set_sys_prop(core=IOCore(mech='HKMGS', tech=45))
    app=App(f=1)
    for cnum in (2,4,8,16,32,64):
        r = sys.perf_by_cnum(cnum, app)
        print (r['perf'], r['freq'])


