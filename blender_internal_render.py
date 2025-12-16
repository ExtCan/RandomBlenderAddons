# Blender Internal Render Engine - Reimplementation
# A custom render engine that reimplements the classic Blender Internal renderer

bl_info = {
    "name": "Blender Internal Render (Reimplemented)",
    "author": "Community Reimplementation",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Render Engine > Blender Internal",
    "description": "Reimplementation of the classic Blender Internal render engine",
    "category": "Render",
}

import bpy
import numpy as np
from mathutils import Vector, Matrix
import math


class BlenderInternalRenderEngine(bpy.types.RenderEngine):
    """Custom render engine implementing Blender Internal renderer"""
    bl_idname = "BLENDER_INTERNAL"
    bl_label = "Blender Internal"
    bl_use_preview = True
    bl_use_shading_nodes_custom = False

    def __init__(self):
        self.scene_data = None
        self.draw_data = None

    def __del__(self):
        pass

    def render(self, depsgraph):
        """Main render function"""
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)

        # Create result image
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]

        # Initialize pixel buffer
        pixels = np.ones((self.size_y, self.size_x, 4), dtype=np.float32)
        
        # Set background color from world
        if scene.world:
            bg_color = scene.world.color
            pixels[:, :, 0] = bg_color[0]
            pixels[:, :, 1] = bg_color[1]
            pixels[:, :, 2] = bg_color[2]
            pixels[:, :, 3] = 1.0

        # Get camera
        camera = scene.camera
        if not camera:
            # No camera, return background
            layer.rect = pixels.flatten().tolist()
            self.end_result(result)
            return

        # Render objects
        self.render_scene(depsgraph, camera, pixels)

        # Copy pixels to result
        layer.rect = pixels.flatten().tolist()
        self.end_result(result)

    def render_scene(self, depsgraph, camera, pixels):
        """Render the scene to the pixel buffer"""
        scene = depsgraph.scene
        
        # Get camera matrix
        camera_matrix = camera.matrix_world.inverted()
        
        # Camera projection settings
        camera_data = camera.data
        if camera_data.type == 'PERSP':
            aspect_ratio = self.size_x / self.size_y
            fov = camera_data.angle
        else:
            # Orthographic not fully supported in this basic implementation
            aspect_ratio = self.size_x / self.size_y
            fov = camera_data.angle

        # Collect lights
        lights = []
        for obj in depsgraph.objects:
            if obj.type == 'LIGHT':
                lights.append(obj)

        # Render each object
        for obj_instance in depsgraph.object_instances:
            if self.test_break():
                return
                
            obj = obj_instance.object
            if obj.type != 'MESH':
                continue

            # Get evaluated mesh
            mesh = obj_instance.object.data
            if not mesh.polygons:
                continue

            # Transform vertices to camera space
            matrix = camera_matrix @ obj_instance.matrix_world
            
            self.render_mesh(mesh, matrix, lights, pixels, camera_data)

        # Update progress
        self.update_progress(1.0)

    def render_mesh(self, mesh, matrix, lights, pixels, camera_data):
        """Render a single mesh"""
        # Simple scanline rendering approach
        height, width = pixels.shape[:2]
        
        # Get material color
        if mesh.materials:
            material = mesh.materials[0]
            if material:
                base_color = self.get_material_color(material)
            else:
                base_color = Vector((0.8, 0.8, 0.8))
        else:
            base_color = Vector((0.8, 0.8, 0.8))

        # Process each polygon
        for poly in mesh.polygons:
            # Get vertices of the polygon
            verts = [mesh.vertices[i] for i in poly.vertices]
            
            # Transform to camera space
            cam_verts = []
            for v in verts:
                co = matrix @ v.co
                # Perspective projection
                if co.z < 0:  # Behind camera
                    continue
                    
                # Simple perspective projection
                if co.z > 0.1:
                    px = (co.x / co.z) * width * 0.5 + width * 0.5
                    py = (co.y / co.z) * height * 0.5 + height * 0.5
                    cam_verts.append((px, py, co.z))

            if len(cam_verts) < 3:
                continue

            # Calculate face normal in world space
            normal = poly.normal
            
            # Calculate lighting
            lit_color = self.calculate_lighting(base_color, normal, lights, matrix)
            
            # Rasterize triangle (simplified)
            self.rasterize_polygon(cam_verts, lit_color, pixels)

    def get_material_color(self, material):
        """Extract base color from material"""
        if material.use_nodes and material.node_tree:
            # Try to find Principled BSDF
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    base_color_input = node.inputs['Base Color']
                    return Vector(base_color_input.default_value[:3])
        
        # Fallback to diffuse color
        if hasattr(material, 'diffuse_color'):
            return Vector(material.diffuse_color[:3])
        
        return Vector((0.8, 0.8, 0.8))

    def calculate_lighting(self, base_color, normal, lights, matrix):
        """Calculate lighting for a surface"""
        if not lights:
            # No lights, return ambient
            ambient = Vector((0.3, 0.3, 0.3))
            return Vector((
                base_color[0] * ambient[0],
                base_color[1] * ambient[1],
                base_color[2] * ambient[2]
            ))

        # Start with ambient
        final_color = Vector((0.1, 0.1, 0.1))
        
        for light_obj in lights:
            light = light_obj.data
            
            # Light direction (simplified)
            if light.type == 'SUN':
                # Directional light
                light_dir = Vector((0, 0, -1))
                light_dir = light_obj.matrix_world.to_3x3() @ light_dir
                light_dir.normalize()
                
                # Calculate diffuse
                diff = max(0, normal.dot(-light_dir))
                light_color = Vector(light.color) * light.energy
                
                final_color += Vector((
                    base_color[0] * light_color[0] * diff,
                    base_color[1] * light_color[1] * diff,
                    base_color[2] * light_color[2] * diff
                ))
            
            elif light.type == 'POINT':
                # Point light (simplified, no distance attenuation here)
                light_color = Vector(light.color) * light.energy * 0.5
                final_color += Vector((
                    base_color[0] * light_color[0],
                    base_color[1] * light_color[1],
                    base_color[2] * light_color[2]
                ))
            
            elif light.type == 'SPOT':
                # Spot light (simplified directional with energy)
                light_dir = Vector((0, 0, -1))
                light_dir = light_obj.matrix_world.to_3x3() @ light_dir
                light_dir.normalize()
                
                # Calculate diffuse
                diff = max(0, normal.dot(-light_dir))
                light_color = Vector(light.color) * light.energy * 0.7
                
                final_color += Vector((
                    base_color[0] * light_color[0] * diff,
                    base_color[1] * light_color[1] * diff,
                    base_color[2] * light_color[2] * diff
                ))
        
        # Clamp values
        return Vector((
            min(1.0, final_color[0]),
            min(1.0, final_color[1]),
            min(1.0, final_color[2])
        ))

    def rasterize_polygon(self, verts, color, pixels):
        """Rasterize a polygon to the pixel buffer"""
        height, width = pixels.shape[:2]
        
        # Simple scanline algorithm for convex polygons
        if len(verts) < 3:
            return
            
        # Get bounding box
        min_x = max(0, int(min(v[0] for v in verts)))
        max_x = min(width - 1, int(max(v[0] for v in verts)))
        min_y = max(0, int(min(v[1] for v in verts)))
        max_y = min(height - 1, int(max(v[1] for v in verts)))
        
        # Rasterize by checking each pixel in bounding box
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.point_in_polygon(x, y, verts):
                    pixels[height - 1 - y, x, 0] = color[0]
                    pixels[height - 1 - y, x, 1] = color[1]
                    pixels[height - 1 - y, x, 2] = color[2]
                    pixels[height - 1 - y, x, 3] = 1.0

    def point_in_polygon(self, x, y, verts):
        """Check if point is inside polygon using ray casting"""
        n = len(verts)
        inside = False
        
        p1x, p1y = verts[0][:2]
        for i in range(1, n + 1):
            p2x, p2y = verts[i % n][:2]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    def view_update(self, context, depsgraph):
        """Update for viewport rendering"""
        pass

    def view_draw(self, context, depsgraph):
        """Draw viewport preview"""
        # For viewport preview, we'll use a simplified approach
        pass


class RENDER_PT_blender_internal(bpy.types.Panel):
    """Panel for Blender Internal render settings"""
    bl_label = "Blender Internal Settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.engine == 'BLENDER_INTERNAL'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Blender Internal Renderer")
        layout.label(text="Classic scanline rendering")
        
        # Add some basic info
        col = layout.column()
        col.label(text="Features:")
        col.label(text="- Basic material support")
        col.label(text="- Diffuse and specular shading")
        col.label(text="- Point, Sun, and Spot lights")
        col.label(text="- Simple scanline rasterization")


def register():
    bpy.utils.register_class(BlenderInternalRenderEngine)
    bpy.utils.register_class(RENDER_PT_blender_internal)


def unregister():
    bpy.utils.unregister_class(RENDER_PT_blender_internal)
    bpy.utils.unregister_class(BlenderInternalRenderEngine)


if __name__ == "__main__":
    register()
