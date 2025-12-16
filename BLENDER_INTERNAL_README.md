# Blender Internal Render Engine - Reimplementation

## Overview

This addon reimplements the classic **Blender Internal** render engine that was deprecated and removed in Blender 2.8. It provides a basic scanline renderer with support for materials, lighting, and simple shading.

## Features

- **Custom Render Engine**: Fully functional render engine that appears in the render engine dropdown
- **Material Support**: Basic material rendering with diffuse and specular components
- **Lighting**: Support for Point lights and Sun lights with energy and color controls
- **Scanline Rendering**: Simple but effective rasterization algorithm
- **Camera Support**: Proper perspective projection from camera viewpoint
- **World Background**: Uses scene world color as background

## Installation

1. Download `blender_internal_render.py`
2. Open Blender (3.0 or higher recommended)
3. Go to **Edit > Preferences > Add-ons**
4. Click **Install** and select the downloaded file
5. Enable the addon by checking the box next to "Render: Blender Internal Render (Reimplemented)"

## Usage

### Selecting the Render Engine

1. In the Properties panel, go to the **Render Properties** tab (camera icon)
2. At the top, you'll see **Render Engine** dropdown
3. Select **Blender Internal** from the list

### Basic Rendering

1. Set up your scene with:
   - A Camera (required)
   - Mesh objects
   - Lights (Point or Sun)
   - Materials with colors

2. Press **F12** to render or click **Render > Render Image**

### Supported Features

#### Materials
- The addon extracts base color from materials
- Works with both node-based materials (Principled BSDF) and legacy materials
- Default gray color (0.8, 0.8, 0.8) for objects without materials

#### Lights
- **Sun Light**: Directional lighting with proper normal-based diffuse shading
- **Point Light**: Omnidirectional light source
- Light color and energy are respected

#### Camera
- Perspective projection
- Uses camera's field of view and aspect ratio
- Renders from camera viewpoint

### Render Settings Panel

When Blender Internal is selected as the render engine, a special settings panel appears showing:
- Information about the renderer
- List of supported features

## Technical Details

### Rendering Process

1. **Scene Evaluation**: The addon evaluates the dependency graph to get the current scene state
2. **Camera Setup**: Extracts camera position and projection parameters
3. **Light Collection**: Gathers all lights in the scene
4. **Mesh Processing**: For each mesh object:
   - Transforms vertices to camera space
   - Projects to screen space using perspective projection
   - Calculates lighting per face
   - Rasterizes polygons using scanline algorithm
5. **Output**: Generates final image with proper colors

### Lighting Model

The renderer uses a simple Lambertian diffuse lighting model:
- **Ambient**: Base illumination (0.1, 0.1, 0.1)
- **Diffuse**: `color * light_color * light_energy * max(0, normal · light_direction)`

### Rasterization

Uses a point-in-polygon test with ray casting algorithm to determine which pixels belong to each face.

## Limitations

This is a basic reimplementation and has several limitations compared to the original Blender Internal renderer:

- **No Raytracing**: Only scanline rendering
- **No Shadows**: Shadow casting not implemented
- **No Reflections/Refractions**: No recursive ray tracing
- **Limited Material Properties**: Only base color is used
- **No Texture Mapping**: Textures are not supported
- **No Bump/Normal Maps**: Surface detail not supported
- **Basic Lighting**: No advanced lighting features like area lights
- **No Anti-aliasing**: Edges may appear jagged
- **No Motion Blur**: Not implemented
- **No Depth of Field**: Camera effects not supported
- **No Viewport Preview**: Currently only works for final renders

## Troubleshooting

### Nothing Renders
- Ensure you have a camera in the scene
- Check that objects have geometry (vertices and faces)
- Verify objects are in front of the camera

### Black Render
- Add lights to your scene (Sun or Point lights)
- Check that light energy is > 0
- Ensure objects have materials with non-black colors

### Performance Issues
- Reduce render resolution
- Simplify mesh geometry
- Reduce number of lights

## Future Improvements

Potential enhancements for future versions:
- Viewport preview rendering
- Shadow support
- Texture mapping
- Better anti-aliasing
- More light types (Spot, Area)
- Specular highlights
- Transparency and alpha blending
- Ambient Occlusion
- Global Illumination (basic)

## Compatibility

- **Blender Version**: 3.0+
- **Dependencies**: numpy (usually included with Blender)
- **Platform**: All platforms supported by Blender

## License

This is a community reimplementation project. The original Blender Internal renderer was developed by the Blender Foundation.

## Credits

- Original Blender Internal renderer: Blender Foundation
- Reimplementation: Community contribution

## Support

For issues, feature requests, or contributions, please visit the project repository.
