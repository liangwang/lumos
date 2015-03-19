#!/usr/bin/env python

import os
from os.path import join as joinpath

def mk_dir(parent,  dname):
    """
    Create directory if not exist.

    :param parent: The full path to the parent diretory
    :param dname: The directory name to be created
    :rtype: The full path to the newly created directory
    """
    abspath = joinpath(parent, dname)
    try:
        os.makedirs(abspath)
    except OSError:
        if os.path.isdir(abspath):
            pass
        else:
            raise
    return abspath


def make_ws_dirs(base, anl_name):
    """
    Create directories for an analysis.

    :param anl_name: the name of an analysis
    :rtype: a directory pair for figures (*fdir*) and data (*ddir*), respectively.

    """
    ws_dir = joinpath(base, anl_name)
    fdir = mk_dir(ws_dir, 'figures')
    ddir = mk_dir(ws_dir, 'data')
    return (fdir, ddir)


def try_update(config, options, section, name):
    if config.has_option(section, name):
        if not hasattr(options, name):
            setattr(options, name, config.get(section, name))
        elif options.override:
            setattr(options, name, config.get(section, name))


def parse_bw(bw_cfg):
    cfg_striped = ''.join(bw_cfg.split())
    bw_dict = dict()
    for bw in cfg_striped.split(','):
        tmp = bw.split(':')
        t = int(tmp[0])
        v = float(tmp[1])
        bw_dict[t] = v

    return bw_dict
