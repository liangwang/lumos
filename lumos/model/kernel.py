#!/usr/bin/env python
# encoding: utf-8
import scipy.stats
import numpy
import configparser
from lxml import etree
import logging
from lumos import settings

_logger = logging.getLogger('Kernel')
if settings.DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

ASIC_PERF_RATIO = 5


class UCoreParam(object):
    PARAMS = ('miu', 'phi', 'bw')

    def __init__(self, miu=0.001, phi=0.001, bw=0.001):
        object.__setattr__(self, '_miu', miu)
        object.__setattr__(self, '_phi', phi)
        object.__setattr__(self, '_bw', bw)

    @property
    def miu(self):
        return self._miu
    @miu.setter
    def miu(self, miu):
        object.__setattr__(self, '_miu', miu)

    @property
    def phi(self):
        return self._phi
    @phi.setter
    def phi(self, phi):
        object.__setattr__(self, '_phi', phi)

    @property
    def bw(self):
        return self._bw
    @bw.setter
    def bw(self, bw):
        object.__setattr__(self, '_bw', bw)

    def __str__(self):
        return '[{0}] miu: {1}, phi: {2}, bw: {3}'.format(
            self.__repr__(), self._miu, self._phi, self._bw)

    def __setattr__(self, name, value):
        if hasattr(self, '_'+name):
            object.__setattr__(self, name, value)
        else:
            raise TypeError('{0} has no member of {1}'.format(
                self.__class__.__name__, name))


class KernelError(Exception):
    pass


class Kernel(object):
    def __init__(self, kid):
        self._kid = kid
        self._accelerators = dict()

    def __str__(self):
        return '{0}: {1}'.format(self.__repr__(), self._kid)

    @property
    def kid(self):
        return self._kid

    def add_acc(self, acc_id, ucore_param):
        self._accelerators[acc_id] = ucore_param

    def del_acc(self, acc_id):
        try:
            del self._accelerators[acc_id]
        except KeyError:
            _logger.warning('No accelerator named {0} available'.format(acc_id))

    def get_acc(self, acc_id):
        try:
            return self._accelerators[acc_id]
        except KeyError:
            raise KernelError('Kernel {0} does not have accelerator {1}'.format(
                self._kid, acc_id))

    def list_all_accs(self):
        return self._accelerators.keys()


kernel_pool = {
    'MMM': {
        'GPU': UCoreParam(miu=3.41, phi=0.74, bw=0.725),
        'FPGA': UCoreParam(miu=0.75, phi=0.31, bw=0.325),
        'ASIC': UCoreParam(miu=27.4, phi=0.79, bw=3.62),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=0.216),
        'IO': UCoreParam(miu=1, phi=1, bw=0.16),
    },
    'BS': {
        'GPU': UCoreParam(miu=17.0, phi=0.57, bw=5.85),
        'FPGA': UCoreParam(miu=5.68, phi=0.26, bw=3.975),
        'ASIC': UCoreParam(miu=482, phi=4.75, bw=66.249),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=0.35),
        'IO': UCoreParam(miu=1, phi=1, bw=0.26),
    },
    'FFT': {
        'GPU': UCoreParam(miu=2.42, phi=0.59, bw=1),
        'FPGA': UCoreParam(miu=2.81, phi=0.29, bw=1),
        'ASIC': UCoreParam(miu=733, phi=5.34, bw=1),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=1),
        'IO': UCoreParam(miu=1, phi=1, bw=1),
    },
    'fpgaeff1': {
        'GPU': UCoreParam(miu=3.41, phi=0.74, bw=0.725),
        'FPGA': UCoreParam(miu=20, phi=0.5, bw=2),
        'ASIC': UCoreParam(miu=27.4, phi=0.79, bw=3.62),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=0.216),
        'IO': UCoreParam(miu=1, phi=1, bw=0.16),
    },
    'fpgaeff2': {
        'GPU': UCoreParam(miu=3.41, phi=0.74, bw=0.725),
        'FPGA': UCoreParam(miu=40, phi=2.5, bw=20),
        'ASIC': UCoreParam(miu=87.4, phi=2.79, bw=30.62),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=0.216),
        'IO': UCoreParam(miu=1, phi=1, bw=0.16),
    },
    'asiceff1': {
        'GPU': UCoreParam(miu=17.0, phi=0.57, bw=5.85),
        'FPGA': UCoreParam(miu=20, phi=2, bw=8),
        'ASIC': UCoreParam(miu=482, phi=4.75, bw=66.249),
        'O3CPU': UCoreParam(miu=1, phi=1, bw=0.35),
        'IO': UCoreParam(miu=1, phi=1, bw=0.26),
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

def create_fixednorm(dist_params, fname='fixednorm.cfg', size=100, kid_prefix='fixednorm',
        occur=None, perf_range=None):
    """
    Create kernels with relative U-core performance following a normal distribution,
    but fixed kernel sample points

    :dist_params: distribution parameters, including mean, std, etc.
    :fname: file to store kernels
    :size: number of kernels to create
    :kid_prefix: prefix string for kernel id
    :perf_range: (min,max) of performance range, if not set, default to 0.5*mean, and 1.5*mean
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

    cfg = configparser.RawConfigParser()
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
    cfg = configparser.RawConfigParser()
    for rv, prob,kid in zip(rvs, probs, ids):
        kname = 'norm%03d'% kid
        cfg.add_section(kname)
        cfg.set(kname, 'fpga_miu', rv)
        cfg.set(kname, 'asic_miu', rv*ASIC_PERF_RATIO)
        cfg.set(kname, 'occur', prob)

    with open(fname, 'wb') as f:
        cfg.write(f)


def create_fixednorm_xml(dist_params, fname='fixednorm.xml', size=100,
                         kid_prefix='fixednorm', perf_range=None):
    """
    Create kernels with relative U-core performance following a normal
    distribution. The actual sampled kernels have the relative performance
    uniformly drawn from the range of 0.5*mean to 1.5*mean, if not specified.
    The probability of presence in an application for a kernel is the CDF of its
    relative performance in the normal distribution.

    Args:
       dist_params (dict):
          Distribution parameters, such as mean, standard deviation.
       fname (str):
          file to save the generated kernels, default to ``fixednorm.xml``
       size (int):
          number of kernels to create, default to 100.
       kid_prefix (str):
          prefix string for kernel id
       perf_range (pair):
          A pair of (min,max) specifying the performance range, if not set,
          default to 0.5*mean as min, and 1.5*mean as max.

    Returns:
       N/A


    """
    kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]
    perf_mean = dist_params['mean']
    perf_std = dist_params['std']

    if perf_range:
        perf_min,perf_max = perf_range
    else:
        perf_min = 0.5 * perf_mean
        perf_max = 1.5 * perf_mean

    rvs = numpy.linspace(perf_min, perf_max, size)
    rvs2 = numpy.linspace(perf_min, perf_max, size-1)
    cdfs = scipy.stats.norm.cdf(rvs2, perf_mean, perf_std)
    probs1 = numpy.insert(cdfs, 0, 0)
    probs2 = numpy.append(cdfs, 1)
    probs = (probs2-probs1) * 1.5 # 1.5 is kernel_count_per_app (average)

    root = etree.Element('kernels')
    for kernel,perf,prob in zip(kernels, rvs, probs):
        k_root = etree.SubElement(root, 'kernel')
        k_root.set('name', kernel)

        fpga_root = etree.SubElement(k_root, 'fpga')
        fpga_root.set('miu', '%.3e'% (perf/ASIC_PERF_RATIO))

        asic_root = etree.SubElement(k_root, 'asic')
        asic_root.set('miu', '%.3e'%perf)

        ele = etree.SubElement(k_root, 'occur')
        ele.text = '%.3e' % prob

    tree = etree.ElementTree(root)
    tree.write(fname, pretty_print=True)



def create_randnorm_xml(dist_params,fname='randnorm.xml', size=100,
                        kid_prefix='randnorm'):
    """
    Create kernels with relative U-core performance following a normal
    distribution. The actual sampled kernels have the relative performance
    randomly drawn from the normal distribution. The probability of presence in
    an application for a kernel is the CDF of its relative performance in the
    normal distribution.

    Args:
       dist_params (dict):
          Distribution parameters, such as mean, standard deviation.
       fname (str):
          file to save the generated kernels, default to ``randnorm.xml``
       size (int):
          number of kernels to create, default to 100.
       kid_prefix (str):
          prefix string for kernel id


    Returns:
       N/A


    """

    miu = dist_params['mean']
    sigma = dist_params['std']
    rvs = numpy.random.normal(miu, sigma, size*2)
    rvs_positive = [ rv for rv in rvs if rv > 0][:size]
    rvs = rvs_positive

    probs = scipy.stats.norm.pdf(rvs, miu, sigma)
    ids = numpy.arange(size)
    kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]

    root = etree.Element('kernels')
    for kernel,perf,prob in zip(kernels, rvs, probs):
        k_root = etree.SubElement(root, 'kernel')
        k_root.set('name', kernel)

        fpga_root = etree.SubElement(k_root, 'fpga')
        fpga_root.set('miu', '%.3e'% (perf/ASIC_PERF_RATIO))

        asic_root = etree.SubElement(k_root, 'asic')
        asic_root.set('miu', '%.3e'% (perf))

        ele = etree.SubElement(k_root, 'occur')
        ele.text = '%.3e' % prob

    tree = etree.ElementTree(root)
    tree.write(fname, pretty_print=True)


def load(fname='norm.cfg'):
    cfg = configparser.RawConfigParser()
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

def reg_kernels(kernels):
    """
    Add kernels to kernel dict

    Args:
       kernels (dict):
          dict to kernels

    Return:
       N/A
    """
    kernel_pool.update(kernels)

def load_xml(fname='norm.xml'):
    """
    Load kernels from an XML file. Also update the global kernel pool
    (kernel_pool). If a kernel with the same name has already been loaded into
    the global kernel pool, it will be overide with the new one.

    Args:
       fname (str):
          The file to be loaded

    Returns:
       kernels (list):
          A sorted (by name) list of kernels that have been loaded.
    """
    tree = etree.parse(fname)
    kernels = []
    for k_root in tree.iter('kernel'):
        k_name = k_root.get('name')
        kernels.append(k_name)

        kernel_pool[k_name] = dict()
        accelerator_root = k_root.find('accelerator')
        for ele in accelerator_root.getchildren():
            uid = ele.tag
            miu = float(ele.get('miu'))
            kernel_pool[k_name][uid] = UCoreParam(miu=miu)

        ele = k_root.find('occur')
        prob = float(ele.text)


        kernel_pool[k_name]['occur'] = prob

    return sorted(kernels)


def load_kernels(fname='norm.xml'):
    """Load kernels from an XML file.

    Args:
       fname (filepath):
          The file to be loaded, in XML format

    Returns:
       kernels (dict):
          A dict of (kernel_name, kernel_object) pair, indexed by kernel's name.

    Raises:
        KernelError: if parameters is not float
    """
    tree = etree.parse(fname)
    kernels = dict()
    for k_root in tree.iter('kernel'):
        k_name = k_root.get('name')
        k = Kernel(k_name)

        accelerator_root = k_root.find('accelerator')
        for ele in accelerator_root.getchildren():
            acc_id = ele.tag
            ucore_param = UCoreParam()
            for attr, val in ele.items():
                try:
                    setattr(ucore_param, attr, float(val))
                except (ValueError, TypeError):
                    raise KernelError(
                        'Error decoding Ucore parameters, attr: {0}, val: {1}, '
                        'val is not a float')
            k.add_acc(acc_id, ucore_param)

        kernels[k_name] = k
    return kernels


def do_test():
    params = {'mean': 80,
            'std': 10}
    #create_fixednorm_xml(params, fname='ker_test.xml', size=20)
    #create_randnorm(params, fname='ker_test.cfg', size=10)
    #kernels = load_xml('ker_test.xml')
    kernels = load_xml('kernels_asic_inc.xml')
    print(kernels)
    print(kernel_pool)
    #for i in xrange(20):
        #print random.gauss(6,2)
    #rvs = scipy.stats.norm.rvs(80,20,size=20)
    #probs = scipy.stats.norm.pdf(rvs, 80,20)
    #print rvs
    #print probs

def do_generate():
    #params = {'mean': 200,
            #'std': 35}
    #occur = numpy.linspace(0.9, 0.1, 10)
    #create_fixednorm_xml(params, fname='fixednorm_10.xml', size=10)
    params = {'mean': 100,
            'std': 25}
    #create_fixednorm_xml(params, fname='fixednorm_fpga80x.xml', size=10)
    create_randnorm_xml(params, size=1000, fname='config/kernels_norm20x5.xml')

def load_from_xml(fname='norm.xml'):
    """Load kernels from an XML file. This is different from load_xml,
    which is old and should be obsolete. load_from_xml expects a
    different XML format from the previous load_xml.

    Args:
       fname (str):
          The file to be loaded

    Returns:
       kernels (list):
          A sorted (by name) list of kernels that have been loaded.

    """
    tree = etree.parse(fname)
    kernels = dict()
    for k_root in tree.iter('kernel'):
        k_name = k_root.get('name')
        k = Kernel(k_name)

        accelerator_root = k_root.find('accelerator')
        for ele in accelerator_root.getchildren():
            acc_id = ele.tag
            ucore_param = UCoreParam()
            for attr,val in ele.items():
                try:
                    setattr(ucore_param, attr, float(val))
                except ValueError:
                    print('(attr, val): {0}, {1}, val is not a float'.format(attr, val))
                except TypeError as te:
                    print(te)

            k.add_acc(acc_id, ucore_param)

        kernels[k_name] = k
    return kernels



if __name__ == '__main__':
    #do_test()
    do_generate()
