
# coding: utf-8

# # Analysis Setup

# In[1]:

get_ipython().magic('matplotlib inline')
import pandas as pd
import matplotlib.pyplot as plt

#pd.set_option('display.mpl_style', 'default') # Make the graphs a bit prettier
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['font.size'] = 14.0
plt.rcParams['lines.linewidth'] = 2.0


# In[2]:

df = pd.read_csv('syn.csv', index_col=0)
def plot_data(df, legend, sel_vec, x='vdd', y='speedup'):
    query_str = '&'.join(['{0}=={1}'.format(k, v) for k,v in sel_vec.items()])
    df2 = df.query(query_str)
    df2_pivot = df2.pivot(index=x, columns=legend, values=y)
    df2_pivot.plot()


# # Parameter Choices
# 
# The range of the following parameters are application-dependent, and are extracted from PARSEC profiling:
# 
# - **L1 miss rate (4)**: 0.005, 0.01, 0.05, 0.1
# - **L2 miss list (6)**: 0.01, 0.05, 0.1, 0.2, 0.5, 0.6
# - **Ratio of memory insts. (8)**: 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3, 0.32
# - **L2 latency parameter alpha (4)**: 0.5, 1.0, 1.5, 2.0
# - **CPI (7)**: 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1
# 
# The range of the following parameters are system-related, and chosen based on common knowledge:
# 
# - **Vdd (7)**: 500, 550, 600, 650, 700, 750, 800
# - **System area (3)**: 200, 150, 100
# - **System power (3)**: 120, 90, 60

# # Ratio of memory instructions

# In[3]:

sel_vec = {
    'area':200, 
    'power': 60, 
    'alpha': 1, 
    'cpi': 0.9, 
    'l1m': 0.1, 
    'l2m': 0.1}
plot_data(df, 'rm', sel_vec)


# # Sensitivy to Power Budget

# In[4]:

sel_vec = {
    'area':200, 
    'rm': 0.18, 
    'alpha': 1, 
    'cpi': 0.9, 
    'l1m': 0.1, 
    'l2m': 0.1}
plot_data(df, 'power', sel_vec)


# # Sensitivity to Area budget

# In[5]:

sel_vec = {
    'power':90, 
    'rm': 0.18, 
    'alpha': 1, 
    'cpi': 0.9, 
    'l1m': 0.1, 
    'l2m': 0.1}
plot_data(df, 'area', sel_vec)


# # Sensitivity to LLC cache latency parameter (alpha)

# In[6]:

sel_vec = {
    'power':90, 
    'rm': 0.18, 
    'area': 200, 
    'cpi': 0.9, 
    'l1m': 0.1, 
    'l2m': 0.1}
plot_data(df, 'alpha', sel_vec)


# # CPI

# In[7]:

sel_vec = {
    'power':90, 
    'rm': 0.18, 
    'area': 200, 
    'alpha': 1.0, 
    'l1m': 0.1, 
    'l2m': 0.1}
plot_data(df, 'cpi', sel_vec)


# # L1 miss rate

# In[8]:

sel_vec = {
    'power':90, 
    'rm': 0.18, 
    'area': 200, 
    'alpha': 1.0, 
    'cpi': 1, 
    'l2m': 0.1}
plot_data(df, 'l1m', sel_vec)


# # LLC miss rate

# In[9]:

sel_vec = {
    'power':90, 
    'rm': 0.18, 
    'area': 200, 
    'alpha': 1.0, 
    'cpi': 1, 
    'l1m': 0.05}
plot_data(df, 'l2m', sel_vec)

