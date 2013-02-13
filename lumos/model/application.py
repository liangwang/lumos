#!/usr/bin/env python
import logging
import numpy.random
import scipy.stats


class App(object):
    """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
    def __init__(self, f=0.9, m=0, name='app'):
        """ Initialize an application

        Arguments:
        f -- the fraction of parallel part of program (default 0.9)
        m -- the factor of memory latency (default 0)

        """
        self.f = f
        self.f_noacc = f

        self.m = m

        self.name = name

        self.kernels = {}

        self.tag = self.tag_update()

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
        return self.kernels[kid]

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


def build(cov, occ, probs, kernels, name, f_parallel=1):
    """Build an application from a set of kernels

    :cov: coverage percentage of all present kernels
    :occ: occurance bit-vector for all kernels
    :probs: probability vector of all kernels for appearance
    :kernels: all possible kernels (kernel pool)
    :name: The name of the application
    :f_parallel: the fraction of parallel part
    :returns: the resulting application

    """
    active_kernels = dict()
    psum = 0
    for o,p,acc in zip(occ, probs, kernels):
        if o:
            active_kernels[p] = acc
            psum = psum + p

    ksorted = sorted(active_kernels.items())
    krever = ksorted[:] # make another copy
    krever.reverse()
    app = App(f=f_parallel, name=name)

    for (p, acc),(prv,acc2) in zip(ksorted, krever):
        kcov = cov * prv / psum
        #kcov = 0.05
        app.reg_kernel(acc, kcov)

    return app


def build_single(cov, kernel, name, f_parallel=1):
    app = App(f=f_parallel, name=name)
    app.reg_kernel(kernel, cov)

    return app


def random_uc_cov(dist, param1, param2):
    """@todo: Docstring for rand_uc_cov

    :dist: @todo
    :param1: @todo
    :param2: @todo
    :returns: @todo

    """
    if dist == 'norm':
        mean = param1
        std = param2
        r = scipy.stats.norm.rvs(mean, std)
        while r < 0:
            r = scipy.stats.norm.rvs(mean, std)
    elif dist == 'lognorm':
        mean = param1
        std = param2
        r = numpy.random.lognormal(mean, std)
    elif dist == 'uniform':
        rmin = param1
        rmax = param2
        r = numpy.random.uniform(rmin, rmax)
        while r < 0:
            r = numpy.random.uniform(rmin, rmax)
    else:
        loggging.error('Unknown distribution for coverage: %s' % dist)
        r = 0

    return r

def random_kernel_cov(cov_params):
    dist = cov_params['dist']

    if dist == 'norm':
        mean = cov_params['mean']
        std = cov_params['std']
        r = scipy.stats.norm.rvs(mean, std)
        while r < 0:
            r = scipy.stats.norm.rvs(mean, std)
    elif dist == 'lognorm':
        mean = cov_params['mean']
        std = cov_params['std']
        r = numpy.random.lognormal(mean, std)
    elif dist == 'uniform':
        rmin = cov_params['min']
        rmax = cov_params['max']
        r = numpy.random.uniform(rmin, rmax)
        while r < 0:
            r = numpy.random.uniform(rmin, rmax)
    else:
        loggging.error('Unknown distribution for coverage: %s' % dist)
        r = 0

    return r

if __name__ == '__main__':
    app = App(1)
    app.reg_kernel('MMM', 0.1)
    app.reg_kernel('BS', 0.2)
    print app.tag
