@echo off
echo Building Windows executable...
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

REM Build the executable
echo.
echo Creating executable...
pyinstaller --name="PDF Compressor" ^
    --onefile ^
    --windowed ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=pikepdf ^
    --hidden-import=fitz ^
    --hidden-import=PyMuPDF ^
    --collect-submodules=pikepdf ^
    --collect-submodules=PIL ^
    --collect-all=pikepdf ^
    --collect-all=fitz ^
    src\pdf_compressor.py

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

