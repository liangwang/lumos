
from os.path import join as joinpath
import conf.misc
DATA_DIR=joinpath(conf.misc.homedir,
                    'outputs', 'analyses')
FIG_DIR=joinpath(conf.misc.homedir,
                    'outputs', 'figures')

class Analysis(object):
    name='DefaultAnalysis'

    def __init__(self):
        pass

class PerfAnalysis(Analysis):
    def __init__(self, sys_area, sys_power):

        Analysis.__init__(self)

    def analyze(self):
        pass

    def plot(self):
        pass


