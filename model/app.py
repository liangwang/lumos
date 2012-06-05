#!/usr/bin/env python
import logging


class App(object):
    """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
    def __init__(self, f=0.9, m=0):
        """ Initialize an application

        Arguments:
        f -- the fraction of parallel part of program (default 0.9)
        m -- the factor of memory latency (default 0)

        """
        self.f = f
        self.f_noacc = f

        self.m = m

        self.kernels = {}

    def __repr__(self):
        return self.tag

    def tag_update(self):
        f_str = str(int((self.f-self.f_noacc)*100))

        return '-'.join([f_str,] + [('%s-%d' % (kid, int(self.kernels[kid]*100))) for kid in self.kernels]) 

    def reg_kernel(self, kid, cov):
        """Register a kernel that could be accelerated by certain ASIC, or more
           Generalized GPU/FPGA

        :kid: @todo
        :cov: @todo
        :returns: True if register succeed
                  False if failed

        """
        kernels = self.kernels

        if kid in kernels:
            logging.error('Kernel %s already exist' % kid)
            return False

        if cov > self.f_noacc:
            logging.error('cov of %s is too large to exceed the overall parallel ratio' % kid)
            return False

        kernels[kid] = cov
        self.f_noacc = self.f_noacc - cov

        #self.tag = '_'.join([kid, '-'.join([str(int(100*(1-self.f))), str(int(100*(self.f_noacc))), str(int(100*cov))])])
        self.tag = self.tag_update()

        return True

    def set_cov(self, kid, cov):
        """Set the coverage of a kernel

        :kid: @todo
        :cov: @todo
        :returns: @todo

        """
        kernels = self.kernels

        if kid not in kernels:
            logging.error('Kernel %s has not been registerd' % kid)
            return False

        cov_old = kernels[kid]

        if self.f_noacc + cov_old < cov:
            logging.error('cov of %s is too large to exceed the overall parallel ratio' % kid)
            return False

        kernels[kid] = cov
        self.f_noacc = self.f_noacc + cov_old - cov

        self.tag = self.tag_update()

        return True

    def get_kernel(self):
        """Get the first kernel as kid
        :returns: @todo

        """
        kids = self.kernels.keys()
        return kids[0]

    def get_kids(self):
        return self.kernels.keys()

    def get_cov(self, kid):
        return kids

    def has_kernels(self):
        if self.kernels:
            return True
        else:
            return False

class UCoreParam:
    def __init__(self, miu, phi, bw):
        self.miu = miu
        self.phi = phi
        self.bw = bw


class AppMMM(dict):
    name = 'MMM'
    def __init__(self, f=0.9, m=0, f_acc=0):
        super(dict, self).__init__()

        self["GPU"] = UCoreParam(miu=3.41,phi=0.74, bw=0.725)
        self["FPGA"] = UCoreParam(miu=0.75,phi=0.31, bw=0.325)
        self["ASIC"] = UCoreParam(miu=27.4,phi=0.79, bw=3.62)
        self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=0.216)
        self["IO"] = UCoreParam(miu=1,phi=1, bw=0.16)

        self.f = f
        self.f_acc = f_acc
        self.m = m

        self.tag = '_'.join([self.name,
            '-'.join([str(int(100*(1-f))), str(int(100*(f-f_acc))), str(int(100*f_acc))])])


class AppBS(dict):
    name = 'BS'
    def __init__(self, f=0.9, m=0, f_acc=0):
        super(dict, self).__init__()

        self["GPU"] = UCoreParam(miu=17.0,phi=0.57, bw=5.85)
        self["FPGA"] = UCoreParam(miu=5.68,phi=0.26, bw=3.975)
        self["ASIC"] = UCoreParam(miu=482,phi=4.75, bw=66.249)
        self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=0.35)
        self["IO"] = UCoreParam(miu=1,phi=1, bw=0.26)

        self.f = f
        self.f_acc = f_acc
        self.m = m

        self.tag = '_'.join([self.name,
            '-'.join([str(int(100*(1-f))), str(int(100*(f-f_acc))), str(int(100*f_acc))])])


class AppFFT64(dict):
    name = 'FFT'
    def __init__(self, f=0.9, m=0, f_acc=0):
        super(dict, self).__init__()

        self["GPU"] = UCoreParam(miu=2.42,phi=0.59, bw = 1)
        self["FPGA"] = UCoreParam(miu=2.81,phi=0.29, bw = 1)
        self["ASIC"] = UCoreParam(miu=733,phi=5.34, bw = 1)
        self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=1)
        self["IO"] = UCoreParam(miu=1,phi=1, bw=1)

        self.f = f
        self.f_acc = f_acc
        self.m = m

        self.tag = '_'.join([self.name,
            '-'.join([str(int(100*(1-f))), str(int(100*(f-f_acc))), str(int(100*f_acc))])])

if __name__ == '__main__':
    app = App(1)
    app.reg_kernel('MMM', 0.1)
    app.reg_kernel('BS', 0.2)
    print app.tag
