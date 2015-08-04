
# coding: utf-8

# In[1]:

get_ipython().magic('env LUMOS_DEBUG=heterogsys')


# In[2]:

from lumos.model.system.hetero import HeterogSysDetailed,SysConfigDetailed
from lumos.model.system.budget import Budget, Sys_L
from lumos.model.workload import load_kernels_and_apps


# In[3]:

sysconfig = SysConfigDetailed()
sysconfig.tech = 22
sysconfig.rlacc_area_ratio=0.2
#sysconfig.delay_l1 = 0
# sysconfig.budget = Budget(area=200, power=60)
ks, apps = load_kernels_and_apps('../../workloads/sirius.xml')


# In[4]:

sys = HeterogSysDetailed(sysconfig, ks)


# In[5]:

# for vdd in (500,550,600,650, 700, 750, 800):
vdd = 650
print(sys.perf(vdd, apps['synapp_0']))
print(sys.thru_core.perfnom)


# In[ ]:



