# Building the Native Render Engine

This guide provides detailed instructions for building the native C/C++ render engine from Blender 2.79 source code.

## Why Build the Native Engine?

The native engine provides:
- **Performance**: C/C++ is much faster than Python
- **Accuracy**: Uses the original render engine code
- **Features**: Complete implementation of all BI features

Without the native engine, the addon falls back to a Python implementation which is slower and has limited features.

## Prerequisites

### All Platforms

1. **CMake 3.10 or higher**
   - Download from: https://cmake.org/download/

2. **Python 3.7+** with development headers
   - The same version Blender uses

3. **Blender Source Code**
   ```bash
   git clone https://github.com/blender/blender.git
   ```
   OR download specific version headers

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install \
    build-essential \
    cmake \
    git \
    python3-dev \
    libpython3-dev
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install \
    gcc gcc-c++ \
    cmake \
    git \
    python3-devel
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake python
```

You'll also need Xcode Command Line Tools:
```bash
xcode-select --install
```

### Windows

1. **Visual Studio 2019 or 2022**
   - Download Community edition (free): https://visualstudio.microsoft.com/
   - During installation, select "Desktop development with C++"

2. **CMake**
   - Download installer: https://cmake.org/download/
   - Add to PATH during installation

3. **Python**
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH"
   - Install for all users

4. **Git**
   - Download from: https://git-scm.com/download/win

## Building Steps

### Step 1: Get Blender Source

You need Blender source code (or at least the headers) for your target Blender version.

**Option A: Clone Full Source**
```bash
git clone https://github.com/blender/blender.git
cd blender
git checkout v3.6.0  # or your Blender version
```

**Option B: Download Headers Only** (faster)
- Download from Blender releases
- Extract to a known location

### Step 2: Navigate to Engine Source

```bash
cd /path/to/addon/blender_internal_render/engine_src
```

### Step 3: Build

**Linux/macOS:**
```bash
./build.sh --blender-src /path/to/blender
```

**Windows:**
```cmd
build.bat --blender-src C:\path\to\blender
```

Or set environment variable:
```bash
export BLENDER_SOURCE_DIR=/path/to/blender
./build.sh
```

### Step 4: Verify Build

After successful build:

**Linux:**
```bash
ls build/blender_render_engine.so
```

**macOS:**
```bash
ls build/blender_render_engine.so
```

**Windows:**
```cmd
dir build\Release\blender_render_engine.pyd
```

## Manual Build (Advanced)

If the build scripts don't work, you can build manually:

```bash
cd engine_src
mkdir build
cd build

# Configure
cmake .. \
    -DBLENDER_INCLUDE_DIR=/path/to/blender/source \
    -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release -j $(nproc)
```

Windows (in Developer Command Prompt):
```cmd
cmake .. ^
    -G "Visual Studio 16 2019" ^
    -DBLENDER_INCLUDE_DIR=C:\path\to\blender\source ^
    -DCMAKE_BUILD_TYPE=Release

cmake --build . --config Release
```

## Troubleshooting

### "CMake not found"

Make sure CMake is installed and in your PATH:
```bash
cmake --version
```

If not found, install CMake or add it to PATH.

### "Python.h not found"

You need Python development headers:

**Linux:**
```bash
sudo apt-get install python3-dev
```

**macOS:**
```bash
brew install python
```

**Windows:**
Reinstall Python, make sure to check "Include development headers"

### "BLENDER_INCLUDE_DIR not found"

The CMake variable must point to Blender's `source` directory:
```bash
./build.sh --blender-src /correct/path/to/blender
```

Verify the path contains:
- `source/blender/makesdna/`
- `source/blender/blenkernel/`
- `source/blender/render/`

### Compilation Errors

**Undefined symbols/missing functions:**
- The translation layer may be incomplete
- Some Blender APIs may have changed
- Check CMakeLists.txt includes correct paths

**Type mismatches:**
- Blender structures may have changed between versions
- May need to update compatibility layer

**Linker errors:**
- Missing library dependencies
- Check CMake configuration for required libraries

### Module Doesn't Load in Blender

**"ImportError: cannot import name 'blender_render_engine'"**

1. Check the module was built:
   ```bash
   ls engine_src/build/*.so  # Linux/macOS
   dir engine_src\build\Release\*.pyd  # Windows
   ```

2. Check Python version matches Blender's:
   ```bash
   blender --version  # Note Python version
   python --version   # Should match
   ```

3. Try loading manually in Blender's Python console:
   ```python
   import sys
   sys.path.insert(0, '/path/to/addon/engine_src/build')
   import blender_render_engine
   print(blender_render_engine.test())
   ```

**"Symbol not found" or "DLL load failed"**

Missing dependencies. On Linux, check with:
```bash
ldd build/blender_render_engine.so
```

On macOS:
```bash
otool -L build/blender_render_engine.so
```

On Windows:
```cmd
dumpbin /dependents build\Release\blender_render_engine.pyd
```

## Testing the Build

Once built, test in Blender:

1. Start Blender with console:
   ```bash
   blender  # Linux/macOS
   blender.exe --debug  # Windows
   ```

2. Enable the addon

3. Check console output:
   ```
   Native Blender Internal render engine loaded: Blender Internal Render Engine (Native) - Loaded
   ```

4. Create a simple scene and render with "Blender Internal" engine

## Platform-Specific Notes

### Linux

- Use system Python that matches Blender's version
- May need to set `LD_LIBRARY_PATH` for dependencies
- Some distros may require additional `-dev` packages

### macOS

- Code signing may be required for newer macOS versions
- Use same architecture as Blender (arm64 or x86_64)
- May need to approve dylib in Security & Privacy settings

### Windows

- Use same compiler as Blender build (MSVC)
- Match architecture (64-bit)
- May need to install Visual C++ Redistributable

## Optimizations

### Release vs Debug

Always build in Release mode for performance:
```bash
-DCMAKE_BUILD_TYPE=Release
```

Debug builds are much slower but helpful for development.

### Compiler Optimizations

Add compiler flags in CMakeLists.txt:
```cmake
set(CMAKE_C_FLAGS_RELEASE "-O3 -march=native")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")
```

### Parallel Building

Use all CPU cores:
```bash
cmake --build . -j $(nproc)  # Linux
cmake --build . -j $(sysctl -n hw.ncpu)  # macOS
cmake --build . -j %NUMBER_OF_PROCESSORS%  # Windows
```

## Next Steps

After successful build:

1. **Test rendering** with various materials and settings
2. **Compare results** with Blender 2.79 if possible
3. **Report issues** on GitHub
4. **Contribute** improvements to the translation layer

## Getting Help

If you encounter issues:

1. Check this guide thoroughly
2. Search existing GitHub issues
3. Create a new issue with:
   - Your OS and version
   - Blender version
   - Complete error messages
   - Build log output

## Additional Resources

- Blender Build Documentation: https://wiki.blender.org/wiki/Building_Blender
- CMake Documentation: https://cmake.org/documentation/
- Blender 2.79 Source: https://github.com/ExtCan/blender-AI-edits/tree/v2.79
