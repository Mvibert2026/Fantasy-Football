@echo off
REM Double-click to install the updated PreToolUse hook.
REM Adds: chained-command (&& ; ||) interception, and quoted-span stripping
REM so commit messages that merely MENTION a blocked term no longer trip it.

setlocal
cd /d "%~dp0.."

echo.
echo ==========================================================
echo  Updating .claude\hooks\block_dangerous.py
echo  Folder: %CD%
echo ==========================================================
echo.

if not exist ".claude\hooks" mkdir ".claude\hooks"

if exist ".claude\hooks\block_dangerous.py" (
  copy /y ".claude\hooks\block_dangerous.py" ".claude\hooks\block_dangerous.py.bak-v1" >nul
  echo Backed up previous hook to block_dangerous.py.bak-v1
)

copy /y "tools\block_dangerous_v2.py" ".claude\hooks\block_dangerous.py" >nul
if errorlevel 1 goto :fail

set "PY=C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo Self-test:
echo.
"%PY%" "tools\test_hook.py"
if errorlevel 1 goto :fail

echo.
echo ----------------------------------------------------------
echo  DONE. Quit Claude Code completely and reopen it.
echo ----------------------------------------------------------
goto :end

:fail
echo.
echo ----------------------------------------------------------
echo  SOMETHING WENT WRONG. Previous hook is at
echo  .claude\hooks\block_dangerous.py.bak-v1
echo ----------------------------------------------------------

:end
echo.
pause
