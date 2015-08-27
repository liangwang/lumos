""" This module includes memory characterisitics for the baseline reference. Data is extracted from:
table 4 of the paper 'Dark Silicon and the End of Multicore Scaling'. """
BASELINE_L1_TECH_NODE = 22
BASELINE_L1_TECH_NAME = 'cmos'
BASELINE_L1_TECH_VARIANT = 'hp'
BASELINE_L1_DELAY = 3 
BASELINE_L1_SIZE = 65536  # 64KB

# scaled from L1 characteristics using Lumos embedded cachedb
BASELINE_L2_TECH_NODE = 22
BASELINE_L2_TECH_NAME = 'cmos'
BASELINE_L2_TECH_VARIANT = 'hp'
BASELINE_L2_DELAY = 29
BASELINE_L2_SIZE = 18874368  # 18MB

# from the paper
BASELINE_MEM_LATENCY = 426
