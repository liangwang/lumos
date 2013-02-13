import os

try:
    LUMOS_DEBUG=os.environ['LUMOS_DEBUG']
except KeyError:
    LUMOS_DEBUG=False

# True: use remote simulation results
# Flase: use local copy in 'data'
try:
    LUMOS_USE_REMOTE=os.environ['LUMOS_USE_REMOTE']
except KeyError:
    LUMOS_USE_REMOTE=False

try:
    LUMOS_HOME=os.environ['LUMOS_HOME']
except KeyError:
    LUMOS_HOME=os.getcwd()

try:
    LUMOS_ANALYSIS_DIR = os.environ['LUMOS_ANALYSIS_DIR']
except KeyError:
    LUMOS_ANALYSIS_DIR = os.path.join(LUMOS_HOME, 'analyses')

LUMOS_SIM_CIRCUIT = 'adder32'
