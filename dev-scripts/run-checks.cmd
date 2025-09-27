:: ********* BEGIN REMARKS *********
:: This script is NOT an actual pre-commit hook.
:: its a helper to run `isort`, `black`, flake8`, and `mypy` on all staged files before any commit.
:: ********** END REMARKS **********

@echo off
@setlocal enabledelayedexpansion

echo Starting pre-commit checks...
echo -------- SETUP --------
echo Ensuring correct virtual environment...
:: check in a virtual environment is already activated
if defined VIRTUAL_ENV (
    echo Deactivating current virtual environment %VIRTUAL_ENV% ...
    call deactivate
)
echo Virtual environment deactivated.

:: Get the directory of the script
echo Getting script directory...
set "SCRIPT_DIR=%~dp0"

:: get the folder one level up from the script directory
echo Getting repository root directory...
set "REPO_ROOT=%SCRIPT_DIR%..\"

:: Change to the repository root directory
echo Changing to repository root directory: %REPO_ROOT%
cd /d "%REPO_ROOT%"

:: activate the virtual environment
echo Activating virtual environment...
call "%REPO_ROOT%.venv\Scripts\activate.bat"

echo running `uv sync` to ensure all dependencies are installed...
uv sync
echo installing project in editable mode...
echo.
pip install -e .
echo.
echo Virtual environment activated.
echo.
echo -------- END SETUP --------
echo.
echo.
echo -------- START CHECKS --------
:: Run isort, black, flake8, and mypy on all files in the repository
echo 1. ISORT
:: if isort fails, the script will exit with a non-zero exit code
uv run isort --check-only --diff .
echo --------------------------------
if errorlevel 1 (
    echo ISORT CHECKS FAILED
    echo isort found issues. Please run 'uv run isort .' to fix them.
    exit /b 1
) else (
    echo ISORT CHECKS PASSED
)
echo --------------------------------
echo.

:: Run black checks
echo 2. BLACK
echo -------- BLACK OUTPUT --------
uv run black --check --diff .
echo --------------------------------
if errorlevel 1 (
    echo BLACK CHECKS FAILED
    echo black found issues. Please run 'uv run black .' to fix them.
) else (
    echo BLACK CHECKS PASSED
)
echo --------------------------------
echo.

:: Run flake8 checks
echo 3. FLAKE8
uv run flake8 src
echo --------------------------------
if errorlevel 1 (
    echo FLAKE8 CHECKS FAILED
    echo flake8 found issues. Please fix them.
) else (
    echo FLAKE8 CHECKS PASSED
)
echo.
echo --------------------------------

:: Run mypy checks
echo 4. MYPY
echo --------- MYPY OUTPUT ----------
uv run mypy . --verbose
echo --------------------------------
if errorlevel 1 (
    echo MYPY CHECKS FAILED
    echo mypy found issues. Please fix them.
) else (
    echo MYPY CHECKS PASSED
)
echo.
echo --------------------------------
echo.
echo.
echo -------- END CHECKS --------
echo.
echo.
if errorlevel 1 (
    echo STATUS: SOME CHECKS FAILED
    exit /b 1
) else (
    echo STATUS: ALL CODE QUALITY CHECKS PASSED
    echo RUNNING TESTS
)
echo -------- START TESTS --------
echo.
echo.
echo 5. PYTEST
echo --------- PYTEST OUTPUT ----------
uv run pytest
echo --------------------------------
if errorlevel 1 (
    echo TESTS FAILED
    echo Some tests failed. Please fix the issues above before committing.
    exit /b 1
) else (
    echo ALL TESTS PASSED
)
exit /b 0