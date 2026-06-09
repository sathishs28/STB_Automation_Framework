@echo off
setlocal enabledelayedexpansion

rem Manual validation launcher only.
rem For automated startup prefer run_redrathub.py.
rem Determine repository root from batch file location
set REPO_ROOT=%~dp0
if "%REPO_ROOT:~-1%"=="\" set REPO_ROOT=%REPO_ROOT:~0,-1%

set HUB_DIR=%REPO_ROOT%\setup_files\IR_blaster\RedRatHub-V8.01
set HTTP_PORT=%1
if "%HTTP_PORT%"=="" set HTTP_PORT=8080

set IRDATA_FILES=
for %%D in (
  "%REPO_ROOT%\assets\ir_signals_redrat\*.xml"
  "%REPO_ROOT%\assets\ir_signals\*.xml"
) do (
  for %%F in (%%D) do (
    set IRDATA_FILES=!IRDATA_FILES! "%%~fF"
  )
)

if "%IRDATA_FILES%"=="" (
  echo No IR data XML files found in assets\ir_signals_redrat or assets\ir_signals
  exit /b 1
)

cd /d "%HUB_DIR%"

%HUB_DIR%\RedRatHub.exe --irdata %IRDATA_FILES% --httpport %HTTP_PORT%