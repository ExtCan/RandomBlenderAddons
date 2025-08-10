# Addon to turn image pixels into colored cubes in Blender 4.0 as a single optimized mesh
# Location: View3D > Add > Image > Pixel Cubes

bl_info = {
    "name": "Pixel Cubes from Image",
    "author": "Groky-Chan and Pink",
    "version": (1, 2),
    "blender": (4, 0, 0),
    "location": "View3D > Add > Image > Pixel Cubes",
    "description": "Creates a colored cube for each pixel in an image as a single optimized mesh",
    "category": "Add Mesh",
}

import bpy

class OBJECT_OT_add_pixel_cubes(bpy.types.Operator):
    """Add Pixel Cubes from Image"""
    bl_idname = "object.add_pixel_cubes"
    bl_label = "Add Pixel Cubes"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(
        name="Image File",
        subtype='FILE_PATH',
    )

    scale: bpy.props.FloatProperty(
        name="Cube Scale",
        description="Size of each cube",
        default=1.0,
        min=0.001,
    )

    skip_transparent: bpy.props.BoolProperty(
        name="Skip Transparent Pixels",
        description="Don't create cubes for pixels with alpha < 0.5",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No image file selected!")
            return {'CANCELLED'}

        try:
            img = bpy.data.images.load(self.filepath, check_existing=True)
        except RuntimeError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        w, h = img.size
        if w == 0 or h == 0:
            self.report({'ERROR'}, "Invalid image size!")
            return {'CANCELLED'}

        pixels = img.pixels[:]

        # Collect unique colors
        color_dict = {}
        color_list = []
        mat_index = 0

        for i in range(w):
            for j in range(h):
                idx = (j * w + i) * 4
                r, g, b, a = pixels[idx:idx + 4]

                if self.skip_transparent and a < 0.5:
                    continue

                color_key = tuple(round(c, 4) for c in (r, g, b))

                if color_key not in color_dict:
                    color_dict[color_key] = mat_index
                    color_list.append(color_key)
                    mat_index += 1

        # Create materials
        materials = []
        for color_key in color_list:
            color = (*color_key, 1.0)
            mat = bpy.data.materials.new(name=f"PixelColor_{color_key}")
            mat.use_nodes = True

            # Remove default Principled BSDF
            principled = mat.node_tree.nodes.get("Principled BSDF")
            if principled:
                mat.node_tree.nodes.remove(principled)

            # Add Diffuse BSDF
            diffuse = mat.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
            diffuse.inputs['Color'].default_value = color
            diffuse.inputs['Roughness'].default_value = 1.0

            # Connect to Material Output
            output = mat.node_tree.nodes.get("Material Output")
            mat.node_tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])

            materials.append(mat)

        # Now build the mesh
        verts = []
        faces = []
        poly_mats = []

        half = self.scale / 2
        vert_offset = 0

        for i in range(w):
            for j in range(h):
                idx = (j * w + i) * 4
                r, g, b, a = pixels[idx:idx + 4]

                if self.skip_transparent and a < 0.5:
                    continue

                color_key = tuple(round(c, 4) for c in (r, g, b))
                mat_idx = color_dict[color_key]

                x = i * self.scale
                y = j * self.scale
                z = 0.0

                # Add 8 vertices
                verts.extend([
                    (x - half, y - half, z - half),
                    (x + half, y - half, z - half),
                    (x + half, y + half, z - half),
                    (x - half, y + half, z - half),
                    (x - half, y - half, z + half),
                    (x + half, y - half, z + half),
                    (x + half, y + half, z + half),
                    (x - half, y + half, z + half),
                ])

                # Add 6 faces (quads)
                faces.extend([
                    (vert_offset + 0, vert_offset + 1, vert_offset + 2, vert_offset + 3),  # bottom
                    (vert_offset + 4, vert_offset + 5, vert_offset + 6, vert_offset + 7),  # top
                    (vert_offset + 0, vert_offset + 1, vert_offset + 5, vert_offset + 4),  # front
                    (vert_offset + 3, vert_offset + 2, vert_offset + 6, vert_offset + 7),  # back
                    (vert_offset + 0, vert_offset + 3, vert_offset + 7, vert_offset + 4),  # left
                    (vert_offset + 1, vert_offset + 2, vert_offset + 6, vert_offset + 5),  # right
                ])

                # Add material index for each of the 6 faces
                poly_mats.extend([mat_idx] * 6)

                vert_offset += 8

        # Create mesh and object
        mesh = bpy.data.meshes.new("PixelCubes")
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        obj = bpy.data.objects.new("PixelCubes", mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # Add materials to object
        for mat in materials:
            obj.data.materials.append(mat)

        # Assign material indices to polygons
        for poly_idx, poly in enumerate(mesh.polygons):
            poly.material_index = poly_mats[poly_idx]

        # Clean up the image if not used elsewhere
        if len(img.users) == 0:
            bpy.data.images.remove(img)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_add_pixel_cubes.bl_idname, text="Pixel Cubes")

def register():
    bpy.utils.register_class(OBJECT_OT_add_pixel_cubes)
    bpy.types.VIEW3D_MT_image_add.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_image_add.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_add_pixel_cubes)

if __name__ == "__main__":
    register()