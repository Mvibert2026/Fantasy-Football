@echo off
REM Wrapper invoked by Windows Scheduled Task "FantasyFootball_MFL_ADP_Daily".
REM Runs the MFL ADP ingest (src/ingest_mfl_adp.py, ADR-035) against the main
REM checkout's data/nfl.db, then commits and pushes the dated CSV archive
REM under data/adp-snapshots/ -- that CSV is the off-machine backup for rows
REM that cannot be re-fetched once a day has passed (see the module docstring
REM in src/ingest_mfl_adp.py: "the CSV is the canonical archive; the DB is a
REM queryable cache of it").
REM
REM This file is intentionally NOT under source control review discipline in
REM the same sense as application code -- it is operational glue that must
REM live in the main checkout (not an ephemeral worktree) so the scheduled
REM task keeps working across worktree creation/merge/deletion. It only ever
REM touches data/adp-snapshots/*.csv, never application source.

cd /d "C:\Users\matth\Documents\Personal\Fantasy Football"

"C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe" "C:\Users\matth\Documents\Personal\Fantasy Football\src\ingest_mfl_adp.py"
if errorlevel 1 (
    echo ingest_mfl_adp.py failed with errorlevel %ERRORLEVEL% -- skipping git commit/push
    exit /b 1
)

git add data\adp-snapshots\*.csv
git diff --cached --quiet
if %ERRORLEVEL%==0 (
    echo no new/changed CSV snapshot files to commit
    exit /b 0
)

for /f "tokens=1-3 delims=/ " %%a in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set TODAY=%%a
git commit -m "data: daily ADP snapshot CSV backfill (automated, FantasyFootball_MFL_ADP_Daily)"
if errorlevel 1 (
    echo git commit failed with errorlevel %ERRORLEVEL%
    exit /b 1
)

git push origin HEAD
if errorlevel 1 (
    echo git push failed with errorlevel %ERRORLEVEL% -- commit is local only, needs manual push
    exit /b 1
)

echo ADP snapshot task complete: ingest + CSV archive committed and pushed.
