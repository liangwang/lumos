#!/usr/bin/env python

from lxml import etree
import argparse
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--input-xmlfile', '-i', required=True)
parser.add_argument('--output-xmlfile', '-o', required=True)
parser.add_argument('--rc-count', required=True)
parser.add_argument('--rc-time', required=True)
args = parser.parse_args()

_file_description_ = """
Add reconfiguration overhead to kernels by {scriptname}

- Generated from {0}
- rc count: {1}
- rc time: {2}
- Generated at: {time:%H:%M:%S, %Y-%m-%d}
""".format(args.input_xmlfile,
           args.rc_count,
           args.rc_time,
           time=datetime.now(),
           scriptname=__file__)

xmlparser = etree.XMLParser(remove_blank_text=True)
root = etree.parse(args.input_xmlfile, xmlparser)
root.getroot().insert(0, etree.Comment(_file_description_))
apps_root = root.find('apps')
for app in apps_root:
    kernels = app.find('kernel_config')
    for k in kernels:
        name = k.get('name')
        if name == 'coreonly':
            continue
        k.set('rc_time', args.rc_time)
        k.set('rc_count', args.rc_count)

root.write(args.output_xmlfile, pretty_print=True)

