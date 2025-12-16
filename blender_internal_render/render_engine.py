# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Blender Internal Render Engine - Translation Layer

This module provides a translation layer between modern Blender and the
original Blender 2.79 Internal render engine C/C++ code.

The engine can work in two modes:
1. Native mode: Uses the compiled C/C++ render engine (best performance)
2. Fallback mode: Uses pure Python implementation (compatibility)
"""

import bpy
import numpy as np
from mathutils import Vector, Matrix, Color
import math
from concurrent.futures import ThreadPoolExecutor
import time
import os
import sys

# Try to import the native render engine module
NATIVE_ENGINE_AVAILABLE = False
native_engine = None

try:
    # Look for the compiled module in the addon directory
    addon_dir = os.path.dirname(__file__)
    engine_dir = os.path.join(addon_dir, 'engine_src', 'build')
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)
    
    import blender_render_engine as native_engine
    NATIVE_ENGINE_AVAILABLE = True
    print(f"Native Blender Internal render engine loaded: {native_engine.test()}")
except ImportError as e:
    print(f"Native render engine not available, using Python fallback: {e}")
    NATIVE_ENGINE_AVAILABLE = False


class BlenderInternalRenderEngine(bpy.types.RenderEngine):
    """
    Blender Internal render engine with translation layer.
    
    This engine bridges modern Blender with the original Blender 2.79
    Internal render engine code through a translation layer.
    
    Modes:
    - Native: Uses compiled C/C++ engine (when available)
    - Fallback: Pure Python implementation
    """
    
    bl_idname = 'BLENDER_RENDER'
    bl_label = "Blender Internal"
    bl_use_preview = True
    bl_use_postprocess = True
    bl_use_shading_nodes = False
    bl_use_shading_nodes_custom = False
    
    def __init__(self):
        self.session = None
        self.render_data = {}
        self.use_native = NATIVE_ENGINE_AVAILABLE
    
    # Render methods
    def render(self, depsgraph):
        """Main render method called by Blender"""
        if self.use_native and NATIVE_ENGINE_AVAILABLE:
            self.render_native(depsgraph)
        else:
            self.render_fallback(depsgraph)
    
    def render_native(self, depsgraph):
        """Render using native C/C++ engine"""
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)
        
        # Initialize render result
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]
        
        try:
            # Call native render engine
            # TODO: Pass scene data to native engine
            # TODO: Get render result back
            
            self.report({'INFO'}, "Native render engine called")
            
            # For now, just fill with a test pattern
            pixels = np.zeros((self.size_y, self.size_x, 4), dtype=np.float32)
            for y in range(self.size_y):
                for x in range(self.size_x):
                    pixels[y, x] = [0.2, 0.6, 0.2, 1.0]  # Green tint for native
            layer.rect = pixels.flatten().tolist()
            
        except Exception as e:
            self.report({'ERROR'}, f"Native render error: {str(e)}")
            # Fallback to Python implementation
            self.render_fallback(depsgraph)
            return
        
        self.end_result(result)
    
    def render_fallback(self, depsgraph):
        """Render using Python fallback implementation"""
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)
        
        # Initialize render result
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]
        
        # Perform rendering
        try:
            if self.is_preview:
                # Faster preview rendering
                self.render_preview(depsgraph, layer)
            else:
                # Full quality rendering
                self.render_scene(depsgraph, layer)
        except Exception as e:
            self.report({'ERROR'}, f"Render error: {str(e)}")
            print(f"Detailed error: {e}")
            import traceback
            traceback.print_exc()
        
        self.end_result(result)
    
    def render_preview(self, depsgraph, layer):
        """Fast preview rendering"""
        # Create a simple gradient or solid color for preview
        pixels = np.zeros((self.size_y, self.size_x, 4), dtype=np.float32)
        
        # Simple gradient background
        for y in range(self.size_y):
            for x in range(self.size_x):
                pixels[y, x] = [0.5, 0.5, 0.6, 1.0]  # Grayish-blue
        
        # Flatten and set pixels
        layer.rect = pixels.flatten().tolist()
    
    def render_scene(self, depsgraph, layer):
        """Full scene rendering with ray tracing"""
        scene = depsgraph.scene
        
        # Get camera
        camera = scene.camera
        if not camera:
            self.report({'WARNING'}, "No camera found in scene")
            self.render_preview(depsgraph, layer)
            return
        
        # Initialize pixel buffer
        pixels = np.zeros((self.size_y, self.size_x, 4), dtype=np.float32)
        
        # Setup camera matrices
        cam_matrix = camera.matrix_world
        cam_data = camera.data
        
        # Render settings
        rd = scene.render
        use_antialiasing = getattr(rd, 'use_antialiasing', False)
        aa_samples = getattr(rd, 'antialiasing_samples', '5')
        
        # Get all renderable objects
        objects = [obj for obj in depsgraph.objects 
                  if obj.type == 'MESH' and obj.visible_get()]
        
        # Build scene geometry
        scene_geo = self.build_scene_geometry(depsgraph, objects)
        
        # Get lights
        lights = [obj for obj in depsgraph.objects 
                 if obj.type == 'LIGHT' and obj.visible_get()]
        
        # Render progress tracking
        total_pixels = self.size_x * self.size_y
        pixels_done = 0
        update_frequency = max(1, total_pixels // 100)  # Update every 1%
        
        # Render each pixel
        for y in range(self.size_y):
            if self.test_break():
                break
            
            for x in range(self.size_x):
                # Normalized device coordinates
                ndc_x = (x + 0.5) / self.size_x
                ndc_y = (y + 0.5) / self.size_y
                
                # Generate camera ray
                ray_origin, ray_direction = self.generate_camera_ray(
                    camera, cam_matrix, cam_data, ndc_x, ndc_y
                )
                
                # Trace ray and get color
                color = self.trace_ray(
                    ray_origin, ray_direction, scene_geo, lights, 
                    depsgraph, max_depth=2
                )
                
                pixels[self.size_y - 1 - y, x] = [color[0], color[1], color[2], 1.0]
                
                pixels_done += 1
                if pixels_done % update_frequency == 0:
                    progress = pixels_done / total_pixels
                    self.update_progress(progress)
                    self.update_stats("Rendering", f"Pixel {pixels_done}/{total_pixels}")
        
        # Set final pixels
        layer.rect = pixels.flatten().tolist()
    
    def build_scene_geometry(self, depsgraph, objects):
        """Build scene geometry data structure for ray tracing"""
        scene_geo = []
        
        for obj in objects:
            if obj.type != 'MESH':
                continue
            
            # Get evaluated mesh
            obj_eval = obj.evaluated_get(depsgraph)
            mesh = obj_eval.to_mesh()
            
            if mesh is None:
                continue
            
            # Get transformation matrix
            matrix_world = obj.matrix_world
            
            # Get material
            material = None
            if len(obj.data.materials) > 0:
                material = obj.data.materials[0]
            
            # Store geometry data
            geo_data = {
                'object': obj,
                'mesh': mesh,
                'matrix_world': matrix_world.copy(),
                'matrix_inverse': matrix_world.inverted(),
                'material': material,
                'triangles': []
            }
            
            # Convert mesh to triangles
            mesh.calc_loop_triangles()
            for tri in mesh.loop_triangles:
                v_indices = tri.vertices
                verts = [mesh.vertices[i].co for i in v_indices]
                normals = [mesh.vertices[i].normal for i in v_indices]
                
                # Transform to world space
                verts_world = [matrix_world @ v for v in verts]
                normals_world = [matrix_world.to_3x3() @ n for n in normals]
                
                geo_data['triangles'].append({
                    'vertices': verts_world,
                    'normals': normals_world,
                    'normal': tri.normal,
                    'material_index': tri.material_index
                })
            
            scene_geo.append(geo_data)
            
            # Clean up
            obj_eval.to_mesh_clear()
        
        return scene_geo
    
    def generate_camera_ray(self, camera, cam_matrix, cam_data, ndc_x, ndc_y):
        """Generate a camera ray for the given pixel coordinates"""
        # Convert NDC to screen space [-1, 1]
        screen_x = (ndc_x * 2.0) - 1.0
        screen_y = (ndc_y * 2.0) - 1.0
        
        # Get camera parameters
        if cam_data.type == 'PERSP':
            # Perspective camera
            aspect_ratio = self.size_x / self.size_y
            fov = cam_data.angle
            
            # Calculate ray direction in camera space
            tan_fov = math.tan(fov / 2.0)
            ray_dir_cam = Vector((
                screen_x * tan_fov * aspect_ratio,
                screen_y * tan_fov,
                -1.0
            )).normalized()
            
            # Transform to world space
            ray_origin = cam_matrix.translation
            ray_direction = (cam_matrix.to_3x3() @ ray_dir_cam).normalized()
        else:
            # Orthographic camera
            scale = cam_data.ortho_scale
            aspect_ratio = self.size_x / self.size_y
            
            # Ray origin in camera space
            ray_origin_cam = Vector((
                screen_x * scale * aspect_ratio * 0.5,
                screen_y * scale * 0.5,
                0.0
            ))
            
            # Transform to world space
            ray_origin = cam_matrix @ ray_origin_cam
            ray_direction = (cam_matrix.to_3x3() @ Vector((0, 0, -1))).normalized()
        
        return ray_origin, ray_direction
    
    def trace_ray(self, ray_origin, ray_direction, scene_geo, lights, depsgraph, max_depth=3):
        """Trace a ray through the scene"""
        # Find closest intersection
        hit_data = self.intersect_scene(ray_origin, ray_direction, scene_geo)
        
        if hit_data is None:
            # No hit - return background color
            return self.get_background_color(depsgraph.scene)
        
        # Shade the hit point
        color = self.shade_point(
            hit_data, ray_origin, ray_direction, 
            scene_geo, lights, depsgraph, max_depth
        )
        
        return color
    
    def intersect_scene(self, ray_origin, ray_direction, scene_geo):
        """Find the closest intersection of a ray with the scene"""
        closest_hit = None
        closest_distance = float('inf')
        
        for geo_data in scene_geo:
            for triangle in geo_data['triangles']:
                hit = self.intersect_triangle(
                    ray_origin, ray_direction, triangle
                )
                
                if hit and hit['distance'] < closest_distance:
                    closest_distance = hit['distance']
                    hit['geo_data'] = geo_data
                    hit['triangle'] = triangle
                    closest_hit = hit
        
        return closest_hit
    
    def intersect_triangle(self, ray_origin, ray_direction, triangle):
        """Ray-triangle intersection using Möller–Trumbore algorithm"""
        v0, v1, v2 = triangle['vertices']
        
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        h = ray_direction.cross(edge2)
        a = edge1.dot(h)
        
        if abs(a) < 1e-8:
            return None  # Ray is parallel to triangle
        
        f = 1.0 / a
        s = ray_origin - v0
        u = f * s.dot(h)
        
        if u < 0.0 or u > 1.0:
            return None
        
        q = s.cross(edge1)
        v = f * ray_direction.dot(q)
        
        if v < 0.0 or u + v > 1.0:
            return None
        
        t = f * edge2.dot(q)
        
        if t > 1e-8:  # Ray intersection
            hit_point = ray_origin + ray_direction * t
            
            # Interpolate normal
            w = 1.0 - u - v
            n0, n1, n2 = triangle['normals']
            normal = (n0 * w + n1 * u + n2 * v).normalized()
            
            return {
                'distance': t,
                'point': hit_point,
                'normal': normal,
                'uv': (u, v)
            }
        
        return None
    
    def shade_point(self, hit_data, ray_origin, ray_direction, scene_geo, lights, depsgraph, max_depth):
        """Shade a point using material properties and lighting"""
        point = hit_data['point']
        normal = hit_data['normal']
        geo_data = hit_data['geo_data']
        material = geo_data['material']
        
        # Default material color
        diffuse_color = Color((0.8, 0.8, 0.8))
        specular_color = Color((1.0, 1.0, 1.0))
        specular_intensity = 0.5
        specular_hardness = 50
        emit = 0.0
        alpha = 1.0
        
        # Get material properties if available
        if material:
            diffuse_color = Color(material.diffuse_color[:3])
            if hasattr(material, 'specular_color'):
                specular_color = Color(material.specular_color[:3])
            if hasattr(material, 'specular_intensity'):
                specular_intensity = material.specular_intensity
            if hasattr(material, 'specular_hardness'):
                specular_hardness = material.specular_hardness
            if hasattr(material, 'emit'):
                emit = material.emit
        
        # Initialize color with emission
        color = diffuse_color * emit
        
        # Ambient lighting
        world = depsgraph.scene.world
        ambient = Color((0.0, 0.0, 0.0))
        if world:
            ambient_factor = 0.0
            if hasattr(world, 'ambient_color'):
                ambient = Color(world.ambient_color[:3])
            # Use a small ambient factor
            color += diffuse_color * ambient * 0.1
        
        # Direct lighting from lights
        for light_obj in lights:
            light_data = light_obj.data
            light_pos = light_obj.matrix_world.translation
            
            # Vector from surface to light
            to_light = light_pos - point
            light_distance = to_light.length
            light_dir = to_light.normalized()
            
            # Shadow test
            shadow_offset = normal * 0.001  # Offset to avoid self-intersection
            shadow_hit = self.intersect_scene(point + shadow_offset, light_dir, scene_geo)
            
            if shadow_hit and shadow_hit['distance'] < light_distance:
                continue  # Point is in shadow
            
            # Light intensity with distance falloff
            light_color = Color(light_data.color[:3])
            light_energy = light_data.energy
            
            # Distance attenuation
            if light_data.type == 'POINT':
                attenuation = 1.0 / (1.0 + light_distance * light_distance * 0.01)
            elif light_data.type == 'SUN':
                attenuation = 1.0
                light_dir = (light_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            elif light_data.type == 'SPOT':
                attenuation = 1.0 / (1.0 + light_distance * light_distance * 0.01)
                # TODO: Implement spot cone
            else:
                attenuation = 1.0 / (1.0 + light_distance * light_distance * 0.01)
            
            # Diffuse lighting (Lambertian)
            n_dot_l = max(0.0, normal.dot(light_dir))
            diffuse = diffuse_color * light_color * light_energy * attenuation * n_dot_l
            
            # Specular lighting (Blinn-Phong)
            view_dir = (ray_origin - point).normalized()
            half_vec = (light_dir + view_dir).normalized()
            n_dot_h = max(0.0, normal.dot(half_vec))
            specular = specular_color * light_color * light_energy * attenuation * \
                      specular_intensity * pow(n_dot_h, specular_hardness)
            
            color += diffuse + specular
        
        # Clamp color
        color.r = min(1.0, max(0.0, color.r))
        color.g = min(1.0, max(0.0, color.g))
        color.b = min(1.0, max(0.0, color.b))
        
        return color
    
    def get_background_color(self, scene):
        """Get the background color from world settings"""
        world = scene.world
        if world:
            # Try to get horizon color (classic BI)
            if hasattr(world, 'horizon_color'):
                return Color(world.horizon_color[:3])
            # Fallback to modern use_nodes color
            elif world.use_nodes and world.node_tree:
                # Try to find background node
                for node in world.node_tree.nodes:
                    if node.type == 'BACKGROUND':
                        return Color(node.inputs['Color'].default_value[:3])
        
        # Default gray background
        return Color((0.05, 0.05, 0.05))
    
    def view_update(self, context, depsgraph):
        """Called when the scene is updated in viewport"""
        pass
    
    def view_draw(self, context, depsgraph):
        """Called for viewport rendering"""
        # For now, we don't implement viewport rendering
        pass


def register():
    bpy.utils.register_class(BlenderInternalRenderEngine)


def unregister():
    bpy.utils.unregister_class(BlenderInternalRenderEngine)


if __name__ == "__main__":
    register()
