@echo off
:: --- CLEANUP & FORMATTING ---
echo Running automatic formatters...

echo 1. Sorting imports with isort...
uv run isort . --profile black --line-length 88
echo.

echo 2. Formatting code with black...
uv run black .
echo.

echo 3. Linting code with flake8...
uv run flake8 src --count --statistics
echo.

echo Formatters done.
