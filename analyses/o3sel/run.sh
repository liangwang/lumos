PYTHONPATH=$PWD/../../:$PYTHONPATH
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=large --budget=large --tech=45
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=large --budget=large --tech=32
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=large --budget=large --tech=22
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=large --budget=large --tech=16
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=medium --budget=medium --tech=45
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=medium --budget=medium --tech=32
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=medium --budget=medium --tech=22
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=medium --budget=medium --tech=16
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=small --budget=small --tech=45
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=small --budget=small --tech=32
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=small --budget=small --tech=22
python ${LUMOS_HOME}/lumos/analyses/o3sel.py --series=small --budget=small --tech=16
#python ../o3sel.py --series=large 
#python ../o3sel.py --series=medium
#python ../o3sel.py --series=small

