@echo off
echo Building Windows executable using .spec file...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build using spec file
echo.
echo Creating executable...
pyinstaller pdf_compressor.spec

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable is in the 'dist' folder: dist\PDF Compressor.exe
echo.
pause

