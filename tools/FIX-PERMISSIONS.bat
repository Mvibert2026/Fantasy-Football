@echo off
REM Double-click to apply both permission fixes:
REM   1. install/refresh the hook (blocks destructive commands; intercepts
REM      multi-command blocks including newline-separated ones)
REM   2. broaden command allow-rules so routine commands stop prompting

setlocal
cd /d "%~dp0.."

echo.
echo ==========================================================
echo  Claude Code permissions - full fix
echo  Folder: %CD%
echo ==========================================================

set "PY=C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo [1/3] Installing hook...
if not exist ".claude\hooks" mkdir ".claude\hooks"
if exist ".claude\hooks\block_dangerous.py" (
  copy /y ".claude\hooks\block_dangerous.py" ".claude\hooks\block_dangerous.py.bak-prev" >nul
)
copy /y "tools\block_dangerous_v2.py" ".claude\hooks\block_dangerous.py" >nul
if errorlevel 1 goto :fail
echo   done.

echo.
echo [2/3] Broadening allow rules...
"%PY%" "tools\broaden_permissions.py"
if errorlevel 1 goto :fail

echo.
echo [3/3] Testing the hook...
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
echo  SOMETHING WENT WRONG - nothing was lost.
echo  Backups end in .bak-  Send the text above to Claude.
echo ----------------------------------------------------------

:end
echo.
pause
