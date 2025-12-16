# Random Blender Addons

![Build Status](https://github.com/ExtCan/RandomBlenderAddons/actions/workflows/build-addon.yml/badge.svg)
![Test Status](https://github.com/ExtCan/RandomBlenderAddons/actions/workflows/test-addon.yml/badge.svg)

A collection of useful Blender addons.

## Available Addons

### 1. Rotating ASCII
Export Object as Rotating ASCII python script

### 2. pixel2cube
Imports images as colored cubes, best used with sprites. Make sure when you separate the sprite models to merge by distance, it creates doubles for some reason.

### 3. Blender Internal Render Engine
Restores the Blender Internal (BI) render engine from Blender 2.79 to modern Blender versions using a translation layer.

**Quick Start:**
- 📦 **Download pre-built artifacts** from [GitHub Actions](https://github.com/ExtCan/RandomBlenderAddons/actions) (easiest way to test)
- 📥 Install from source or build native engine for best performance

**Features:**
- Original C/C++ render engine code with translation layer
- Complete UI panels from Blender 2.79
- Python fallback renderer for systems without native compilation
- Full material system (diffuse, specular, transparency, mirror, SSS, halo)
- All procedural textures
- Classic lighting and shadows
- Ray tracing support

See [blender_internal_render/README.md](blender_internal_render/README.md) for detailed documentation and [blender_internal_render/BUILD_GUIDE.md](blender_internal_render/BUILD_GUIDE.md) for build instructions.

## Installation

Each addon has its own installation instructions. Generally:

1. Download or clone this repository
2. Copy the addon folder to your Blender addons directory
3. Enable the addon in Blender Preferences → Add-ons

## License

- Individual addons may have their own licenses
- Blender Internal Render Engine uses GPL v2+ (derived from Blender 2.79)
