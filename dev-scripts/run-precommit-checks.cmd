@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  Run Code Quality & Test Suite
:: ============================================================================
::  This script runs linters, formatters (in check-only mode), and the
::  test suite to ensure code quality before a commit. It does not make
::  any changes to the files.
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

echo Ensuring dependencies are up-to-date...
uv sync --all-extras >nul
echo.

:: --- CHECK EXECUTION ---
set "CHECKS_FAILED=0"

:: Define a subroutine to run a check
goto:run_checks

:run_check
    echo.
    echo ============================================================================
    echo Running: %~1
    echo ============================================================================
    %~2
    if !errorlevel! neq 0 (
        echo.
        echo ^> CHECK FAILED: %~1. %~3
        set "CHECKS_FAILED=1"
    ) else (
        echo.
        echo ^> CHECK PASSED: %~1.
    )
    goto:eof

:run_checks
    call:run_check "isort" "uv run isort --check-only --diff ." "Imports are not sorted. Run 'scripts\run-cleanup.cmd'."
    call:run_check "black" "uv run black --check --diff ." "Code is not formatted. Run 'scripts\run-cleanup.cmd'."
    call:run_check "flake8" "uv run flake8 src" "Linting errors found. Please fix them."
    call:run_check "mypy" "uv run mypy ." "Type checking errors found. Please fix them."

    echo.
    echo ============================================================================
    echo FINAL CHECK SUMMARY
    echo ============================================================================
    if %CHECKS_FAILED%==1 (
        echo Some code quality checks failed. Please review the output above.
        exit /b 1
    )

    echo All code quality checks passed. Proceeding to tests...
    echo.

    call:run_check "pytest" "uv run pytest" "Tests failed. Please review the output above and fix the issues."

    echo.
    echo ============================================================================
    echo FINAL STATUS
    echo ============================================================================
    if %CHECKS_FAILED%==1 (
        echo One or more steps failed.
        exit /b 1
    )

echo All checks and tests passed successfully!
endlocal
exit /b 0
