
# coding: utf-8

# In[1]:

get_ipython().magic('env LUMOS_DEBUG=homogsys')


# In[2]:

from lumos.model.system.homo import HomoSysDetailed,SysConfigDetailed
from lumos.model.system.budget import Budget


# In[3]:

sysconfig = SysConfigDetailed()
#sysconfig.delay_l1 = 0
sysconfig.budget = Budget(area=200, power=60)


# In[4]:

sys = HomoSysDetailed(sysconfig)


# In[5]:

from lumos.model.workload import load_kernels_and_apps


# In[7]:

ks, apps = load_kernels_and_apps('detailed_workload_syn.xml')

for vdd in (500,550,600,650, 700, 750, 800):
    print(sys.perf(vdd, apps['l1m0.1_l2m0.5_rm0.32_alpha2.0_cpi1.1'])/sys.core.perfnom)


# In[ ]:



