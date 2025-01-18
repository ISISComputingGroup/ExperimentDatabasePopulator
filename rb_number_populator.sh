#!/bin/bash
venv="exp_db_populator_venv" # Name of the virtual environment

. /home/epics/EPICS/config_env.sh
source /home/epics/RB_num_populator/$venv/bin/activate # activate the virtual environment
exp_db_populator
deactivate # deactivate the virtual environment
