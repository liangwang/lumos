#!/usr/bin/env python
# encoding: utf-8
import configparser
from lxml import etree
import logging
from lumos import settings

_logger = logging.getLogger('Kernel')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

ASIC_PERF_RATIO = 5


class KernelError(Exception):
    pass


class KernelParam(object):
    # miu -> perf, phi -> power
    PARAMS = ('perf', 'power', 'bw')

    def __init__(self, perf=0.001, power=0.001, bw=0.001):
        object.__setattr__(self, '_perf', perf)
        object.__setattr__(self, '_power', power)
        object.__setattr__(self, '_bw', bw)

    @property
    def perf(self):
        return self._perf
    @perf.setter
    def perf(self, perf):
        object.__setattr__(self, '_perf', perf)

    @property
    def power(self):
        return self._power
    @power.setter
    def power(self, power):
        object.__setattr__(self, '_power', power)

    @property
    def bw(self):
        return self._bw
    @bw.setter
    def bw(self, bw):
        object.__setattr__(self, '_bw', bw)

    def __str__(self):
        return '[{0}] perf: {1}, power: {2}, bw: {3}'.format(
            self.__repr__(), self._perf, self._power, self._bw)

    def __setattr__(self, name, value):
        if hasattr(self, '_'+name):
            object.__setattr__(self, name, value)
        else:
            raise TypeError('{0} has no member of {1}'.format(
                self.__class__.__name__, name))


class Kernel():
    def __init__(self, name, parallel_factor=0):
        self._name = name
        self._kernel_params = dict()

        self.pf = parallel_factor
        if parallel_factor:
            self.is_serial = True
        else:
            self.is_serial = False

    def __str__(self):
        return '{0}: {1}'.format(self.__repr__(), self._name)

    @classmethod
    def load_from_xmltree(cls, xmltree):
        name = xmltree.get('name')
        if not name:
            raise KernelError('No name in kernel config')

        parallel_factor = xmltree.get('parallel_factor')
        if not parallel_factor:
            parallel_factor = 1
        else:
            parallel_factor = float(parallel_factor)

        k = cls(name, parallel_factor)
        acc_root = xmltree.find('accelerator')
        if acc_root is None:
            return k

        for ele in acc_root:
            acc_id = ele.tag
            kernel_param = KernelParam()
            for attr, val in ele.items():
                try:
                    setattr(kernel_param, attr, float(val))
                except TypeError as e:
                    raise e
                except ValueError:
                    raise KernelError(
                        'Error decoding Ucore parameters, attr: {0}, val: {1}, '
                        'val is not a float'.format(attr, val))
            k._add_kernel_param(acc_id, kernel_param)
        return k

    @property
    def name(self):
        return self._name

    def _add_kernel_param(self, acc_id, kernel_param):
        self._kernel_params[acc_id] = kernel_param

    def get_kernel_param(self, acc_id):
        try:
            return self._kernel_params[acc_id]
        except KeyError:
            raise KernelError('Kernel {0} does not register accelerator {1}, availables are {2}'.format(
                self._name, acc_id, self._kernel_params.keys()))

    def get_all_accs(self):
        return self._kernel_params.keys()


def load_suite_xmltree(xmltree):
    kernels = dict()
    # for r_ in xmltree.findall('kernel'):
    for r_ in xmltree.findall('kernel'):
        k = Kernel.load_from_xmltree(r_)
        kernels[k.name] = k
    return kernels


def load_suite_xmlfile(xmlfile):
    ele_tree = etree.parse(xmlfile)
    return load_suite_xmltree(ele_tree)

# kernel_pool = {
#     'MMM': {
#         'GPU': KernelParam(perf=3.41, power=0.74, bw=0.725),
#         'FPGA': KernelParam(perf=0.75, power=0.31, bw=0.325),
#         'ASIC': KernelParam(perf=27.4, power=0.79, bw=3.62),
#         'O3CPU': KernelParam(perf=1, power=1, bw=0.216),
#         'IO': KernelParam(perf=1, power=1, bw=0.16),
#     },
#     'BS': {
#         'GPU': KernelParam(perf=17.0, power=0.57, bw=5.85),
#         'FPGA': KernelParam(perf=5.68, power=0.26, bw=3.975),
#         'ASIC': KernelParam(perf=482, power=4.75, bw=66.249),
#         'O3CPU': KernelParam(perf=1, power=1, bw=0.35),
#         'IO': KernelParam(perf=1, power=1, bw=0.26),
#     },
#     'FFT': {
#         'GPU': KernelParam(perf=2.42, power=0.59, bw=1),
#         'FPGA': KernelParam(perf=2.81, power=0.29, bw=1),
#         'ASIC': KernelParam(perf=733, power=5.34, bw=1),
#         'O3CPU': KernelParam(perf=1, power=1, bw=1),
#         'IO': KernelParam(perf=1, power=1, bw=1),
#     },
#     'fpgaeff1': {
#         'GPU': KernelParam(perf=3.41, power=0.74, bw=0.725),
#         'FPGA': KernelParam(perf=20, power=0.5, bw=2),
#         'ASIC': KernelParam(perf=27.4, power=0.79, bw=3.62),
#         'O3CPU': KernelParam(perf=1, power=1, bw=0.216),
#         'IO': KernelParam(perf=1, power=1, bw=0.16),
#     },
#     'fpgaeff2': {
#         'GPU': KernelParam(perf=3.41, power=0.74, bw=0.725),
#         'FPGA': KernelParam(perf=40, power=2.5, bw=20),
#         'ASIC': KernelParam(perf=87.4, power=2.79, bw=30.62),
#         'O3CPU': KernelParam(perf=1, power=1, bw=0.216),
#         'IO': KernelParam(perf=1, power=1, bw=0.16),
#     },
#     'asiceff1': {
#         'GPU': KernelParam(perf=17.0, power=0.57, bw=5.85),
#         'FPGA': KernelParam(perf=20, power=2, bw=8),
#         'ASIC': KernelParam(perf=482, power=4.75, bw=66.249),
#         'O3CPU': KernelParam(perf=1, power=1, bw=0.35),
#         'IO': KernelParam(perf=1, power=1, bw=0.26),
#     },
# }


# def get_kernel(kid):
#     """get kernel by kid

#     :kid: @todo
#     :returns: kernel dict if kid existed in kernel_pool,
#               None, if kid is not find

#     """
#     if kid in kernel_pool:
#         return kernel_pool[kid]
#     else:
#         return None


# def gen_kernel_gauss(mean, std, num=None):
#     ken_gauss = dict()
#     if num:
#         rvs = scipy.stats.norm.rvs(mean, std, size=num)
#         probs = scipy.stats.norm.pdf(rvs, mean, std)
#         id = 0
#         for rv,prob in zip(rvs, probs):
#             ken_gauss['gauss%d' % id ] = {'FPGA': KernelParam(perf=rv),
#                                         'prob': prob}
#             id = id + 1

#         #for id in xrange(num):
#             #uc_perf = random.gauss(mean,std)
#             #while not uc_perf > 0:
#                 #uc_perf = random.gauss(mean, std)
#             #prob = gauss_pdf(uc_perf, mean, std)
#             #ken_gauss['gauss%d' % id ] = {'FPGA': KernelParam(perf=uc_perf),
#                                         #'prob': prob}

#     else:
#         rv = scipy.stats.norm.rvs(mean, std)
#         prob = scipy.stats.norm.pdf(rv, mean, std)
#         id = len(kernel_pool)+1
#         ken_gauss['gauss%d' % id] = {'FPGA': KernelParam(perf=rv),
#                                                      'prob': prob}

#     kernel_pool.update(ken_gauss)
#     return ken_gauss

# def create_fixednorm(dist_params, fname='fixednorm.cfg', size=100, kid_prefix='fixednorm',
#         occur=None, perf_range=None):
#     """
#     Create kernels with relative U-core performance following a normal distribution,
#     but fixed kernel sample points

#     :dist_params: distribution parameters, including mean, std, etc.
#     :fname: file to store kernels
#     :size: number of kernels to create
#     :kid_prefix: prefix string for kernel id
#     :perf_range: (min,max) of performance range, if not set, default to 0.5*mean, and 1.5*mean
#     :returns: N/A

#     """
#     kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]
#     perf_mean = dist_params['mean']
#     perf_std = dist_params['std']
#     rvs = numpy.linspace(0.5*perf_mean, 1.5*perf_mean, size)
#     if occur:
#         probs = occur
#     else:
#         rvs2 = numpy.linspace(0.5*perf_mean, 1.5*perf_mean, size-1)
#         cdfs = scipy.stats.norm.cdf(rvs2, perf_mean, perf_std)
#         probs1 = numpy.insert(cdfs, 0, 0)
#         probs2 = numpy.append(cdfs, 1)
#         probs = (probs2-probs1) * 1.5 # 1.5 is kernel_count_per_app (average)

#     cfg = configparser.RawConfigParser()
#     for kernel,perf,prob in zip(kernels, rvs, probs):
#         cfg.add_section(kernel)
#         cfg.set(kernel, 'fpga_perf', perf/ASIC_PERF_RATIO)
#         cfg.set(kernel, 'asic_perf', perf)
#         cfg.set(kernel, 'occur', prob)

#     with open(fname, 'wb') as f:
#         cfg.write(f)

# def create_randnorm(dist_params,fname='norm.cfg', size=100, kid_prefix='randnorm'):
#     """Create kernels with performance in normal distribution,
#     and randomly choose kernel sample points

#     :dist_params: distribution parameters, including mean, std, etc.
#     :fname: file to store kernels
#     :size: number of kernels to create
#     :kid_prefix: prefix string for kernel id
#     :returns: N/A

#     """

#     perf = dist_params['mean']
#     sigma = dist_params['std']
#     rvs = numpy.random.normal(perf, sigma, size)
#     probs = scipy.stats.norm.pdf(rvs, perf, sigma)
#     ids = numpy.arange(size)
#     cfg = configparser.RawConfigParser()
#     for rv, prob,kid in zip(rvs, probs, ids):
#         kname = 'norm%03d'% kid
#         cfg.add_section(kname)
#         cfg.set(kname, 'fpga_perf', rv)
#         cfg.set(kname, 'asic_perf', rv*ASIC_PERF_RATIO)
#         cfg.set(kname, 'occur', prob)

#     with open(fname, 'wb') as f:
#         cfg.write(f)


# def create_fixednorm_xml(dist_params, fname='fixednorm.xml', size=100,
#                          kid_prefix='fixednorm', perf_range=None):
#     """
#     Create kernels with relative U-core performance following a normal
#     distribution. The actual sampled kernels have the relative performance
#     uniformly drawn from the range of 0.5*mean to 1.5*mean, if not specified.
#     The probability of presence in an application for a kernel is the CDF of its
#     relative performance in the normal distribution.

#     Args:
#        dist_params (dict):
#           Distribution parameters, such as mean, standard deviation.
#        fname (str):
#           file to save the generated kernels, default to ``fixednorm.xml``
#        size (int):
#           number of kernels to create, default to 100.
#        kid_prefix (str):
#           prefix string for kernel id
#        perf_range (pair):
#           A pair of (min,max) specifying the performance range, if not set,
#           default to 0.5*mean as min, and 1.5*mean as max.

#     Returns:
#        N/A


#     """
#     kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]
#     perf_mean = dist_params['mean']
#     perf_std = dist_params['std']

#     if perf_range:
#         perf_min,perf_max = perf_range
#     else:
#         perf_min = 0.5 * perf_mean
#         perf_max = 1.5 * perf_mean

#     rvs = numpy.linspace(perf_min, perf_max, size)
#     rvs2 = numpy.linspace(perf_min, perf_max, size-1)
#     cdfs = scipy.stats.norm.cdf(rvs2, perf_mean, perf_std)
#     probs1 = numpy.insert(cdfs, 0, 0)
#     probs2 = numpy.append(cdfs, 1)
#     probs = (probs2-probs1) * 1.5 # 1.5 is kernel_count_per_app (average)

#     root = etree.Element('kernels')
#     for kernel,perf,prob in zip(kernels, rvs, probs):
#         k_root = etree.SubElement(root, 'kernel')
#         k_root.set('name', kernel)

#         fpga_root = etree.SubElement(k_root, 'fpga')
#         fpga_root.set('perf', '%.3e'% (perf/ASIC_PERF_RATIO))

#         asic_root = etree.SubElement(k_root, 'asic')
#         asic_root.set('perf', '%.3e'%perf)

#         ele = etree.SubElement(k_root, 'occur')
#         ele.text = '%.3e' % prob

#     tree = etree.ElementTree(root)
#     tree.write(fname, pretty_print=True)


# def create_randnorm_xml(dist_params,fname='randnorm.xml', size=100,
#                         kid_prefix='randnorm'):
#     """
#     Create kernels with relative U-core performance following a normal
#     distribution. The actual sampled kernels have the relative performance
#     randomly drawn from the normal distribution. The probability of presence in
#     an application for a kernel is the CDF of its relative performance in the
#     normal distribution.

#     Args:
#        dist_params (dict):
#           Distribution parameters, such as mean, standard deviation.
#        fname (str):
#           file to save the generated kernels, default to ``randnorm.xml``
#        size (int):
#           number of kernels to create, default to 100.
#        kid_prefix (str):
#           prefix string for kernel id


#     Returns:
#        N/A


#     """

#     perf = dist_params['mean']
#     sigma = dist_params['std']
#     rvs = numpy.random.normal(perf, sigma, size*2)
#     rvs_positive = [ rv for rv in rvs if rv > 0][:size]
#     rvs = rvs_positive

#     probs = scipy.stats.norm.pdf(rvs, perf, sigma)
#     ids = numpy.arange(size)
#     kernels = ['_gen_%s_%03d' % (kid_prefix, idx) for idx in xrange(size)]

#     root = etree.Element('kernels')
#     for kernel,perf,prob in zip(kernels, rvs, probs):
#         k_root = etree.SubElement(root, 'kernel')
#         k_root.set('name', kernel)

#         fpga_root = etree.SubElement(k_root, 'fpga')
#         fpga_root.set('perf', '%.3e'% (perf/ASIC_PERF_RATIO))

#         asic_root = etree.SubElement(k_root, 'asic')
#         asic_root.set('perf', '%.3e'% (perf))

#         ele = etree.SubElement(k_root, 'occur')
#         ele.text = '%.3e' % prob

#     tree = etree.ElementTree(root)
#     tree.write(fname, pretty_print=True)


# def load(fname='norm.cfg'):
#     cfg = configparser.RawConfigParser()
#     cfg.read(fname)
#     for sec in cfg.sections():
#         fpga_perf = float(cfg.get(sec, 'fpga_perf'))
#         asic_perf = float(cfg.get(sec, 'asic_perf'))
#         prob = float(cfg.get(sec, 'occur'))
#         kernel_pool[sec] = {
#                 'FPGA': KernelParam(perf=fpga_perf),
#                 'ASIC': KernelParam(perf=asic_perf),
#                 'occur': prob
#                 }

#     return sorted(cfg.sections())

# def reg_kernels(kernels):
#     """
#     Add kernels to kernel dict

#     Args:
#        kernels (dict):
#           dict to kernels

#     Return:
#        N/A
#     """
#     kernel_pool.update(kernels)

# def load_xml(fname='norm.xml'):
#     """
#     Load kernels from an XML file. Also update the global kernel pool
#     (kernel_pool). If a kernel with the same name has already been loaded into
#     the global kernel pool, it will be overide with the new one.

#     Args:
#        fname (str):
#           The file to be loaded

#     Returns:
#        kernels (list):
#           A sorted (by name) list of kernels that have been loaded.
#     """
#     tree = etree.parse(fname)
#     kernels = []
#     for k_root in tree.iter('kernel'):
#         k_name = k_root.get('name')
#         kernels.append(k_name)

#         kernel_pool[k_name] = dict()
#         accelerator_root = k_root.find('accelerator')
#         for ele in accelerator_root.getchildren():
#             uid = ele.tag
#             perf = float(ele.get('perf'))
#             kernel_pool[k_name][uid] = KernelParam(perf=perf)

#         ele = k_root.find('occur')
#         prob = float(ele.text)


#         kernel_pool[k_name]['occur'] = prob

#     return sorted(kernels)


# def load_kernels(fname='norm.xml'):
#     """Load kernels from an XML file.

#     Args:
#        fname (filepath):
#           The file to be loaded, in XML format

#     Returns:
#        kernels (dict):
#           A dict of (kernel_name, kernel_object) pair, indexed by kernel's name.

#     Raises:
#         KernelError: if parameters is not float
#     """
#     tree = etree.parse(fname)
#     kernels = dict()
#     for k_root in tree.iter('kernel'):
#         k_name = k_root.get('name')
#         k = Kernel(k_name)

#         accelerator_root = k_root.find('accelerator')
#         for ele in accelerator_root.getchildren():
#             acc_id = ele.tag
#             kernel_param = KernelParam()
#             for attr, val in ele.items():
#                 try:
#                     setattr(kernel_param, attr, float(val))
#                 except (ValueError, TypeError):
#                     raise KernelError(
#                         'Error decoding Ucore parameters, attr: {0}, val: {1}, '
#                         'val is not a float')
#             k.add_acc(acc_id, kernel_param)

#         kernels[k_name] = k
#     return kernels


# def do_test():
#     params = {'mean': 80,
#             'std': 10}
#     #create_fixednorm_xml(params, fname='ker_test.xml', size=20)
#     #create_randnorm(params, fname='ker_test.cfg', size=10)
#     #kernels = load_xml('ker_test.xml')
#     kernels = load_xml('kernels_asic_inc.xml')
#     print(kernels)
#     print(kernel_pool)
#     #for i in xrange(20):
#         #print random.gauss(6,2)
#     #rvs = scipy.stats.norm.rvs(80,20,size=20)
#     #probs = scipy.stats.norm.pdf(rvs, 80,20)
#     #print rvs
#     #print probs

# def do_generate():
#     #params = {'mean': 200,
#             #'std': 35}
#     #occur = numpy.linspace(0.9, 0.1, 10)
#     #create_fixednorm_xml(params, fname='fixednorm_10.xml', size=10)
#     params = {'mean': 100,
#             'std': 25}
#     #create_fixednorm_xml(params, fname='fixednorm_fpga80x.xml', size=10)
#     create_randnorm_xml(params, size=1000, fname='config/kernels_norm20x5.xml')

# def load_from_xmlfile(fname):
#     pass


# def load_from_xml(fname='norm.xml'):
#     """Load kernels from an XML file. This is different from load_xml,
#     which is old and should be obsolete. load_from_xml expects a
#     different XML format from the previous load_xml.

#     Args:
#        fname (str):
#           The file to be loaded

#     Returns:
#        kernels (list):
#           A sorted (by name) list of kernels that have been loaded.

#     """
#     tree = etree.parse(fname)
#     kernels = dict()
#     for k_root in tree.iter('kernel'):
#         k_name = k_root.get('name')
#         k = Kernel(k_name)

#         accelerator_root = k_root.find('accelerator')
#         for ele in accelerator_root.getchildren():
#             acc_id = ele.tag
#             ucore_param = KernelParam()
#             for attr,val in ele.items():
#                 try:
#                     setattr(ucore_param, attr, float(val))
#                 except ValueError:
#                     print('(attr, val): {0}, {1}, val is not a float'.format(attr, val))
#                 except TypeError as te:
#                     print(te)

#             k.add_acc(acc_id, ucore_param)

#         kernels[k_name] = k
#     return kernels
