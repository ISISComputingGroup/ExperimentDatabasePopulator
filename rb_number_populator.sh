#!/bin/bash
venv="exp_db_populator_venv" # Name of the virtual environment

. /home/epics/EPICS/config_env.sh
source /home/epics/RB_num_populator/$venv/bin/activate # activate the virtual environment
$venv/bin/python3.8 /home/epics/RB_num_populator/main.py
deactivate # deactivate the virtual environment
