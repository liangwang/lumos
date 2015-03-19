#!/usr/bin/env python

import argparse
from configobj import ConfigObj
import os

def LumosNumlist(string):
    """ LumosNumlist is a number list specified in following ways:

    1. enumeration: 1,2,3,4
    2. range: 1:5 -> 1,2,3,4,5
    3. range with step: 1:5:2 -> 1,3,5
    4. a mix of the above three, the mix should keep the orders, so 1,2,3:10,12:20:2,30 is legitimate, while
       1,2,3,1:10 is not.

    """
    num_list = []
    for s in string.split(','):
        if ':' in s:
            range_params = s.split(':')
            num_params = len(range_params)
            if num_params == 2:
                start = int(range_params[0])
                end = int(range_params[1])
                step = 1
            elif num_params == 3:
                start = int(range_params[0])
                end = int(range_params[1])
                step = int(range_params[2])
            else:
                raise ValueError('Unknown range pattern {0}'.format(s))
            num_list.extend([str(x) for x in xrange(start, end+step, step)])
        else:
            try:
                dummy = int(s)
            except ValueError:
                raise ValueError('Unknown number, expect integer, but given {0}'.format(s))

            num_list.append(s)

    return num_list


class LumosArgumentParser(object):
    def __init__(self, config_dir=None, desc=None):
        if not config_dir:
            config_dir = os.getcwd()
        self._cf_parser = argparse.ArgumentParser(add_help=False)
        self._cf_parser.add_argument(
            '-c', '--config-file', metavar='FILE',
            default=os.path.join(config_dir, 'default.cfg'),
            help='configuration file, default to: %(default)s')

        cf_args, self._argv = self._cf_parser.parse_known_args()

        if os.path.isfile(cf_args.config_file):
            config = ConfigObj(cf_args.config_file, list_values=False, interpolation=False)
            self._args_defaults = config.dict()
        else:
            print('WARNING: fail to open configuration file: {0}'.format(cf_args.config_file))
            self._args_defaults = None

        description = """{0}\n

        """.format(desc)

        epilog = "NOTED: Options are passed by both command-line arguments and configuration "
        "file (specified by '-c'). Command-line arguments override configuration options "
        "if there are any conflicts."

        self._arg_parser = argparse.ArgumentParser(
            parents=[self._cf_parser], description=description, epilog=epilog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        if self._args_defaults:
            self._arg_parser.set_defaults(**self._args_defaults)

    def add_argument(self, *args, **kwargs):
        self._arg_parser.add_argument(*args, **kwargs)

    def parse_args(self):
        return self._arg_parser.parse_args(self._argv)
