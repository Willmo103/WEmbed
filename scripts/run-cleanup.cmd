:: This script is a helper to sync the project, run checks, and clean up the environment.
:: It is intended to be run from the command line.


:: uv clean
:: echo Cleanup completed.
uv sync
echo installing project in editable mode...
uv pip install -e .

echo running isort to format imports...
uv run isort .
echo.

echo running black to format code...
uv run black .
echo.

echo running flake8 to check code style...
uv run flake8 src
echo.

echo running mypy to check types...
uv run mypy src --verbose
echo.

echo All checks and cleanup completed.
echo.

echo -------- END CLEANUP --------
echo.

echo Running `pytest` to execute tests...
uv run pytest
echo.
echo -------- END TESTS --------

exit /b 0