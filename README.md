
# Experiment Database Populator

The experiment database populator is a Python 3.8 program that is designed to run centrally and periodically update instrument databases.

The Experiment Database Populator runs on [Control SVCS](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/control-svcs) using credentials found in the usual place.

The repository on control-svcs is located under: `/home/epics/RB_num_populator`

The populator is executed hourly by a cron job.

Logs are outputed hourly to `/home/epics/RB_number_populator/logs`.

Output from the cron job, which will show if the program is not working are written to `/tmp/rb_num_pop.out`.

See [HERE](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Experimental-Database#deployment) for more information inside the WIKI.
