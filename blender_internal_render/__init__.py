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
Blender Internal Render Engine Addon

This addon restores the Blender Internal (BI) render engine UI panels
from Blender 2.79 for use in modern Blender versions.

IMPORTANT LIMITATIONS:
- This addon only provides the UI panels and interface
- The actual C/C++ render engine code is NOT included (it was removed from Blender)
- Rendering will not work without the original render engine implementation
- This addon is primarily for compatibility, reference, and educational purposes

The addon includes:
- Render settings panels
- Material system (diffuse, specular, transparency, mirrors, SSS, etc.)
- Texture system and texture slots
- World/environment settings
- Lamp/light settings for BI render engine
- Render layers and passes

Based on Blender 2.79 source code:
https://github.com/ExtCan/blender-AI-edits/tree/v2.79
"""

bl_info = {
    "name": "Blender Internal Render Engine",
    "author": "Blender Foundation (original), ExtCan (addon port)",
    "version": (2, 79, 0),
    "blender": (3, 0, 0),
    "location": "Properties > Render",
    "description": "Restore Blender Internal render engine UI from Blender 2.79 (UI only, core rendering not included)",
    "warning": "UI only - actual rendering requires the original C-level render engine",
    "doc_url": "https://github.com/ExtCan/RandomBlenderAddons",
    "category": "Render",
}

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

# Import UI modules
from . import (
    ui_render,
    ui_render_layer,
    ui_material,
    ui_texture,
    ui_world,
    ui_lamp,
)


class BlenderInternalPreferences(AddonPreferences):
    bl_idname = __name__

    show_warning: BoolProperty(
        name="Show Compatibility Warning",
        description="Display a warning about render engine limitations",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        
        if self.show_warning:
            box = layout.box()
            box.label(text="⚠ IMPORTANT COMPATIBILITY NOTICE ⚠", icon='ERROR')
            box.label(text="This addon only restores the UI panels from Blender 2.79.")
            box.label(text="The actual Blender Internal render engine (C/C++ code) is NOT included.")
            box.label(text="Rendering will not work without the original render engine implementation.")
            box.label(text="This addon is for reference, compatibility, and educational purposes only.")
            
        layout.prop(self, "show_warning")


# Module management
modules = [
    ui_render,
    ui_render_layer,
    ui_material,
    ui_texture,
    ui_world,
    ui_lamp,
]


def register():
    # Register preferences first
    bpy.utils.register_class(BlenderInternalPreferences)
    
    # Register all modules
    for mod in modules:
        mod.register()
    
    print("Blender Internal Render Engine addon loaded (UI only)")


def unregister():
    # Unregister in reverse order
    for mod in reversed(modules):
        mod.unregister()
    
    bpy.utils.unregister_class(BlenderInternalPreferences)
    
    print("Blender Internal Render Engine addon unloaded")


if __name__ == "__main__":
    register()
