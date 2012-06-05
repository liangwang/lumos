#!/usr/bin/env python
# encoding: utf-8
import scipy.stats
import numpy
import ConfigParser
import random
import math

ASIC_PERF_RATIO = 5

class UCoreParam:
    def __init__(self, miu=0.001, phi=0.001, bw=0.001):
        self.miu = miu
        self.phi = phi
        self.bw = bw

class Kernel(dict):
    def __init__(self, kid, app_occ_prob=1):
        dict.__init__(self)
        self['app_occ_prob'] = app_occ_prob
        self.kid = kid

kernel_pool = {
'MMM': {
    'GPU': UCoreParam(miu=3.41,phi=0.74,bw=0.725),
    'FPGA': UCoreParam(miu=0.75,phi=0.31, bw=0.325),
    'ASIC': UCoreParam(miu=27.4,phi=0.79, bw=3.62),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=0.216),
    'IO': UCoreParam(miu=1,phi=1, bw=0.16),
    },
'BS' : {
    'GPU': UCoreParam(miu=17.0,phi=0.57, bw=5.85),
    'FPGA': UCoreParam(miu=5.68,phi=0.26, bw=3.975),
    'ASIC': UCoreParam(miu=482,phi=4.75, bw=66.249),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=0.35),
    'IO': UCoreParam(miu=1,phi=1, bw=0.26),
    },
'FFT': {
    'GPU': UCoreParam(miu=2.42,phi=0.59, bw = 1),
    'FPGA': UCoreParam(miu=2.81,phi=0.29, bw = 1),
    'ASIC': UCoreParam(miu=733,phi=5.34, bw = 1),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=1),
    'IO': UCoreParam(miu=1,phi=1, bw=1),
    },
'fpgaeff1': {
    'GPU': UCoreParam(miu=3.41,phi=0.74,bw=0.725),
    'FPGA': UCoreParam(miu=20,phi=0.5, bw=2),
    'ASIC': UCoreParam(miu=27.4,phi=0.79, bw=3.62),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=0.216),
    'IO': UCoreParam(miu=1,phi=1, bw=0.16),
    },
'fpgaeff2': {
    'GPU': UCoreParam(miu=3.41,phi=0.74,bw=0.725),
    'FPGA': UCoreParam(miu=40,phi=2.5, bw=20),
    'ASIC': UCoreParam(miu=87.4,phi=2.79, bw=30.62),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=0.216),
    'IO': UCoreParam(miu=1,phi=1, bw=0.16),
    },
'asiceff1' : {
    'GPU': UCoreParam(miu=17.0,phi=0.57, bw=5.85),
    'FPGA': UCoreParam(miu=20,phi=2, bw=8),
    'ASIC': UCoreParam(miu=482,phi=4.75, bw=66.249),
    'O3CPU': UCoreParam(miu=1,phi=1, bw=0.35),
    'IO': UCoreParam(miu=1,phi=1, bw=0.26),
    },
}

def get_kernel(kid):
    """get kernel by kid

    :kid: @todo
    :returns: kernel dict if kid existed in kernel_pool,
              None, if kid is not find

    """
    if kid in kernel_pool:
        return kernel_pool[kid]
    else:
        return None

def gauss_pdf(rv, mean, std):
    return (1/math.sqrt(2*math.pi*(std**2)) * math.exp(-(rv-mean)**2)/(2*(std**2)))

def gen_kernel_gauss(mean, std, num=None):
    ken_gauss = dict()
    if num:
        rvs = scipy.stats.norm.rvs(mean, std, size=num)
        probs = scipy.stats.norm.pdf(rvs, mean, std)
        id = 0
        for rv,prob in zip(rvs, probs):
            ken_gauss['gauss%d' % id ] = {'FPGA': UCoreParam(miu=rv),
                                        'prob': prob}
            id = id + 1

        #for id in xrange(num):
            #uc_miu = random.gauss(mean,std)
            #while not uc_miu > 0:
                #uc_miu = random.gauss(mean, std)
            #prob = gauss_pdf(uc_miu, mean, std)
            #ken_gauss['gauss%d' % id ] = {'FPGA': UCoreParam(miu=uc_miu),
                                        #'prob': prob}
            
    else:
        rv = scipy.stats.norm.rvs(mean, std)
        prob = scipy.stats.norm.pdf(rv, mean, std)
        id = len(kernel_pool)+1
        ken_gauss['gauss%d' % id] = {'FPGA': UCoreParam(miu=rv),
                                                     'prob': prob}

    kernel_pool.update(ken_gauss)
    return ken_gauss

def create_fixednorm(dist_params, fname='fixednorm.cfg', size=100, kid_prefix='fixednorm', occur=None):
    """Create kernels with performance in normal distribution,
    but fixed kernel sample points

    :dist_params: distribution parameters, including mean, std, etc.
    :fname: file to store kernels
    :size: number of kernels to create
    :kid_prefix: prefix string for kernel id
    :returns: N/A

    """
    kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]
    perf_mean = dist_params['mean']
    perf_std = dist_params['std']
    rvs = numpy.linspace(0.5*perf_mean, 1.5*perf_mean, size)
    if occur:
        probs = occur
    else:
        rvs2 = numpy.linspace(0.5*perf_mean, 1.5*perf_mean, size-1)
        cdfs = scipy.stats.norm.cdf(rvs2, perf_mean, perf_std)
        probs1 = numpy.insert(cdfs, 0, 0)
        probs2 = numpy.append(cdfs, 1)
        probs = (probs2-probs1) * 1.5 # 1.5 is kernel_count_per_app (average)

    cfg = ConfigParser.RawConfigParser()
    for kernel,perf,prob in zip(kernels, rvs, probs):
        cfg.add_section(kernel)
        cfg.set(kernel, 'fpga_miu', perf/ASIC_PERF_RATIO)
        cfg.set(kernel, 'asic_miu', perf)
        cfg.set(kernel, 'occur', prob)

    with open(fname, 'wb') as f:
        cfg.write(f)


def create_randnorm(dist_params,fname='norm.cfg', size=100, kid_prefix='randnorm'):
    """Create kernels with performance in normal distribution,
    and randomly choose kernel sample points

    :dist_params: distribution parameters, including mean, std, etc.
    :fname: file to store kernels
    :size: number of kernels to create
    :kid_prefix: prefix string for kernel id
    :returns: N/A

    """

    miu = dist_params['mean']
    sigma = dist_params['std']
    rvs = numpy.random.normal(miu, sigma, size)
    probs = scipy.stats.norm.pdf(rvs, miu, sigma)
    ids = numpy.arange(size)
    cfg = ConfigParser.RawConfigParser()
    for rv, prob,kid in zip(rvs, probs, ids):
        kname = 'norm%03d'% kid
        cfg.add_section(kname)
        cfg.set(kname, 'fpga_miu', rv)
        cfg.set(kname, 'asic_miu', rv*ASIC_PERF_RATIO)
        cfg.set(kname, 'occur', prob)

    with open(fname, 'wb') as f:
        cfg.write(f)

def load(fname='norm.cfg'):
    cfg = ConfigParser.RawConfigParser()
    cfg.read(fname)
    for sec in cfg.sections():
        fpga_miu = float(cfg.get(sec, 'fpga_miu'))
        asic_miu = float(cfg.get(sec, 'asic_miu'))
        prob = float(cfg.get(sec, 'occur'))
        kernel_pool[sec] = {
                'FPGA': UCoreParam(miu=fpga_miu),
                'ASIC': UCoreParam(miu=asic_miu),
                'occur': prob
                }

    return sorted(cfg.sections())

def do_test():
    params = {'mean': 80,
            'std': 10}
    create_fixednorm(params, fname='ker_test.cfg', size=20)
    #create_randnorm(params, fname='ker_test.cfg', size=10)
    kernels = load('ker_test.cfg')
    print kernels
    #for i in xrange(20):
        #print random.gauss(6,2)
    #rvs = scipy.stats.norm.rvs(80,20,size=20)
    #probs = scipy.stats.norm.pdf(rvs, 80,20)
    #print rvs
    #print probs

def do_generate():
    params = {'mean': 200,
            'std': 35}
    occur = numpy.linspace(0.9, 0.1, 10)
    create_fixednorm(params, fname='fixednorm_10.cfg', size=10)

if __name__ == '__main__':
    #do_test()
    do_generate()
