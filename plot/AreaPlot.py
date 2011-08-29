'''
Created on Aug 12, 2011

@author: lw2aw
'''

from Plot import Matplot
from model import System2
import matplotlib.pyplot as plt
from os.path import join as joinpath

class AreaPlot(Matplot):
    '''
    Maximum speedup scaled to area
    '''


    def __init__(self, power, prefix='area'):
        '''
        Constructor
        '''
        