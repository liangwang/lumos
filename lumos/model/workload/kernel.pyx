#!/usr/bin/env python
# encoding: utf-8
import configparser
from lxml import etree
import logging
from lumos.settings import LUMOS_DEBUG
from lumos import BraceMessage as _bm_

__logger = None

if LUMOS_DEBUG and ('all' in LUMOS_DEBUG or 'kernel' in LUMOS_DEBUG):
    _debug_enabled = True
else:
    _debug_enabled = False

def _debug(brace_msg):
    global __logger
    if not _debug_enabled:
        return

    if not __logger:
        __logger = logging.getLogger('kernel')
        __logger.setLevel(logging.DEBUG)

    __logger.debug(brace_msg)


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

        # self.pf = parallel_factor
        # if parallel_factor:
        #     self.is_serial = True
        # else:
        #     self.is_serial = False

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
        if acc_root is not None:
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

        core_perf_root = xmltree.find('core_perf_config')
        if core_perf_root is not None:
            for ele in core_perf_root:
                if ele.tag is etree.Comment:
                    continue
                setattr(k, ele.tag, float(ele.text))
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

    def is_serial(self):
        """Whether the kernel can be accelerated via multi-core parallellization."""
        pf = getattr(self, 'pf', None)
        if not pf:
            return True
        else:
            return False

    def is_accelerable(self):
        """Whether the kernel has any accelerator associated."""
        if self._kernel_params:
            return True
        else:
            return False

    def accelerated_by(self, acc_id):
        if acc_id in self._kernel_params:
            return True
        else:
            return False

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

