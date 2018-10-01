REM @echo off
set MYDIREXPDB=%~dp0

set CYGWIN=nodosfilewarning
call %MYDIREXPDB%..\..\..\config_env_base.bat

set EPICS_CAS_INTF_ADDR_LIST=127.0.0.1
set EPICS_CAS_BEACON_ADDR_LIST=127.255.255.255

set IOCLOGROOT=%ICPVARDIR%/logs/ioc
for /F "usebackq" %%I in (`cygpath %IOCLOGROOT%`) do SET IOCCYGLOGROOT=%%I

set EXPDB_CONSOLEPORT=9010

@echo Starting Experimental Data Application (console port %EXPDB_CONSOLEPORT%)
set EXPDB_CMD=%MYDIREXPDB%start_expdata_py.bat

REM Unlike IOC we are not using "--noautorestart --wait" so gateway will start immediately and also automatically restart on exit

%ICPTOOLS%\cygwin_bin\procServ.exe --logstamp --logfile="%IOCCYGLOGROOT%/EXPDB-%%Y%%m%%d.log" --timefmt="%%c" --restrict --ignore="^D^C" --name=EXPDB --pidfile="/cygdrive/c/windows/temp/EPICS_EXPDB.pid" %EXPDB_CONSOLEPORT% %EXPDB_CMD%
