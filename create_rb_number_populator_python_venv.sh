#!/bin/bash
#This script should be executed in as a SU from within /home/epics/RB_num_populator/
venv="exp_db_populator_venv" # Name of the virtual environment
/usr/local/bin/python3.8 -m venv /home/epics/RB_num_populator/$venv # create virtual environment
source $venv/bin/activate # activate the virtual environment
$venv/bin/pip install -r requirements.txt # Install requirements.txt
deactivate # deactivate the virtual environment
echo "Virtual environment created"
