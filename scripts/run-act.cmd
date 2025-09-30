@echo off
setlocal enabledelayedexpansion

:: This script runs the GitHub Actions workflow locally using 'act'.
:: It targets the currently checked-out Git branch and uses the local files
:: without pulling any remote changes.

echo --- Local CI Runner using act ---

:: 1. Check if 'act' is installed
where act >nul 2>nul
if %errorlevel% neq 0 (
    echo 'act' CLI not found in your PATH.
    echo Please run the 'install-act.cmd' script first or install it manually.
    exit /b 1
)

:: 2. Get the current Git branch name
echo Detecting current Git branch...
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set "CURRENT_BRANCH=%%i"

if not defined CURRENT_BRANCH (
    echo Could not determine the current Git branch.
    echo Make sure you are inside a Git repository.
    exit /b 1
)
echo Running on branch: %CURRENT_BRANCH%
echo.

:: 3. Define cache and artifact directories to keep the root directory clean
set "ACT_CACHE_DIR=%~dp0.act-cache"
set "ACT_ARTIFACT_DIR=%~dp0.act-artifacts"
mkdir "%ACT_CACHE_DIR%" >nul 2>nul
mkdir "%ACT_ARTIFACT_DIR%" >nul 2>nul

echo Caching enabled at: %ACT_CACHE_DIR%
echo Artifacts will be stored in: %ACT_ARTIFACT_DIR%
echo.

:: 4. Run 'act'
:: --no-pull: Uses local files and doesn't fetch Docker images.
:: --branch: Specifies the branch name to simulate the event for.
:: --container-architecture native: Ensures it runs on your machine's architecture.
:: --artifact-server-path: Redirects artifacts to a local folder.
:: --cache-server-path: Redirects cache to a local folder.
:: Note: 'act' automatically discovers workflows in the standard '.github/workflows' directory.
:: If your 'ci.yml' is elsewhere, you need the '-W <path>' flag.

echo Starting act...
act push --branch %CURRENT_BRANCH% --no-pull --container-architecture native --artifact-server-path "%ACT_ARTIFACT_DIR%" --cache-server-path "%ACT_CACHE_DIR%"

if !errorlevel! neq 0 (
    echo.
    echo --- ACT WORKFLOW FAILED ---
    exit /b 1
) else (
    echo.
    echo --- ACT WORKFLOW COMPLETED SUCCESSFULLY ---
)

endlocal
exit /b 0
