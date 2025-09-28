@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  Clean & Format Codebase
:: ============================================================================
::  This script formats the code using isort and black, then runs linters
::  and the test suite. It is designed to fix formatting issues automatically.
:: ============================================================================

:: --- SCRIPT SETUP ---
echo Setting up environment...
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\"
cd /d "%REPO_ROOT%"

:: Ensure the virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call "%REPO_ROOT%.venv\Scripts\activate.bat"
)

echo Ensuring dependencies are up-to-date and project is installed...
uv sync --all-extras >nul
uv pip install -e . >nul
echo.

:: --- CLEANUP & FORMATTING ---
echo Running automatic formatters...

echo 1. Sorting imports with isort...
uv run isort .
echo.

echo 2. Formatting code with black...
uv run black .
echo.

echo --- VALIDATION CHECKS ---
echo Running validation checks after formatting...

echo 3. Linting with flake8...
uv run flake8 src
if !errorlevel! neq 0 (
    echo ^> Flake8 found issues that could not be automatically fixed.
)
echo.

echo 4. Type checking with mypy...
uv run mypy .
if !errorlevel! neq 0 (
    echo ^> MyPy found type errors. Please fix them manually.
)
echo.

echo --- FINAL TESTS ---
echo All cleanup tasks have been completed
uv run pytest
if !errorlevel! neq 0 (
    echo ^> Tests failed. Please fix the issues before committing.
)
echo.
echo ============================================================================
echo All cleanup, formatting, checks, and tests have all been run.
echo ============================================================================

endlocal
exit /b 0
