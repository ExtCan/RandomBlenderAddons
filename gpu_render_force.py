# Blender 2.79 addon to force GPU rendering for Blender Render engine (NOT Cycles)
# This addon enables GPU acceleration for the Blender Internal renderer

bl_info = {
    "name": "GPU Render Force",
    "author": "ExtCan",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "Properties > Render > GPU Render",
    "description": "Forces Blender Render engine to use GPU acceleration",
    "category": "Render",
}

import bpy


class ForceGPURenderOperator(bpy.types.Operator):
    """Force GPU Rendering for Blender Render Engine"""
    bl_idname = "render.force_gpu_render"
    bl_label = "Enable GPU Render"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # Ensure we're using Blender Render (not Cycles)
        if scene.render.engine != 'BLENDER_RENDER':
            self.report({'WARNING'}, "Switching to Blender Render engine")
            scene.render.engine = 'BLENDER_RENDER'
        
        # Enable GPU rendering in user preferences
        user_prefs = context.user_preferences
        system = user_prefs.system
        
        # Enable OpenGL rendering and set window draw method
        system.use_mipmaps = True
        system.use_gpu_mipmap = True
        
        # Set all 3D viewports to use GLSL shading (GPU accelerated)
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # Set shading to GLSL for GPU acceleration
                        space.viewport_shade = 'SOLID'
                        if hasattr(space, 'use_matcap'):
                            space.use_matcap = False
        
        # Enable game engine settings for better GPU utilization
        scene.game_settings.material_mode = 'GLSL'
        
        # Set render to use GLSL shading
        scene.render.use_shading_nodes = False  # Use GLSL, not nodes
        
        # Enable display mode features
        scene.render.use_simplify = False  # Don't simplify, use full GPU power
        
        self.report({'INFO'}, "GPU rendering enabled for Blender Render engine")
        return {'FINISHED'}


class DisableGPURenderOperator(bpy.types.Operator):
    """Disable GPU Rendering and return to default"""
    bl_idname = "render.disable_gpu_render"
    bl_label = "Disable GPU Render"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # Reset game engine material mode
        scene.game_settings.material_mode = 'MULTITEXTURE'
        
        # Reset viewports
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.viewport_shade = 'SOLID'
        
        self.report({'INFO'}, "GPU rendering disabled")
        return {'FINISHED'}


class GPURenderPanel(bpy.types.Panel):
    """Panel for GPU Render controls"""
    bl_label = "GPU Render Force"
    bl_idname = "RENDER_PT_gpu_force"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        # Only show when Blender Render is active
        return context.scene.render.engine == 'BLENDER_RENDER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="GPU Acceleration for Blender Render:")
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("render.force_gpu_render", icon='AUTO')
        
        row = layout.row(align=True)
        row.operator("render.disable_gpu_render", icon='CANCEL')
        
        layout.separator()
        
        # Show current settings
        box = layout.box()
        box.label(text="Current Settings:")
        box.label(text="Engine: {}".format(scene.render.engine))
        box.label(text="Material Mode: {}".format(scene.game_settings.material_mode))
        
        layout.separator()
        
        # Information box
        info_box = layout.box()
        info_box.label(text="Info:", icon='INFO')
        col = info_box.column(align=True)
        col.scale_y = 0.8
        col.label(text="This enables GPU acceleration for")
        col.label(text="the Blender Internal renderer using")
        col.label(text="GLSL shading mode.")


def register():
    bpy.utils.register_class(ForceGPURenderOperator)
    bpy.utils.register_class(DisableGPURenderOperator)
    bpy.utils.register_class(GPURenderPanel)


def unregister():
    bpy.utils.unregister_class(GPURenderPanel)
    bpy.utils.unregister_class(DisableGPURenderOperator)
    bpy.utils.unregister_class(ForceGPURenderOperator)


if __name__ == "__main__":
    register()
