#!/usr/bin/env python 

from .io_cmos import IOCore as IOCore_CMOS
from .o3_cmos import O3Core as O3Core_CMOS
from .io_tfet import IOCore as IOCore_TFET
from .o3_tfet import O3Core as O3Core_TFET
from .smallcore_finfet import SmallCore as SmallCore_FINFET
from .bigcore_finfet import BigCore as BigCore_FINFET
from .smallcore_tfet import SmallCore as SmallCore_TFET
from .bigcore_tfet import BigCore as BigCore_TFET
from .base import BaseCoreError


def get_coreclass(core_mnemonic):
    if core_mnemonic == 'io-cmos':
        return IOCore_CMOS
    elif core_mnemonic == 'io-tfet':
        return IOCore_TFET
    elif core_mnemonic == 'o3-cmos':
        return O3Core_CMOS
    elif core_mnemonic == 'o3-tfet':
        return O3Core_TFET
    elif core_mnemonic == 'small-tfet':
        return SmallCore_TFET
    elif core_mnemonic == 'small-finfet':
        return SmallCore_FINFET
    elif core_mnemonic == 'big-tfet':
        return BigCore_TFET
    elif core_mnemonic == 'big-finfet':
        return BigCore_FINFET
    else:
        raise BaseCoreError("Unknown core mnemonic: {0}".format(core_mnemonic))
