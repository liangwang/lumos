#!/usr/bin/env python

import os
from math import fabs
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
    """Create directories for an analysis.

    Parameters
    ----------
    anl_name: str
      The name of an analysis.

    Returns
    -------
    fdir, ddir: path
      a pair of directories for figures (fdir) and data (ddir).
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


def approx_equal(a, b, tol=1e-9):
    """Test equivalence of two float numbers

    Parameters
    ----------
    a, b: float
      The two float numbers to be compared
    tol: float
      The tolerance factor, default is 1e-9

    Returns
    -------
    bool:
      True if the two numbers are approximately equal, False otherwise.
    """
    return fabs(a-b) <= max(fabs(a), fabs(b)) * tol
