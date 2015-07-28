#!/usr/bin/env python3

import itertools
from lxml import etree

root = etree.Element('workload')
app_root = etree.SubElement(root, 'apps', type='synthetic')
kernel_root = etree.SubElement(root, 'kernels')

l1_miss_list = ('0.005', '0.01', '0.05', '0.1')
l2_miss_list = ('0.01', '0.05', '0.1', '0.2', '0.5', '0.6')
rm_list = ('0.18', '0.2', '0.22', '0.24', '0.26', '0.28', '0.3', '0.32')
alpha_list = ('0.5', '1.0', '1.5', '2.0')
cpi_list = ('0.5', '0.6', '0.7', '0.8', '0.9', '1.0', '1.1') 
for l1m, l2m, rm, alpha, cpi in itertools.product(l1_miss_list, l2_miss_list, rm_list, alpha_list, cpi_list):
    appname = 'l1m{0}_l2m{1}_rm{2}_alpha{3}_cpi{4}'.format(l1m, l2m, rm, alpha, cpi) 
    app = etree.SubElement(app_root, 'app', name=appname)
    kernel = etree.SubElement(kernel_root, 'kernel', name=appname)
    kernel_config = etree.SubElement(app, 'kernel_config') 
    etree.SubElement(kernel_config, 'kernel', name=appname, cov='1')

    perf_config = etree.SubElement(kernel, 'core_perf_config')

    se = etree.SubElement(perf_config, 'cache_sz_l1_nom')
    se.text = '65536'

    se = etree.SubElement(perf_config, 'cache_sz_l2_nom')
    se.text = '18874368'

    se = etree.SubElement(perf_config, 'miss_l1')
    se.text = l1m

    se = etree.SubElement(perf_config, 'miss_l2')
    se.text = l2m

    se = etree.SubElement(perf_config, 'alpha_l1')
    se.text = '5'

    se = etree.SubElement(perf_config, 'alpha_l2')
    se.text = alpha

    se = etree.SubElement(perf_config, 'rm')
    se.text = rm

    se = etree.SubElement(perf_config, 'cpi_exe')
    se.text = cpi

    se = etree.SubElement(perf_config, 'pf')
    se.text = '1'


tree = etree.ElementTree(root)
tree.write('detailed_workload_syn.xml', pretty_print=True)
