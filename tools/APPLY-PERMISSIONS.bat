@echo off
REM Double-click this file to apply the Claude Code permission configuration.
REM It only writes .claude\settings.json, .claude\settings.local.json and
REM .claude\hooks\block_dangerous.py, backing up anything it replaces.

setlocal
cd /d "%~dp0.."

echo.
echo ==========================================================
echo  Applying Claude Code permission configuration
echo  Folder: %CD%
echo ==========================================================
echo.

set "PY=C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "tools\apply_permissions_config.py"
set RC=%ERRORLEVEL%

echo.
if %RC%==0 (
  echo ----------------------------------------------------------
  echo  DONE. Now quit Claude Code completely and reopen it.
  echo  Check above for: 458 allow, 4 deny preserved
  echo                   failures: 0
  echo ----------------------------------------------------------
) else (
  echo ----------------------------------------------------------
  echo  SOMETHING WENT WRONG - exit code %RC%
  echo  Copy the text above and send it to Claude. Nothing was
  echo  lost; backups end in .bak-<timestamp>
  echo ----------------------------------------------------------
)

echo.
pause
