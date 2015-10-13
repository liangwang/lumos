
# coding: utf-8

# In[1]:

get_ipython().magic('env LUMOS_DEBUG=heterogsys')


# In[2]:

import sys
sys.path.append('/if10/lw2aw/projects/lumos/lumos-dev')


# In[3]:

from lumos.model.system.hetero import HeterogSysDetailed,SysConfigDetailed
from lumos.model.system.budget import Budget, Sys_L
from lumos.model.workload import load_kernels_and_apps


# In[4]:

sysconfig = SysConfigDetailed()
sysconfig.tech = 22
sysconfig.rlacc_area_ratio=0.2
sysconfig.add_asacc('regex', 'asic_5x', 0.03) # regex should be accelerated by FPGA
sysconfig.add_asacc('fd', 'asic_10x', 0.03) # fd should be accelerated by ASIC
#sysconfig.delay_l1 = 0
# sysconfig.budget = Budget(area=200, power=60)
ks, apps = load_kernels_and_apps('../../workloads/sirius_synapp_nonkernel0.01.xml')


# In[5]:

sys = HeterogSysDetailed(sysconfig, ks)


# In[6]:

# for vdd in (500,550,600,650, 700, 750, 800):
vdd = 650
print(sys.perf(vdd, apps['app_0']))
print(sys.thru_core.perfnom)


# In[ ]:



