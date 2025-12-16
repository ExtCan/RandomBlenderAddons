# Blender Internal Render Engine - Quick Start Guide

## Installation Steps

1. **Download the addon**
   - Download `blender_internal_render.py` from this repository

2. **Install in Blender**
   - Open Blender (version 3.0 or higher)
   - Go to `Edit → Preferences` (or `Blender → Preferences` on macOS)
   - Select the `Add-ons` tab
   - Click the `Install...` button at the top
   - Navigate to and select `blender_internal_render.py`
   - Click `Install Add-on`

3. **Enable the addon**
   - In the Add-ons list, search for "Blender Internal"
   - Check the box next to "Render: Blender Internal Render (Reimplemented)"
   - The addon is now active

## Quick Start Tutorial

### Basic Scene Setup

1. **Start with the default scene** (or create a new one)
   - You should have a Camera, Cube, and Light

2. **Select the Blender Internal render engine**
   - Open the Properties panel (right side of the screen)
   - Click on the Render Properties tab (camera icon)
   - At the top, click the Render Engine dropdown
   - Select "Blender Internal"

3. **Render your first image**
   - Press `F12` (or go to `Render → Render Image`)
   - Wait a moment for the render to complete
   - You should see your scene rendered!

### Adding Materials

1. **Select an object** (e.g., the default cube)

2. **Add/Edit material**
   - Go to Material Properties (sphere icon)
   - If no material exists, click "New"
   - Change the "Base Color" to any color you like

3. **Render again** to see the color change

### Working with Lights

The Blender Internal renderer supports three light types:

#### Sun Light (Directional)
- Best for: Outdoor scenes, uniform lighting
- Creates parallel light rays
- Position doesn't matter, only rotation
```
Add → Light → Sun
Rotate to change light direction
Adjust Energy and Color in Light Properties
```

#### Point Light
- Best for: Light bulbs, local lighting
- Emits light in all directions from a point
- Position affects which surfaces are lit
```
Add → Light → Point
Move to position the light
Adjust Energy and Color in Light Properties
```

#### Spot Light
- Best for: Focused lighting, dramatic effects
- Directional cone of light
- Both position and rotation matter
```
Add → Light → Spot
Position and rotate to aim the light
Adjust Energy and Color in Light Properties
```

### Camera Setup

1. **Position the camera**
   - Select the camera object
   - Press `G` to move, `R` to rotate
   - Or use the Transform properties in the sidebar (`N` key)

2. **Look through the camera**
   - Press `Numpad 0` to view through the camera
   - This shows exactly what will be rendered

3. **Adjust camera properties**
   - Select the camera
   - Go to Camera Properties (camera icon in properties)
   - Adjust Focal Length for field of view

### World Background

1. **Change background color**
   - Go to World Properties (world icon)
   - Change the Color to set the background
   - This color will fill areas not covered by objects

## Example Scenes

### Simple Studio Setup
```
1. Delete default cube (X → Delete)
2. Add → Mesh → Suzanne (monkey head)
3. Add → Light → Point (position above and to the side)
4. Add → Light → Point (position on opposite side, lower energy)
5. Render (F12)
```

### Outdoor Scene
```
1. Add → Mesh → Plane (scale up to make ground: S → 10 → Enter)
2. Add various objects (cubes, spheres, etc.)
3. Change Light to Sun type
4. Rotate sun to simulate time of day
5. Change World color to sky blue (e.g., RGB: 0.5, 0.7, 1.0)
6. Render (F12)
```

## Keyboard Shortcuts

- `F12` - Render Image
- `Numpad 0` - View through camera
- `G` - Move selected object
- `R` - Rotate selected object
- `S` - Scale selected object
- `Shift + A` - Add menu (objects, lights, etc.)
- `X` - Delete selected object

## Tips and Tricks

1. **Increase render quality**
   - Go to Render Properties
   - Increase Resolution X and Y
   - Set Resolution % to 100%

2. **Multiple lights for better results**
   - Use 2-3 lights for more interesting shading
   - Try different light types together
   - Use lower energy values when using multiple lights

3. **Color your materials**
   - Different colored objects look better than all gray
   - Try complementary colors for visual interest

4. **Position objects in view**
   - Make sure objects are in front of the camera
   - Use the camera view (Numpad 0) to check composition

5. **Check your normals**
   - If objects look too dark, they might be facing away
   - Select object, Tab to Edit mode
   - In viewport overlays, enable Face Orientation
   - Blue = correct, Red = flipped (use Alt+N → Flip)

## Troubleshooting

### Render is completely black
- **Problem**: No lights in the scene
- **Solution**: Add at least one light (Add → Light → Sun)

### Objects are not visible
- **Problem**: Objects behind camera or outside view
- **Solution**: Press Numpad 0 and check camera view, move objects or camera

### Render is very dark
- **Problem**: Light energy too low or lights too far
- **Solution**: Increase light energy in Light Properties

### Colors look wrong
- **Problem**: Material colors not set correctly
- **Solution**: Check Material Properties, ensure Base Color is set

### Render is too slow
- **Problem**: High resolution or complex geometry
- **Solution**: 
  - Reduce Resolution % in Render Properties
  - Simplify mesh objects (fewer vertices)

## Performance Notes

- Render time increases with:
  - Higher resolution
  - More polygons (faces) in the scene
  - More lights
  - Complex geometry

- For faster renders:
  - Use lower resolution for tests
  - Simplify mesh objects
  - Limit number of lights to 2-3

## What's Next?

Once you're comfortable with the basics:
- Experiment with different light combinations
- Try various material colors
- Create more complex scenes
- Explore different camera angles

## Limitations to Remember

This is a basic renderer. It does NOT support:
- Textures or images on materials
- Shadows
- Reflections
- Transparency
- Bump maps or normal maps
- Ambient Occlusion
- Global Illumination

For these features, use Blender's built-in Cycles or Eevee engines.

## Getting Help

If you encounter issues:
1. Check this guide and the main README
2. Verify you're using Blender 3.0 or higher
3. Make sure the addon is enabled in Preferences
4. Try the default scene first to isolate problems

## Have Fun!

The Blender Internal renderer is a simple but capable tool for basic 3D rendering. Enjoy creating your renders!
