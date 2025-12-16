@echo off
REM Build script for Blender Internal Render Engine native module (Windows)

setlocal enabledelayedexpansion

echo ========================================
echo Blender Internal Render Engine - Build
echo ========================================
echo.

REM Configuration
set "SCRIPT_DIR=%~dp0"
set "BUILD_DIR=%SCRIPT_DIR%build"
set "BLENDER_SRC=%BLENDER_SOURCE_DIR%"

REM Parse arguments
set CLEAN=0

:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--clean" (
    set CLEAN=1
    shift
    goto parse_args
)
if /i "%~1"=="--blender-src" (
    set "BLENDER_SRC=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="-h" goto show_help

echo Unknown option: %~1
goto show_help

:end_parse

REM Check for Blender source
if "%BLENDER_SRC%"=="" (
    echo ERROR: Blender source directory not specified
    echo.
    echo Please provide Blender source path using:
    echo   --blender-src C:\path\to\blender\source
    echo or set BLENDER_SOURCE_DIR environment variable
    echo.
    echo You can get Blender source from:
    echo   git clone https://github.com/blender/blender.git
    echo.
    exit /b 1
)

if not exist "%BLENDER_SRC%" (
    echo ERROR: Blender source directory not found: %BLENDER_SRC%
    exit /b 1
)

echo Configuration:
echo   Blender Source: %BLENDER_SRC%
echo   Build Directory: %BUILD_DIR%
echo.

REM Clean if requested
if %CLEAN%==1 (
    echo Cleaning build directory...
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
)

REM Create build directory
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
cd /d "%BUILD_DIR%"

REM Detect Visual Studio
where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: CMake not found. Please install CMake and add it to PATH
    exit /b 1
)

echo.
echo Running CMake configuration...
cmake .. ^
    -G "Visual Studio 16 2019" ^
    -A x64 ^
    -DBLENDER_INCLUDE_DIR="%BLENDER_SRC%\source" ^
    -DCMAKE_BUILD_TYPE=Release

if %errorlevel% neq 0 (
    echo ERROR: CMake configuration failed
    exit /b 1
)

echo.
echo Building...
cmake --build . --config Release

if %errorlevel% neq 0 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Native module location:
echo   %BUILD_DIR%\Release
echo.
echo To use the native engine:
echo   1. Install the addon in Blender
echo   2. The addon will automatically detect the native module
echo   3. Check Blender console for 'Native Blender Internal render engine loaded'
echo.

goto :eof

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   --clean              Clean build directory before building
echo   --blender-src PATH   Path to Blender source directory
echo   --help, -h           Show this help message
echo.
echo Environment variables:
echo   BLENDER_SOURCE_DIR   Path to Blender source (alternative to --blender-src)
echo.
echo Example:
echo   %~nx0 --blender-src C:\path\to\blender\source
echo   set BLENDER_SOURCE_DIR=C:\path\to\blender\source && %~nx0
echo.
exit /b 0
