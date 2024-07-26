@echo off
setlocal enabledelayedexpansion

REM Iterate over all .py files in migrations directories
for /r %%F in (*.py) do (
    set "file=%%F"
    REM Check if the file is in a "migrations" directory and is not named "__init__.py"
    if "!file!"=="!file:\migrations\=!" (
        rem do nothing
    ) else (
        if /i not "!file:~-10!"=="__init__.py" (
            echo Deleting !file!
            del "!file!"
        )
    )
)

REM Iterate over all .pyc files in migrations directories
for /r %%F in (*.pyc) do (
    set "file=%%F"
    REM Check if the file is in a "migrations" directory
    if "!file!"=="!file:\migrations\=!" (
        rem do nothing
    ) else (
        echo Deleting !file!
        del "!file!"
    )
)
