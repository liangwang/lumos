#!/usr/bin/env python

from lumos import settings
import logging
from ..base import TechModelError, BaseTechModel
from . import hp as finfet_hp
from . import lstp as finfet_lp

_logger = logging.getLogger('FinFETTechModel')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)


class FinFETTechModel(BaseTechModel):
    def __init__(self, variant):
        if variant == 'hp':
            tech = finfet_hp
        elif variant == 'lp':
            tech = finfet_lp
        else:
            raise TechModelError('FinFET model does not have the variant: {0}'.format(variant))

        super(FinFETTechModel, self).__init__('finfet', variant, tech)
