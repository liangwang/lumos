#!/usr/bin/env python

import random
from lxml import etree
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--napps', type=int, help='number of apps to generate', required=True)
parser.add_argument('--non-kernel', type=int, help='non-kernel portion in permille', default=0)
parser.add_argument('--kernels', help='kernels used to generate apps, None (default) if all kernels are used')
# parser.add_argument('--precision', type=int, default=3, help='number of significant digits for precision')
parser.add_argument('-o', '--output-file', default='sirius_synthetic.xml', help='output workload in XML file')
args = parser.parse_args()

if not args.kernels:
    kernels = ['fe','fd','stemmer','crf','dnn-asr','gmm','regex','coreonly']
else:
    kernels = args.kernels.split(',')
nkernels = len(kernels)
if nkernels <= 1:
    print('number of kernels should be at least 2')
    sys.exit(1)

root = etree.Element('workload')
# without this parser tweak, pretty print won't work
parser = etree.XMLParser(remove_blank_text=True)
root.append(etree.parse('sirius.xml', parser).find('kernels'))
app_root = etree.SubElement(root, 'apps', type='synthetic')


args.precision = 3
randrange_min = 0
randrange_max = 10**args.precision - args.non_kernel
for n in range(args.napps):
    rand_indexes = sorted([ random.randrange(randrange_min, randrange_max) for _ in range(nkernels-1)])
    rand_indexes.insert(0, 0)
    rand_indexes.append(randrange_max)
    app = etree.SubElement(app_root, 'app', name='app_{0}'.format(n))
    kernel_config = etree.SubElement(app, 'kernel_config')
    for idx, k_ in enumerate(kernels):
        cov = (rand_indexes[idx+1] - rand_indexes[idx]) / 10**args.precision
        etree.SubElement(kernel_config, 'kernel', name=k_, cov='{0:.{width}f}'.format(cov, width=args.precision))

tree = etree.ElementTree(root)
tree.write(args.output_file, pretty_print=True)
