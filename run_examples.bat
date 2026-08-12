@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0."

if defined AIGC_DIRECTOR_PYTHON (
    set "PYTHON_CMD="%AIGC_DIRECTOR_PYTHON%""
) else (
    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
    if not defined PYTHON_CMD (
        where python >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
    if not defined PYTHON_CMD (
        for %%P in (
            "%LocalAppData%\Programs\Python\Python*\python.exe"
            "%ProgramFiles%\Python*\python.exe"
            "%ProgramFiles(x86)%\Python*\python.exe"
        ) do if exist "%%~P" if not defined PYTHON_CMD set "PYTHON_CMD="%%~P""
    )
)

%PYTHON_CMD% --version >nul 2>&1
if not errorlevel 1 goto :python_ready

if defined AIGC_DIRECTOR_PYTHON goto :missing_python
set "PYTHON_CMD="
for %%P in (
    "%LocalAppData%\Programs\Python\Python*\python.exe"
    "%ProgramFiles%\Python*\python.exe"
    "%ProgramFiles(x86)%\Python*\python.exe"
) do if exist "%%~P" if not defined PYTHON_CMD set "PYTHON_CMD="%%~P""
if not defined PYTHON_CMD goto :missing_python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 goto :missing_python

:python_ready

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
echo === Validate Skill workflow handoff ===
%PYTHON_CMD% -m aigc_director_kit validate-workflow examples\skill_workflow_case.json --library examples\action_library.json
if errorlevel 1 goto :failed

echo.
echo === Validate prompt pack ===
%PYTHON_CMD% -m aigc_director_kit validate-prompt-pack examples\prompt_pack_case.json --plan examples\one_take_previs_case.json
if errorlevel 1 goto :failed

echo.
echo === Validate QC evidence boundary ===
%PYTHON_CMD% -m aigc_director_kit validate-qc-report examples\qc_report_unverified_case.json
if errorlevel 1 goto :failed

echo.
echo === Build runtime adapter handoff ===
%PYTHON_CMD% -m aigc_director_kit build-runtime-handoff examples\skill_workflow_case.json --library examples\action_library.json --adapter optional-runtime-adapter
if errorlevel 1 goto :failed

echo.
echo Done. The examples ran successfully.
goto :finish

:missing_python
echo Python 3.10 or newer was not found through py, python, or common install locations.
echo Install Python from https://www.python.org/downloads/windows/ and enable "Add Python to PATH".
echo Or set AIGC_DIRECTOR_PYTHON to the full path of python.exe before running this file.
goto :failed

:failed
echo.
echo The example run failed. Read the message above.
if /i not "%AIGC_DIRECTOR_NO_PAUSE%"=="1" pause
exit /b 1

:finish
if /i not "%AIGC_DIRECTOR_NO_PAUSE%"=="1" pause
exit /b 0
