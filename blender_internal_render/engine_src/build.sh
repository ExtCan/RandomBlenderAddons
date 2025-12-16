#!/usr/bin/env bash
# Build script for Blender Internal Render Engine native module

set -e  # Exit on error

echo "========================================"
echo "Blender Internal Render Engine - Build"
echo "========================================"
echo ""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
BLENDER_SRC="${BLENDER_SOURCE_DIR:-}"

# Parse arguments
CLEAN=0
HELP=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=1
            shift
            ;;
        --blender-src)
            BLENDER_SRC="$2"
            shift 2
            ;;
        --help|-h)
            HELP=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            HELP=1
            shift
            ;;
    esac
done

if [ $HELP -eq 1 ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean              Clean build directory before building"
    echo "  --blender-src PATH   Path to Blender source directory"
    echo "  --help, -h           Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  BLENDER_SOURCE_DIR   Path to Blender source (alternative to --blender-src)"
    echo ""
    echo "Example:"
    echo "  $0 --blender-src /path/to/blender/source"
    echo "  BLENDER_SOURCE_DIR=/path/to/blender/source $0"
    exit 0
fi

# Check for Blender source
if [ -z "$BLENDER_SRC" ]; then
    echo "ERROR: Blender source directory not specified"
    echo ""
    echo "Please provide Blender source path using:"
    echo "  --blender-src /path/to/blender/source"
    echo "or set BLENDER_SOURCE_DIR environment variable"
    echo ""
    echo "You can get Blender source from:"
    echo "  git clone https://github.com/blender/blender.git"
    echo ""
    exit 1
fi

if [ ! -d "$BLENDER_SRC" ]; then
    echo "ERROR: Blender source directory not found: $BLENDER_SRC"
    exit 1
fi

echo "Configuration:"
echo "  Blender Source: $BLENDER_SRC"
echo "  Build Directory: $BUILD_DIR"
echo ""

# Clean if requested
if [ $CLEAN -eq 1 ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
fi

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Detect number of CPU cores
if command -v nproc >/dev/null 2>&1; then
    CORES=$(nproc)
elif command -v sysctl >/dev/null 2>&1; then
    CORES=$(sysctl -n hw.ncpu)
else
    CORES=4
fi

echo "Building with $CORES parallel jobs..."
echo ""

# Configure
echo "Running CMake configuration..."
cmake .. \
    -DBLENDER_INCLUDE_DIR="$BLENDER_SRC/source" \
    -DCMAKE_BUILD_TYPE=Release

echo ""
echo "Building..."
cmake --build . --config Release -j $CORES

echo ""
echo "========================================"
echo "Build complete!"
echo "========================================"
echo ""
echo "Native module location:"
echo "  $BUILD_DIR"
echo ""
echo "To use the native engine:"
echo "  1. Install the addon in Blender"
echo "  2. The addon will automatically detect the native module"
echo "  3. Check Blender console for 'Native Blender Internal render engine loaded'"
echo ""
