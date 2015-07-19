#!/bin/sh

# To create the notebook
# $ ipython profile create lumos
#
# Then change config in ~/.ipython/profile_lumos/ipython_notebook_config.py
# 1. Modify c.NotebookApp.notebook_dir to the $LUMOS_HOME
# 2. Modify c.NotebookApp.password as the comment suggests
# 3. Modify c.NotebookApp.port if nessesary
# 4. Modify c.NotebookApp.ip from "localhost" to "*", so that it accepts remote internet connection
# 5. Modify c.NotebookApp.certfile to the real certificate


export PYTHONPATH=$(pwd):$PYTHONPATH
ipython notebook --profile=lumos
