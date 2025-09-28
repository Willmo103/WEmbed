@echo off
setlocal

echo Checking if 'act' is already installed...
where act >nul 2>nul
if %errorlevel% equ 0 (
    echo 'act' is already installed. No action needed.
    exit /b 0
)

echo Checking for Winget...
where winget >nul 2>nul
if %errorlevel% neq 0 (
    echo Winget not found. Please install it from the Microsoft Store or GitHub to continue.
    echo https://github.com/microsoft/winget-cli/releases
    exit /b 1
)

echo Winget found. Searching for 'nektos.act'...
winget search nektos.act | find "nektos.act" >nul
if %errorlevel% neq 0 (
    echo Could not find 'nektos.act' via Winget.
    exit /b 1
)

echo 'nektos.act' found. Attempting to install...
winget install --id nektos.act -e --source winget
if %errorlevel% neq 0 (
    echo Failed to install 'act'. Please try installing it manually.
    exit /b 1
)

echo 'act' has been installed successfully.
echo You may need to restart your terminal for the 'act' command to be available in your PATH.

endlocal
exit /b 0
