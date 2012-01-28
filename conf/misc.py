
debug=False

# True: use remote simulation results 
# Flase: use local copy in 'data'
#use_remote=False
use_remote=False

from os.path import join as joinpath, expanduser
homedir=joinpath(expanduser('~'), 'projects', 'qual-remote', 'model-new')
