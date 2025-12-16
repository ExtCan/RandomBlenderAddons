"""
Test script for Blender Internal Render Engine addon

This script creates a simple test scene and renders it with the
Blender Internal render engine.

Usage:
    blender --background --python test_render.py
"""

import bpy
import sys
import os

def setup_test_scene():
    """Create a simple test scene"""
    print("Setting up test scene...")
    
    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Add a cube
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "TestCube"
    
    # Add material to cube
    mat = bpy.data.materials.new(name="TestMaterial")
    mat.diffuse_color = (0.8, 0.2, 0.2, 1.0)  # Red
    if cube.data.materials:
        cube.data.materials[0] = mat
    else:
        cube.data.materials.append(mat)
    
    # Add camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.1, 0, 0.785)
    bpy.context.scene.camera = camera
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    light = bpy.context.active_object
    light.data.energy = 2.0
    
    print("Test scene created")

def test_render():
    """Test rendering with Blender Internal"""
    print("\n" + "="*50)
    print("Testing Blender Internal Render Engine")
    print("="*50 + "\n")
    
    # Setup scene
    setup_test_scene()
    
    # Set render engine
    scene = bpy.context.scene
    
    # Check if BLENDER_RENDER is available
    available_engines = [engine.bl_idname for engine in bpy.types.RenderEngine.__subclasses__()]
    print(f"Available render engines: {available_engines}")
    
    if 'BLENDER_RENDER' not in available_engines:
        print("\nERROR: BLENDER_RENDER engine not found!")
        print("Make sure the Blender Internal addon is installed and enabled.")
        return False
    
    # Set to Blender Internal
    scene.render.engine = 'BLENDER_RENDER'
    print(f"\nRender engine set to: {scene.render.engine}")
    
    # Configure render settings
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    
    # Set output path
    output_path = "/tmp/blender_internal_test.png"
    scene.render.filepath = output_path
    
    print(f"Output path: {output_path}")
    print("\nStarting render...")
    
    try:
        # Render
        bpy.ops.render.render(write_still=True)
        
        # Check if file was created
        if os.path.exists(output_path):
            print(f"\n✓ Render completed successfully!")
            print(f"  Output: {output_path}")
            return True
        else:
            print(f"\n✗ Render completed but output file not found!")
            return False
            
    except Exception as e:
        print(f"\n✗ Render failed with error:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_render()
    
    print("\n" + "="*50)
    if success:
        print("TEST PASSED")
    else:
        print("TEST FAILED")
    print("="*50 + "\n")
    
    sys.exit(0 if success else 1)
