# Blender Internal Render Engine - Translation Layer

This addon restores the Blender Internal (BI) render engine from Blender 2.79 to modern Blender versions using a translation layer approach.

## Overview

The Blender Internal render engine was removed from Blender after version 2.79. This addon brings it back by:

1. **Using the original C/C++ source code** from Blender 2.79
2. **Creating a translation/compatibility layer** to bridge API differences
3. **Compiling it as a native extension** that modern Blender can load
4. **Providing a Python fallback** for systems where native compilation isn't available

## Architecture

```
┌─────────────────────────────────────┐
│   Modern Blender (3.x/4.x)          │
├─────────────────────────────────────┤
│   Python Addon (UI + Registration)  │
├─────────────────────────────────────┤
│   Translation Layer (Python/C)      │
│   - API compatibility shims          │
│   - Data structure conversion        │
│   - RNA/DNA bridges                  │
├─────────────────────────────────────┤
│   Original Blender 2.79              │
│   Render Engine (C/C++)              │
│   - Ray tracing                      │
│   - Materials & Textures             │
│   - Lighting & Shadows               │
│   - SSS, AO, etc.                    │
└─────────────────────────────────────┘
```

## Features

### UI Panels (Restored from 2.79)
- ✅ Render settings and dimensions
- ✅ Anti-aliasing and sampling
- ✅ Material system (diffuse, specular, transparency, mirror, SSS, halo)
- ✅ Texture system with all procedural textures
- ✅ World/environment settings
- ✅ Lamp/light settings (point, sun, spot, area, hemi)
- ✅ Render layers and passes
- ✅ Bake settings

### Render Engine Features
- 🔄 Ray tracing (in progress)
- 🔄 Material shading (in progress)
- 🔄 Texture mapping (in progress)
- 🔄 Lighting and shadows (in progress)
- 🔄 Ambient occlusion (planned)
- 🔄 Subsurface scattering (planned)
- 🔄 Motion blur (planned)
- 🔄 Environment mapping (planned)

Legend: ✅ Complete | 🔄 In Progress | ❌ Not Yet Started

## Installation

### Option 1: Download Pre-Built Artifacts (Easiest)

Pre-built packages are available from GitHub Actions for easy testing:

1. Go to the [GitHub Actions page](https://github.com/ExtCan/RandomBlenderAddons/actions)
2. Click on the latest successful workflow run
3. Download the artifact for your platform and Blender version:
   - `blender-internal-render-linux-blenderX.X`
   - `blender-internal-render-windows-blenderX.X`
   - `blender-internal-render-macos-blenderX.X`
4. Extract the zip file
5. Copy the `blender_internal_render` folder to your Blender addons directory:
   - **Linux**: `~/.config/blender/X.X/scripts/addons/`
   - **macOS**: `~/Library/Application Support/Blender/X.X/scripts/addons/`
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\X.X\scripts\addons\`
6. Open Blender → Edit → Preferences → Add-ons
7. Search for "Blender Internal"
8. Enable the addon

### Option 2: Quick Install from Source (Python Fallback Only)

1. Download the `blender_internal_render` folder from this repository
2. Copy it to your Blender addons directory (see paths above)
3. Open Blender → Edit → Preferences → Add-ons
4. Search for "Blender Internal"
5. Enable the addon

This will give you the UI panels and a Python-based render engine.

### Option 3: Building the Native Engine (Best Performance)

To get full performance with the original C/C++ render engine, you need to compile it.

#### Prerequisites

- CMake 3.10+
- C/C++ compiler (GCC, Clang, or MSVC)
- Python 3.x development headers
- Blender source code or headers

#### Build Steps

1. **Get Blender source headers**
   ```bash
   # Clone Blender source (or just download headers)
   git clone https://github.com/blender/blender.git
   ```

2. **Navigate to engine source**
   ```bash
   cd blender_internal_render/engine_src
   mkdir build
   cd build
   ```

3. **Configure CMake**
   ```bash
   cmake .. \
     -DBLENDER_INCLUDE_DIR=/path/to/blender/source \
     -DCMAKE_BUILD_TYPE=Release
   ```

4. **Build**
   ```bash
   cmake --build . --config Release
   ```

5. **The compiled module** will be in `build/` directory

#### Platform-Specific Notes

**Linux:**
```bash
sudo apt-get install cmake build-essential python3-dev
cmake .. -DBLENDER_INCLUDE_DIR=/path/to/blender/source
make -j$(nproc)
```

**macOS:**
```bash
brew install cmake
cmake .. -DBLENDER_INCLUDE_DIR=/path/to/blender/source
make -j$(sysctl -n hw.ncpu)
```

**Windows:**
```cmd
cmake .. -G "Visual Studio 16 2019" -DBLENDER_INCLUDE_DIR=C:\path\to\blender\source
cmake --build . --config Release
```

## Usage

1. **Set Render Engine**
   - In the Scene Properties, set Render Engine to "Blender Internal"

2. **Configure Materials**
   - The classic BI material panels will appear in Material Properties
   - Set diffuse color, specular, transparency, etc.

3. **Add Lights**
   - Add lamps (Point, Sun, Spot, Area, Hemi)
   - Configure in Light Properties with BI-specific settings

4. **Render**
   - Press F12 or use Render > Render Image
   - Check console to see if native or fallback engine is used

## Known Limitations

### Current Limitations
- **Performance**: Python fallback is slower than original C implementation
- **Features**: Some advanced features not yet implemented in fallback
- **Compatibility**: Some Blender 2.79 properties may not exist in modern Blender
- **Nodes**: Shader nodes are not supported (BI uses fixed-function materials)

### API Differences
Modern Blender has changed significantly since 2.79:
- RNA property names and types may differ
- Some operators have been removed or renamed
- Data structures have evolved

The translation layer handles these differences where possible.

## Development

### Project Structure
```
blender_internal_render/
├── __init__.py              # Main addon file
├── render_engine.py         # Python render engine + translation layer
├── ui_render.py             # Render settings UI
├── ui_material.py           # Material UI
├── ui_texture.py            # Texture UI
├── ui_world.py              # World UI
├── ui_lamp.py               # Lamp UI
├── ui_render_layer.py       # Render layer UI
└── engine_src/              # Native engine source
    ├── CMakeLists.txt       # Build configuration
    ├── compat/              # Compatibility layer
    │   ├── blender_compat.h/c
    │   ├── api_translation.c
    │   ├── rna_bridge.c
    │   └── dna_bridge.c
    ├── bindings/            # Python bindings
    │   └── render_engine_module.c
    └── render/              # Original 2.79 render code
        ├── include/
        ├── source/
        └── raytrace/
```

### Contributing

Contributions are welcome! Areas that need work:

1. **Translation Layer**: Improve API compatibility
2. **Property Mapping**: Map more 2.79 properties to modern equivalents
3. **Feature Implementation**: Complete unfinished render features
4. **Testing**: Test on different platforms and Blender versions
5. **Documentation**: Improve docs and examples

### Testing

```bash
# Test Python fallback
blender --background --python test_render.py

# Test with native engine
# (ensure blender_render_engine.so/pyd is in engine_src/build/)
blender --background --python test_render.py
```

## License

This addon uses code from Blender 2.79, which is licensed under GPL v2 or later.

- Original Blender code: © Blender Foundation
- Translation layer and addon: © ExtCan
- License: GNU GPL v2+

## Credits

- **Blender Foundation**: Original Blender Internal render engine
- **ExtCan**: Addon port and translation layer
- **Blender 2.79 Source**: https://github.com/ExtCan/blender-AI-edits/tree/v2.79

## Troubleshooting

### "Native render engine not available"
- This is normal if you haven't built the native module
- The Python fallback will be used automatically
- Build the native module for better performance (see Building section)

### "No module named 'blender_render_engine'"
- The native module wasn't found
- Check that it's in `engine_src/build/`
- Verify it has the correct name for your platform (.so, .pyd, .dylib)

### Material properties missing
- Some 2.79 properties don't exist in modern Blender
- The addon tries to access them gracefully
- Check console for warnings about missing properties

### Render is black/empty
- Make sure you have a camera in the scene
- Add lights (BI requires explicit lighting)
- Check material settings (emission, diffuse color, etc.)

## Future Plans

- Complete implementation of all BI features
- Optimize Python fallback renderer
- Add more comprehensive property translation
- Support for texture baking
- Viewport rendering support
- Better error handling and user feedback
- Pre-built binaries for common platforms

## Links

- Repository: https://github.com/ExtCan/RandomBlenderAddons
- Blender 2.79 Source: https://github.com/ExtCan/blender-AI-edits/tree/v2.79
- Issues: https://github.com/ExtCan/RandomBlenderAddons/issues
