:: --- CLEANUP & FORMATTING ---
echo Running automatic formatters...

echo 1. Sorting imports with isort...
uv run isort .
echo.

echo 2. Formatting code with black...
uv run black .
echo.
