#!/usr/bin/env python

from lumos import settings
import logging
from ..base import TechModelError, BaseTechModel
from . import homoTFET30nm as tfet_30nm
from . import homoTFET60nm as tfet_60nm

_logger = logging.getLogger('TFETTechModel')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)


class TFETTechModel(BaseTechModel):
    def __init__(self, variant):
        if variant == 'homo30nm':
            tech = tfet_30nm
        elif variant == 'homo60nm':
            tech = tfet_60nm
        else:
            raise TechModelError('TFET tech model does not have the variant: {0}'.format(variant))

        super(TFETTechModel, self).__init__('tfet', variant, tech)
