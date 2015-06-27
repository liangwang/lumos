#!/usr/bin/env python

from lumos import settings
import logging
from ..base import TechModelError, BaseTechModel
from . import hp as cmos_hp
from . import lp as cmos_lp

_logger = logging.getLogger('CMOSTechModel')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)


class CMOSTechModel(BaseTechModel):
    def __init__(self, variant):
        if variant == 'hp':
            tech = cmos_hp
        elif variant == 'lp':
            tech = cmos_lp
        else:
            raise TechModelError('CMOS tech model does not have variant of: {0}'.format(variant))

        super(CMOSTechModel, self).__init__('cmos', variant, tech)
