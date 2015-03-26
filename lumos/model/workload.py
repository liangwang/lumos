#!/usr/bin/env python
import logging
from . import application
# from .application import App
from .application import Application
from . import kernel
import scipy.stats
# import ConfigParser
# import xml.etree.ElementTree as ET
from lxml import etree


def build_with_single_kernel(kernels, cov_params):
    workload = []

    app_num = len(kernels)
    name_idx_len = app_num % 10
    for kernel,app_idx in zip(kernels, xrange(app_num)):
        cov = application.random_kernel_cov(cov_params)
        app_name = '%0*d' % (name_idx_len, app_idx)
        app = application.build_single(cov, kernel, name=app_name)
        workload.append(app)

    return workload


def build(app_num, kernels, cov_dist, cov_param1, cov_param2):
    """
    Build a workload composed of applications with the specified
    kernels coverage following a specified distribution.

    Args:
       app_num (int):
          The number of applications in a workload.
       kernels (list):
          The list of kernel IDs.
       cov_dist (str):
          The distribution type of coverage, currently supports *normal*,
          *lognormal*, *uniform*.
       cov_param1,cov_param2 (number):
          The statistical parameters for the distribution. Their real meanings
          depend on the specific distribution. For *normal* and *lognormal*,
          param1 is the mean, and param2 is the standard deviation. For *uniform*,
          param1 is the minimum range, and param2 is the maximum range.

    Returns:
       workload (list):
          A list of successfully built applications.

    """
    workload = []

    probs = [ kernel.kernel_pool[kid]['occur'] for kid in kernels ]
    kernel_occ_probs = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]

    app_idx = 0
    for occ in zip(*kernel_occ_probs):
        if occ.count(1) > 0:
            cov = application.random_uc_cov(cov_dist, cov_param1, cov_param2)
            app_name = 'app%d' % app_idx
            app_idx = app_idx + 1
            app = application.build(cov, occ, probs, kernels, name=app_name)
            workload.append(app)

    return workload


def build_fixedcov(app_num, kernels, cov):
    """
    Build a workload composed of applications each of which includes a
    kernel with the given coverage. The selection of a kernel for an
    application follows the occur probability of that kernel.

    Args:
       app_num (int):
          The number of applications in a workload.
       kernels (list):
          The list of kernel IDs.
       cov (num):
          The fixed coverage for each kernel once it presents in an
          application, e.g. 0.4

    Returns:
       workload (list):
          A list of successfully built applications.

    """

    workload = []

    probs = [ kernel.kernel_pool[kid]['occur'] for kid in kernels ]
    kernel_occ_probs = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]

    app_idx = 0
    for occ in zip(*kernel_occ_probs):
        if occ.count(1) > 0:
            app_name = 'app%d' % app_idx
            app_idx = app_idx + 1
            app = application.build(cov, occ, probs, kernels, name=app_name)
            workload.append(app)

    return workload


# def dump(workload, fname='workload.cfg'):
#     """Dump workload into a file

#     :workload: @todo
#     :fname: @todo
#     :returns: @todo

#     """
#     cfg = ConfigParser.RawConfigParser()
#     app_num = len(workload)
#     for idx in xrange(app_num):
#         app = workload[idx]
#         cfg.add_section(app.name)
#         kernels = app.kernels
#         kernel_config = ','.join( [ '%s:%.3e' % (kid, kernels[kid]) for kid in kernels] )
#         cfg.set(app.name, 'f_parallel', app.f)
#         cfg.set(app.name, 'kernel_config', kernel_config)

#     with open(fname, 'wb') as f:
#         cfg.write(f)


def dump_xml(workload, fname='workload.xml'):
    root = etree.Element('workload')
    for app in workload:
        app_root = etree.SubElement(root, 'app')
        app_root.set('name', app.name)

        ele_fparallel = etree.SubElement(app_root, 'f_parallel')
        ele_fparallel.text = '%.3e' % app.f

        ele_kcfg = etree.SubElement(app_root, 'kernel_config')
        kernels = app.kernels
        for k in kernels:
            ele_k = etree.SubElement(ele_kcfg, 'kernel')
            ele_k.set('name', k)
            ele_k.set('cov', '%.3e'%kernels[k])


    tree = etree.ElementTree(root)
    tree.write(fname, pretty_print=True)

# def load(fname='workload.cfg'):
#     cfg = ConfigParser.RawConfigParser()
#     cfg.read(fname)
#     worklord = []
#     for sec in cfg.sections():
#         app_name = sec
#         app_f = float(cfg.get(sec, 'f_parallel'))
#         app = App(f=app_f, name=app_name)
#         kernel_config = cfg.get(sec, 'kernel_config')
#         for kcfg in kernel_config.split(','):
#             kcfg_tmp = kcfg.split(':')
#             kid = kcfg_tmp[0]
#             cov = float(kcfg_tmp[1])
#             app.reg_kernel(kid, cov)
#             workload.append(app)

#     return workload


def load_from_xml(kernels, fname='workload.xml'):
    """Load a workload (a set of applications) from an XML file

    Args:
       fname (filepath):
          The XML file to be loaded

    Returns:
       workload (dict):
          A dict of applications this workload contains, indexed by application name
    """
    workload = dict()
    tree = etree.parse(fname)
    for app_root in tree.iter('app'):
        app_name = app_root.get('name')

        ele = app_root.find('f_parallel')
        f_parallel = float(ele.text)
        app = Application(f=f_parallel, name=app_name)

        kcfg_root = app_root.find('kernel_config')
        for k_ele in kcfg_root.iter('kernel'):
            kid = k_ele.get('name')
            kernel = kernels[kid]
            cov = float(k_ele.get('cov'))
            app.add_kernel(kernel, cov)

        workload[app_name] = app

    return workload


def load_workload(kernels, fname='workload.xml'):
    """
    Load a workload from an XML file

    Args:
       fname (str):
          The XML file to be loaded

    Returns:
       workload (dict):
          A dict of applications this workload contains, indexed by application name
    """
    workload = dict()
    tree = etree.parse(fname)
    for app_root in tree.iter('app'):
        app_name = app_root.get('name')

        ele = app_root.find('f_parallel')
        f_parallel = float(ele.text)
        app = Application(f=f_parallel, name=app_name)

        kcfg_root = app_root.find('kernel_config')
        for k_ele in kcfg_root.iter('kernel'):
            kid = k_ele.get('name')
            kernel = kernels[kid]
            cov = float(k_ele.get('cov'))
            app.add_kernel(kernel, cov)

        workload[app_name] = app

    return workload


# def load_xml(fname='workload.xml'):
#     """
#     Load a workload from an XML file

#     Args:
#        fname (str):
#           The XML file to be loaded

#     Returns:
#        workload (list):
#           A list of applications this workload contains.
#     """
#     workload = []
#     tree = etree.parse(fname)
#     for app_root in tree.iter('app'):
#         app_name = app_root.get('name')

#         ele = app_root.find('f_parallel')
#         f_parallel = float(ele.text)
#         app = App(f=f_parallel, name=app_name)

#         kcfg_root = app_root.find('kernel_config')
#         for k_ele in kcfg_root.iter('kernel'):
#             kid = k_ele.get('name')
#             cov = float(k_ele.get('cov'))
#             app.reg_kernel(kid, cov)

#         workload.append(app)

#     return workload

def add_fixedcov(workload_from, kernels, fixedcov, workload_to):
    if 'fixedcov' not in kernels:
        logging.error("can not find the kernel to have fixed coverage")

    workload = load_xml(workload_from)

    for app in workload:
        app.reg_kernel('fixedcov', fixedcov*0.01)

    dump_xml(workload, workload_to)


if __name__ == '__main__':
    import kernel
    #kernels = kernel.load_xml('config/fixednorm_10.xml')
    #workload = build(10, kernels, 'norm', 0.4, 0.1)
    #dump_xml(workload, fname='workload_test.xml')

    kernels = kernel.load_xml('analyses/asicopt/kernels_norm40x10_fixed40.xml')
    add_fixedcov(workload_from='workload_fpga40x_cov40.xml', kernels=kernels,
            fixedcov=40, workload_to='analyses/asicopt/workload_fixed40_norm40x10_cov40.xml')
    #cov_dist_params = {'dist': 'norm',
            #'mean': 0.4, 'std': 0.1}
    #workload = build_with_single_kernel(kernels, cov_dist_params)
    #dump_xml(workload, fname='config/workload_norm80x20_cov40x10.xml')
    #kernels = kernel.load_xml('analyses/asicopt/kernels_norm40x10.xml')
    #workload = build_fixedcov(500, kernels, 0.5)
    #dump_xml(workload, fname='workload_fpga40x_cov50.xml')
    #workload = build_fixedcov(500, kernels, 0.7)
    #dump_xml(workload, fname='workload_fpga40x_cov70.xml')
    #workload = build_fixedcov(500, kernels, 0.3)
    #dump_xml(workload, fname='workload_fpga40x_cov30.xml')
    #workload = build_fixedcov(500, kernels, 0.4)
    #dump_xml(workload, fname='workload_fpga40x_cov40.xml')
    #workload = load_xml()
    #dump_xml(workload, fname='workload2.xml')
