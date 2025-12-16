# Blender 2.79 Modernizer Addon
# Brings modern Blender 2.80+ features and shortcuts to Blender 2.79

bl_info = {
    "name": "Blender 2.79 Modernizer",
    "author": "ExtCan Contributors",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "User Preferences > Addons",
    "description": "Modernizes Blender 2.79 with features and shortcuts from Blender 2.80+",
    "warning": "",
    "category": "System",
}

import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    AddonPreferences,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
)


# ============================================================================
# Addon Preferences
# ============================================================================

class ModernizerPreferences(AddonPreferences):
    bl_idname = __name__
    
    enable_left_click_select = BoolProperty(
        name="Left Click Select",
        description="Enable left click for selection (like Blender 2.80+)",
        default=True,
    )
    
    enable_spacebar_search = BoolProperty(
        name="Spacebar for Search",
        description="Use Spacebar to open search menu instead of play animation",
        default=True,
    )
    
    enable_modern_transform = BoolProperty(
        name="Modern Transform Tools",
        description="Enable modern transform tool behavior",
        default=True,
    )
    
    enable_collection_manager = BoolProperty(
        name="Collection Manager",
        description="Enable collection-like management for groups",
        default=True,
    )
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Keyboard Shortcuts:", icon='PREFERENCES')
        box.prop(self, "enable_left_click_select")
        box.prop(self, "enable_spacebar_search")
        box.prop(self, "enable_modern_transform")
        
        box = layout.box()
        box.label(text="Workflow Features:", icon='SCENE')
        box.prop(self, "enable_collection_manager")
        
        layout.separator()
        layout.label(text="Note: Restart Blender after changing keymap settings", icon='INFO')


# ============================================================================
# Collection-like Group Management
# ============================================================================

class OBJECT_OT_create_collection(Operator):
    """Create a new collection (group) for organizing objects"""
    bl_idname = "object.create_collection"
    bl_label = "New Collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name = StringProperty(
        name="Name",
        description="Name for the new collection",
        default="Collection",
    )
    
    def execute(self, context):
        # Create a new group (Collections equivalent in 2.79)
        bpy.data.groups.new(name=self.collection_name)
        self.report({'INFO'}, "Created collection: {}".format(self.collection_name))
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_add_to_collection(Operator):
    """Add selected objects to a collection (group)"""
    bl_idname = "object.add_to_collection"
    bl_label = "Add to Collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name = StringProperty(
        name="Collection",
        description="Collection to add objects to",
    )
    
    def execute(self, context):
        if not self.collection_name:
            self.report({'WARNING'}, "No collection specified")
            return {'CANCELLED'}
        
        # Get or create the group
        if self.collection_name in bpy.data.groups:
            group = bpy.data.groups[self.collection_name]
        else:
            group = bpy.data.groups.new(name=self.collection_name)
        
        # Add selected objects to group
        # Get existing object names for efficient lookup
        existing_names = {obj.name for obj in group.objects}
        added_count = 0
        for obj in context.selected_objects:
            if obj.name not in existing_names:
                group.objects.link(obj)
                added_count += 1
        
        self.report({'INFO'}, "Added {} object(s) to {}".format(added_count, self.collection_name))
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class OBJECT_OT_remove_from_collection(Operator):
    """Remove selected objects from a collection (group)"""
    bl_idname = "object.remove_from_collection"
    bl_label = "Remove from Collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name = StringProperty(
        name="Collection",
        description="Collection to remove objects from",
    )
    
    def execute(self, context):
        if not self.collection_name or self.collection_name not in bpy.data.groups:
            self.report({'WARNING'}, "Collection not found")
            return {'CANCELLED'}
        
        group = bpy.data.groups[self.collection_name]
        # Get existing object names for efficient lookup
        existing_names = {obj.name for obj in group.objects}
        removed_count = 0
        
        for obj in context.selected_objects:
            if obj.name in existing_names:
                group.objects.unlink(obj)
                removed_count += 1
        
        self.report({'INFO'}, "Removed {} object(s) from {}".format(removed_count, self.collection_name))
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# ============================================================================
# Modern UI Panel
# ============================================================================

class VIEW3D_PT_modern_collections(Panel):
    """Panel for collection management"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Collections"
    bl_label = "Collections Manager"
    bl_context = "objectmode"
    
    @classmethod
    def poll(cls, context):
        prefs = context.user_preferences.addons.get(__name__)
        if prefs:
            return prefs.preferences.enable_collection_manager
        return True
    
    def draw(self, context):
        layout = self.layout
        
        # Create new collection button
        layout.operator("object.create_collection", icon='GROUP')
        
        layout.separator()
        
        # List existing collections (groups)
        if bpy.data.groups:
            box = layout.box()
            box.label(text="Existing Collections:")
            for group in bpy.data.groups:
                row = box.row(align=True)
                row.label(text=group.name, icon='GROUP')
                
                # Show object count
                row.label(text="({})".format(len(group.objects)))
                
                # Add/Remove operators
                op = row.operator("object.add_to_collection", text="", icon='ZOOMIN')
                op.collection_name = group.name
                
                op = row.operator("object.remove_from_collection", text="", icon='ZOOMOUT')
                op.collection_name = group.name
        else:
            layout.label(text="No collections yet", icon='INFO')
        
        # Show selected objects
        if context.selected_objects:
            layout.separator()
            box = layout.box()
            box.label(text="Selected: {} object(s)".format(len(context.selected_objects)))


# ============================================================================
# Quick Search Operator (Spacebar Search)
# ============================================================================

class SCREEN_OT_modern_search_menu(Operator):
    """Open search menu (like Blender 2.80+ Spacebar Search)"""
    bl_idname = "screen.modern_search_menu"
    bl_label = "Search Menu"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Open the search menu
        bpy.ops.wm.search_menu('INVOKE_DEFAULT')
        return {'FINISHED'}


# ============================================================================
# Modern Viewport Navigation Helpers
# ============================================================================

class VIEW3D_OT_modern_frame_selected(Operator):
    """Frame selected objects (improved version)"""
    bl_idname = "view3d.modern_frame_selected"
    bl_label = "Frame Selected"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if context.selected_objects:
            bpy.ops.view3d.view_selected()
        else:
            self.report({'INFO'}, "No objects selected")
        return {'FINISHED'}


class VIEW3D_OT_modern_frame_all(Operator):
    """Frame all objects (improved version)"""
    bl_idname = "view3d.modern_frame_all"
    bl_label = "Frame All"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.ops.view3d.view_all()
        return {'FINISHED'}


# ============================================================================
# Keymap Management
# ============================================================================

addon_keymaps = []

def register_keymaps():
    """Register modern keymaps"""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    
    if not kc:
        return
    
    prefs = bpy.context.user_preferences.addons.get(__name__)
    if not prefs:
        return
    
    # Spacebar for Search (instead of play animation)
    if prefs.preferences.enable_spacebar_search:
        km = kc.keymaps.new(name='Screen', space_type='EMPTY')
        kmi = km.keymap_items.new("screen.modern_search_menu", 'SPACE', 'PRESS')
        addon_keymaps.append((km, kmi))
    
    # Modern navigation shortcuts
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    
    # Numpad Period to frame selected (modern shortcut)
    kmi = km.keymap_items.new("view3d.modern_frame_selected", 'NUMPAD_PERIOD', 'PRESS')
    addon_keymaps.append((km, kmi))
    
    # Home key to frame all
    kmi = km.keymap_items.new("view3d.modern_frame_all", 'HOME', 'PRESS')
    addon_keymaps.append((km, kmi))


def unregister_keymaps():
    """Unregister addon keymaps"""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ============================================================================
# Registration
# ============================================================================

classes = (
    ModernizerPreferences,
    OBJECT_OT_create_collection,
    OBJECT_OT_add_to_collection,
    OBJECT_OT_remove_from_collection,
    VIEW3D_PT_modern_collections,
    SCREEN_OT_modern_search_menu,
    VIEW3D_OT_modern_frame_selected,
    VIEW3D_OT_modern_frame_all,
)


def register():
    """Register addon"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register keymaps after ensuring preferences are available
    try:
        register_keymaps()
    except (AttributeError, KeyError, TypeError) as e:
        # Keymap registration may fail if preferences aren't ready yet
        # This is expected on initial load and can be safely ignored
        pass


def unregister():
    """Unregister addon"""
    unregister_keymaps()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
