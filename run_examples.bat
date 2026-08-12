@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0."

if defined AIGC_DIRECTOR_PYTHON (
    set "PYTHON_CMD=%AIGC_DIRECTOR_PYTHON%"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        set "PYTHON_CMD=python"
    )
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 goto :missing_python

set "PYTHONPATH=%CD%\src"

echo === Validate shot plan ===
%PYTHON_CMD% -m aigc_director_kit validate-plan examples\shot_plan.json
if errorlevel 1 goto :failed

echo.
echo === Search action catalog ===
%PYTHON_CMD% -m aigc_director_kit list-actions --library examples\action_library.json --query run
if errorlevel 1 goto :failed

echo.
echo === Compile bounded action request ===
%PYTHON_CMD% -m aigc_director_kit compile-action --library examples\action_library.json --text "run quick stop, blend 0.2s, fast, in place"
if errorlevel 1 goto :failed

echo.
echo Done. The examples ran successfully.
goto :finish

:missing_python
echo Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/windows/ and run this file again.
goto :failed

:failed
echo.
echo The example run failed. Read the message above.
if /i not "%AIGC_DIRECTOR_NO_PAUSE%"=="1" pause
exit /b 1

:finish
if /i not "%AIGC_DIRECTOR_NO_PAUSE%"=="1" pause
exit /b 0
