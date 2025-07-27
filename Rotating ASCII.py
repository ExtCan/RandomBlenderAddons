import bpy
from mathutils import Vector

bl_info = {
    "name": "Rotating ASCII Exporter",
    "author": "Grok and ME BITCH",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Object",
    "description": "Exports selected mesh to a rotating ASCII Python script",
    "category": "Export",
}

class RotatingASCIIProperties(bpy.types.PropertyGroup):
    width: bpy.props.IntProperty(
        name="Width",
        default=80,
        min=10,
        description="Width of the ASCII canvas"
    )
    height: bpy.props.IntProperty(
        name="Height",
        default=24,
        min=5,
        description="Height of the ASCII canvas"
    )
    scale_x: bpy.props.FloatProperty(
        name="Scale X",
        default=20.0,
        description="Horizontal scaling factor"
    )
    scale_y: bpy.props.FloatProperty(
        name="Scale Y",
        default=10.0,
        description="Vertical scaling factor"
    )
    dist: bpy.props.FloatProperty(
        name="Distance",
        default=4.0,
        min=1.0,
        description="Perspective distance (zoom)"
    )
    line_char: bpy.props.StringProperty(
        name="Line Char",
        default="#",
        maxlen=1,
        description="Character used for drawing lines"
    )
    pause: bpy.props.FloatProperty(
        name="Pause",
        default=0.05,
        min=0.001,
        description="Delay between frames in seconds"
    )
    rot_speed_x: bpy.props.FloatProperty(
        name="Rot Speed X",
        default=0.03,
        description="Rotation speed around X axis"
    )
    rot_speed_y: bpy.props.FloatProperty(
        name="Rot Speed Y",
        default=0.02,
        description="Rotation speed around Y axis"
    )
    rot_speed_z: bpy.props.FloatProperty(
        name="Rot Speed Z",
        default=0.01,
        description="Rotation speed around Z axis"
    )
    use_vertex_colors: bpy.props.BoolProperty(
        name="Use Vertex Colors",
        default=False,
        description="Include vertex colors in the animation using ANSI colors (requires per-vertex colors)"
    )

class RotatingASCIIOperator(bpy.types.Operator):
    """Export Selected Object to Rotating ASCII Script"""
    bl_idname = "object.export_rotating_ascii"
    bl_label = "Export Rotating ASCII"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        mesh = obj.data

        # Compute center and scale to normalize to unit size
        if len(mesh.vertices) == 0:
            self.report({'ERROR'}, "Mesh has no vertices")
            return {'CANCELLED'}

        center = sum((Vector(v.co) for v in mesh.vertices), Vector((0,0,0))) / len(mesh.vertices)
        max_dist = max((Vector(v.co) - center).length for v in mesh.vertices)
        scale_factor = 1.0 / max_dist if max_dist > 0 else 1.0

        # Get properties
        props = context.scene.rotating_ascii_props

        # Check for vertex colors
        color_attr = mesh.color_attributes.active_color
        include_colors = props.use_vertex_colors and color_attr and color_attr.domain == 'POINT'
        if props.use_vertex_colors and not include_colors:
            self.report({'WARNING'}, "Vertex colors not available or not per-vertex. Proceeding without colors.")

        # Normalized vertices as list of tuples
        vertices = []
        if include_colors:
            for i, v in enumerate(mesh.vertices):
                vert = (Vector(v.co) - center) * scale_factor
                col = color_attr.data[i].color
                r = int(col[0] * 255)
                g = int(col[1] * 255)
                b = int(col[2] * 255)
                vertices.append((vert.x, vert.y, vert.z, r, g, b))
        else:
            for v in mesh.vertices:
                vert = (Vector(v.co) - center) * scale_factor
                vertices.append((vert.x, vert.y, vert.z))

        # Edges as list of tuples
        edges = [(e.vertices[0], e.vertices[1]) for e in mesh.edges]

        # Generate the Python script
        script = f"""import math
import time
import os
import sys

# Constants
WIDTH = {props.width}
HEIGHT = {props.height}
SCALE_X = {props.scale_x}
SCALE_Y = {props.scale_y}
TRANSLATE_X = WIDTH // 2
TRANSLATE_Y = HEIGHT // 2
LINE_CHAR = '{props.line_char}'
PAUSE = {props.pause}
DIST = {props.dist}  # Distance for perspective

# Object vertices
vertices = [
"""
        for v in vertices:
            script += f"    {v},\n"
        script += """]

# Edges connecting the vertices
edges = [
"""
        for e in edges:
            script += f"    {e},\n"
        script += """]

def rotate_point(x, y, z, angle_x, angle_y, angle_z):
    # Rotate around X axis
    cos_x = math.cos(angle_x)
    sin_x = math.sin(angle_x)
    y1 = y * cos_x - z * sin_x
    z1 = y * sin_x + z * cos_x

    # Rotate around Y axis
    cos_y = math.cos(angle_y)
    sin_y = math.sin(angle_y)
    x2 = x * cos_y + z1 * sin_y
    z2 = -x * sin_y + z1 * cos_y

    # Rotate around Z axis
    cos_z = math.cos(angle_z)
    sin_z = math.sin(angle_z)
    x3 = x2 * cos_z - y1 * sin_z
    y3 = x2 * sin_z + y1 * cos_z

    return x3, y3, z2

def bresenham(x1, y1, x2, y2, color1=None, color2=None):
    points = []
    use_col = color1 is not None and color2 is not None
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    steps = max(dx, dy, 1)  # Avoid division by zero
    k = 0
    current_x, current_y = x1, y1
    while True:
        if use_col:
            fraction = k / steps
            cr = int(color1[0] + fraction * (color2[0] - color1[0]))
            cg = int(color1[1] + fraction * (color2[1] - color1[1]))
            cb = int(color1[2] + fraction * (color2[2] - color1[2]))
            points.append((current_x, current_y, (cr, cg, cb)))
        else:
            points.append((current_x, current_y))
        if current_x == x2 and current_y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            current_x += sx
        if e2 < dx:
            err += dx
            current_y += sy
        k += 1
    return points

try:
    use_colors = len(vertices[0]) > 3 if vertices else False
    angle_x = 0
    angle_y = 0
    angle_z = 0
    while True:
        # Rotate all vertices
        rotated = []
        for vertex in vertices:
            if use_colors:
                rx, ry, rz = rotate_point(*vertex[:3], angle_x, angle_y, angle_z)
                rotated.append((rx, ry, rz, *vertex[3:]))
            else:
                rx, ry, rz = rotate_point(*vertex, angle_x, angle_y, angle_z)
                rotated.append((rx, ry, rz))

        # Project to 2D with perspective
        projected = []
        for rx, ry, rz, *rest in rotated:
            # Perspective factor
            factor = DIST / (DIST + rz + 2)  # Add 2 to shift z positive
            px = int(TRANSLATE_X + factor * rx * SCALE_X)
            py = int(TRANSLATE_Y - factor * ry * SCALE_Y)  # Invert y for screen coords
            projected.append((px, py))

        # Collect all points on the edges
        if use_colors:
            object_points = {}
        else:
            object_points = set()
        for i, j in edges:
            if use_colors:
                color1 = rotated[i][3:]
                color2 = rotated[j][3:]
                line_points = bresenham(*projected[i], *projected[j], color1, color2)
                for pt in line_points:
                    px, py, col = pt
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        object_points[(px, py)] = col  # Last write wins
            else:
                line_points = bresenham(*projected[i], *projected[j])
                for pt in line_points:
                    px, py = pt
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        object_points.add((px, py))

        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')

        # Draw the frame
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if use_colors:
                    col = object_points.get((x, y))
                    if col:
                        r, g, b = col
                        sys.stdout.write("\\033[38;2;{0};{1};{2}m{3}\\033[0m".format(r, g, b, LINE_CHAR))
                    else:
                        sys.stdout.write(' ')
                else:
                    if (x, y) in object_points:
                        sys.stdout.write(LINE_CHAR)
                    else:
                        sys.stdout.write(' ')
            sys.stdout.write('\\n')
        sys.stdout.flush()

"""
        script += f"""
        # Update angles
        angle_x += {props.rot_speed_x}
        angle_y += {props.rot_speed_y}
        angle_z += {props.rot_speed_z}

        time.sleep(PAUSE)
except KeyboardInterrupt:
    print("\\nAnimation stopped.")
except Exception as e:
    print("Error:", e)
finally:
    input("Press Enter to exit...")
"""

        # Save the script to the same directory as the .blend file
        if bpy.data.filepath:
            filepath = bpy.path.abspath("//rotating_ascii.py")
        else:
            filepath = "rotating_ascii.py"  # Current directory if unsaved

        with open(filepath, 'w') as f:
            f.write(script)

        self.report({'INFO'}, f"Rotating ASCII script saved to {filepath}")
        return {'FINISHED'}

class RotatingASCIIPanel(bpy.types.Panel):
    bl_label = "Rotating ASCII"
    bl_idname = "VIEW3D_PT_rotating_ascii"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ASCII"

    def draw(self, context):
        layout = self.layout
        props = context.scene.rotating_ascii_props
        layout.prop(props, "width")
        layout.prop(props, "height")
        layout.prop(props, "scale_x")
        layout.prop(props, "scale_y")
        layout.prop(props, "dist")
        layout.prop(props, "line_char")
        layout.prop(props, "pause")
        layout.prop(props, "rot_speed_x")
        layout.prop(props, "rot_speed_y")
        layout.prop(props, "rot_speed_z")
        layout.prop(props, "use_vertex_colors")
        layout.operator("object.export_rotating_ascii")

def menu_func(self, context):
    self.layout.operator(RotatingASCIIOperator.bl_idname)

def register():
    bpy.utils.register_class(RotatingASCIIProperties)
    bpy.utils.register_class(RotatingASCIIOperator)
    bpy.utils.register_class(RotatingASCIIPanel)
    bpy.types.Scene.rotating_ascii_props = bpy.props.PointerProperty(type=RotatingASCIIProperties)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    del bpy.types.Scene.rotating_ascii_props
    bpy.utils.unregister_class(RotatingASCIIPanel)
    bpy.utils.unregister_class(RotatingASCIIOperator)
    bpy.utils.unregister_class(RotatingASCIIProperties)

if __name__ == "__main__":
    register()