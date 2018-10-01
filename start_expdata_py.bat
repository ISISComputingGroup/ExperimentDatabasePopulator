set MYDIREXPDATA=%~dp0

%HIDEWINDOW% h
set PYTHONUNBUFFERED=TRUE
%PYTHONW% %MYDIREXPDATA%DatabaseController\main.py
REM "C:\Instrument\Apps\Python\pythonw.exe" %MYDIREXPDATA%src\py\main.py
