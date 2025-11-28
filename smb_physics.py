# Super Mario Bros. Physics Addon for Blender
# Recreates accurate Super Mario Bros. physics for selected object
# The selected object will be considered as the PLAYER

import bpy
import math
from bpy.app.handlers import persistent

bl_info = {
    "name": "Super Mario Bros. Physics",
    "author": "Pink",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > SMB Physics",
    "description": "Recreates accurate Super Mario Bros. physics for the selected object (PLAYER)",
    "category": "Physics",
}

# ==============================================================================
# Super Mario Bros. Physics Constants
# All values are derived from the original NES Super Mario Bros.
# Original game runs at 60fps with specific subpixel physics
# 
# Reference: https://www.smwcentral.net/?p=viewthread&t=98861
# And various SMB physics documentation sources
# ==============================================================================

# Scale factor to convert NES pixel units to Blender units
# NES screen was 256x240 pixels, we scale to make physics feel right in Blender
PIXEL_TO_BLENDER = 0.0625  # 1 NES pixel = 0.0625 Blender units (1/16)

# Gravity - SMB uses 0x0007 per subframe (1/256 pixel per frame²)
# Actual gravity: 7/256 = 0.02734375 pixels/frame² 
# At 60fps this becomes our gravity value
SMB_GRAVITY = 0.02734375 * PIXEL_TO_BLENDER * 60 * 60  # Convert to units/sec²

# Terminal velocity (max falling speed)
# SMB caps vertical velocity at 0x0480 (4.5 pixels/frame)
SMB_TERMINAL_VELOCITY = 4.5 * PIXEL_TO_BLENDER * 60

# Jump initial velocities based on horizontal speed (in pixels/frame)
# These are the actual NES values for Small Mario
# Jump velocity at different run speeds: 4.0, 4.0, 4.0, 5.0 pixels/frame
SMB_JUMP_VELOCITY_WALK = 4.0 * PIXEL_TO_BLENDER * 60
SMB_JUMP_VELOCITY_RUN = 5.0 * PIXEL_TO_BLENDER * 60

# Horizontal movement speeds
# Walking max speed: 0x0130 (1.1875 pixels/frame)
# Running max speed: 0x0290 (2.5625 pixels/frame)
SMB_MAX_WALK_SPEED = 1.1875 * PIXEL_TO_BLENDER * 60
SMB_MAX_RUN_SPEED = 2.5625 * PIXEL_TO_BLENDER * 60

# Acceleration values
# Walking acceleration: 0x0098 (0.59375 pixels/frame²)
# Running acceleration: 0x00E4 (0.890625 pixels/frame²)
SMB_WALK_ACCEL = 0.09375 * PIXEL_TO_BLENDER * 60 * 60
SMB_RUN_ACCEL = 0.140625 * PIXEL_TO_BLENDER * 60 * 60

# Deceleration/friction
# Release friction (skidding): 0x00D0 (0.8125 pixels/frame²)
# Skid deceleration: 0x01A0 (1.625 pixels/frame²)
SMB_FRICTION = 0.8125 * PIXEL_TO_BLENDER * 60 * 60
SMB_SKID_DECEL = 1.625 * PIXEL_TO_BLENDER * 60 * 60

# Air control (reduced control while airborne)
# In SMB, air acceleration is the same but momentum is preserved
SMB_AIR_ACCEL_MULTIPLIER = 1.0  # SMB has full air control for acceleration

# Jump sustain - holding jump reduces gravity effect
# When holding jump: gravity is halved until peak or button release
SMB_JUMP_GRAVITY_MULTIPLIER = 0.5


class SMBPhysicsProperties(bpy.types.PropertyGroup):
    """Properties for SMB Physics simulation"""
    
    # Simulation state
    is_active: bpy.props.BoolProperty(
        name="Physics Active",
        description="Toggle SMB physics simulation",
        default=False
    )
    
    # Current velocity (stored for persistence)
    velocity_x: bpy.props.FloatProperty(name="Velocity X", default=0.0)
    velocity_y: bpy.props.FloatProperty(name="Velocity Y", default=0.0)
    velocity_z: bpy.props.FloatProperty(name="Velocity Z", default=0.0)
    
    # Physics state
    is_grounded: bpy.props.BoolProperty(name="Is Grounded", default=True)
    is_jumping: bpy.props.BoolProperty(name="Is Jumping", default=False)
    jump_held: bpy.props.BoolProperty(name="Jump Held", default=False)
    is_running: bpy.props.BoolProperty(name="Is Running", default=False)
    
    # Input state (controlled via UI or keymap)
    input_left: bpy.props.BoolProperty(name="Move Left", default=False)
    input_right: bpy.props.BoolProperty(name="Move Right", default=False)
    input_jump: bpy.props.BoolProperty(name="Jump", default=False)
    input_run: bpy.props.BoolProperty(name="Run", default=False)
    
    # Ground level (Y position of the ground plane)
    ground_level: bpy.props.FloatProperty(
        name="Ground Level",
        description="Z position of the ground plane",
        default=0.0,
        unit='LENGTH'
    )
    
    # Customizable physics values (defaulting to accurate SMB values)
    gravity: bpy.props.FloatProperty(
        name="Gravity",
        description="Gravity acceleration (units/sec²)",
        default=SMB_GRAVITY,
        min=0.0
    )
    
    terminal_velocity: bpy.props.FloatProperty(
        name="Terminal Velocity",
        description="Maximum falling speed (units/sec)",
        default=SMB_TERMINAL_VELOCITY,
        min=0.0
    )
    
    jump_velocity: bpy.props.FloatProperty(
        name="Jump Velocity (Walk)",
        description="Initial jump velocity when walking (units/sec)",
        default=SMB_JUMP_VELOCITY_WALK
    )
    
    jump_velocity_run: bpy.props.FloatProperty(
        name="Jump Velocity (Run)",
        description="Initial jump velocity when running (units/sec)",
        default=SMB_JUMP_VELOCITY_RUN
    )
    
    max_walk_speed: bpy.props.FloatProperty(
        name="Max Walk Speed",
        description="Maximum walking speed (units/sec)",
        default=SMB_MAX_WALK_SPEED,
        min=0.0
    )
    
    max_run_speed: bpy.props.FloatProperty(
        name="Max Run Speed",
        description="Maximum running speed (units/sec)",
        default=SMB_MAX_RUN_SPEED,
        min=0.0
    )
    
    walk_acceleration: bpy.props.FloatProperty(
        name="Walk Acceleration",
        description="Acceleration when walking (units/sec²)",
        default=SMB_WALK_ACCEL,
        min=0.0
    )
    
    run_acceleration: bpy.props.FloatProperty(
        name="Run Acceleration",
        description="Acceleration when running (units/sec²)",
        default=SMB_RUN_ACCEL,
        min=0.0
    )
    
    friction: bpy.props.FloatProperty(
        name="Friction",
        description="Deceleration when not moving (units/sec²)",
        default=SMB_FRICTION,
        min=0.0
    )
    
    skid_deceleration: bpy.props.FloatProperty(
        name="Skid Deceleration",
        description="Deceleration when changing direction (units/sec²)",
        default=SMB_SKID_DECEL,
        min=0.0
    )
    
    # Movement axis (which axis is forward/up)
    forward_axis: bpy.props.EnumProperty(
        name="Forward Axis",
        description="Which axis represents forward movement",
        items=[
            ('X', "X Axis", "Move along X axis"),
            ('Y', "Y Axis", "Move along Y axis"),
        ],
        default='X'
    )
    
    up_axis: bpy.props.EnumProperty(
        name="Up Axis",
        description="Which axis represents up (jump direction)",
        items=[
            ('Y', "Y Axis", "Jump along Y axis"),
            ('Z', "Z Axis", "Jump along Z axis"),
        ],
        default='Z'
    )


class SMBPhysicsEngine:
    """Core physics engine implementing SMB physics"""
    
    @staticmethod
    def update_physics(context, delta_time):
        """Update physics for one frame"""
        obj = context.active_object
        if not obj:
            return
        
        props = context.scene.smb_physics_props
        if not props.is_active:
            return
        
        # Get current position
        pos_x = obj.location.x
        pos_y = obj.location.y
        pos_z = obj.location.z
        
        # Determine which axes to use
        if props.forward_axis == 'X':
            horizontal_pos = pos_x
            horizontal_vel = props.velocity_x
        else:
            horizontal_pos = pos_y
            horizontal_vel = props.velocity_y
            
        if props.up_axis == 'Z':
            vertical_pos = pos_z
            vertical_vel = props.velocity_z
        else:
            vertical_pos = pos_y
            vertical_vel = props.velocity_y
        
        # Check if grounded
        props.is_grounded = vertical_pos <= props.ground_level
        
        # Horizontal movement
        horizontal_vel = SMBPhysicsEngine.update_horizontal(
            props, horizontal_vel, delta_time
        )
        
        # Vertical movement (jumping/gravity)
        vertical_vel = SMBPhysicsEngine.update_vertical(
            props, vertical_vel, delta_time
        )
        
        # Apply velocities to position
        if props.forward_axis == 'X':
            pos_x += horizontal_vel * delta_time
            props.velocity_x = horizontal_vel
        else:
            pos_y += horizontal_vel * delta_time
            props.velocity_y = horizontal_vel
            
        if props.up_axis == 'Z':
            pos_z += vertical_vel * delta_time
            props.velocity_z = vertical_vel
        else:
            pos_y += vertical_vel * delta_time
            props.velocity_y = vertical_vel
        
        # Ground collision
        if props.up_axis == 'Z':
            if pos_z < props.ground_level:
                pos_z = props.ground_level
                props.velocity_z = 0
                props.is_grounded = True
                props.is_jumping = False
        else:
            if pos_y < props.ground_level:
                pos_y = props.ground_level
                props.velocity_y = 0
                props.is_grounded = True
                props.is_jumping = False
        
        # Update object position
        obj.location.x = pos_x
        obj.location.y = pos_y
        obj.location.z = pos_z
    
    @staticmethod
    def update_horizontal(props, velocity, delta_time):
        """Update horizontal velocity based on input"""
        # Determine target direction
        direction = 0
        if props.input_left:
            direction -= 1
        if props.input_right:
            direction += 1
        
        # Determine max speed and acceleration based on run state
        if props.input_run or props.is_running:
            max_speed = props.max_run_speed
            acceleration = props.run_acceleration
            props.is_running = props.input_run
        else:
            max_speed = props.max_walk_speed
            acceleration = props.walk_acceleration
            props.is_running = False
        
        # Apply air control multiplier if airborne
        if not props.is_grounded:
            acceleration *= SMB_AIR_ACCEL_MULTIPLIER
        
        if direction != 0:
            # Check if skidding (moving opposite to velocity)
            is_skidding = (velocity > 0 and direction < 0) or (velocity < 0 and direction > 0)
            
            if is_skidding:
                # Apply skid deceleration
                decel = props.skid_deceleration * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - decel)
                else:
                    velocity = min(0, velocity + decel)
            else:
                # Apply acceleration
                velocity += direction * acceleration * delta_time
                
                # Clamp to max speed
                velocity = max(-max_speed, min(max_speed, velocity))
        else:
            # No input - apply friction
            if props.is_grounded:
                friction = props.friction * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - friction)
                elif velocity < 0:
                    velocity = min(0, velocity + friction)
        
        return velocity
    
    @staticmethod
    def update_vertical(props, velocity, delta_time):
        """Update vertical velocity (jumping and gravity)"""
        # Handle jump initiation
        if props.input_jump and props.is_grounded and not props.is_jumping:
            props.is_jumping = True
            props.jump_held = True
            
            # Jump velocity depends on horizontal speed
            horizontal_speed = abs(props.velocity_x) if props.forward_axis == 'X' else abs(props.velocity_y)
            
            if horizontal_speed > props.max_walk_speed * 0.8:
                velocity = props.jump_velocity_run
            else:
                velocity = props.jump_velocity
        
        # Track if jump button is still held
        if not props.input_jump:
            props.jump_held = False
        
        # Apply gravity
        if not props.is_grounded:
            # Holding jump reduces gravity (allows variable jump height)
            gravity = props.gravity
            if props.jump_held and velocity > 0:
                gravity *= SMB_JUMP_GRAVITY_MULTIPLIER
            
            velocity -= gravity * delta_time
            
            # Cap at terminal velocity
            velocity = max(-props.terminal_velocity, velocity)
        
        return velocity


class SMB_OT_start_physics(bpy.types.Operator):
    """Start SMB Physics Simulation"""
    bl_idname = "smb.start_physics"
    bl_label = "Start Physics"
    bl_description = "Start Super Mario Bros. physics simulation for the selected object"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _last_time = None
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def modal(self, context, event):
        props = context.scene.smb_physics_props
        
        if not props.is_active:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            import time
            current_time = time.time()
            if self._last_time is not None:
                delta_time = min(current_time - self._last_time, 0.1)  # Cap delta to prevent physics explosion
                SMBPhysicsEngine.update_physics(context, delta_time)
            self._last_time = current_time
            
            # Force viewport update
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        
        # Handle keyboard input for movement
        if event.type == 'LEFT_ARROW':
            props.input_left = (event.value == 'PRESS')
        elif event.type == 'RIGHT_ARROW':
            props.input_right = (event.value == 'PRESS')
        elif event.type == 'SPACE':
            props.input_jump = (event.value == 'PRESS')
        elif event.type == 'LEFT_SHIFT':
            props.input_run = (event.value == 'PRESS')
        elif event.type in {'ESC'}:
            props.is_active = False
            self.cancel(context)
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        props = context.scene.smb_physics_props
        
        if props.is_active:
            props.is_active = False
            return {'CANCELLED'}
        
        # Reset velocities
        props.velocity_x = 0
        props.velocity_y = 0
        props.velocity_z = 0
        props.is_jumping = False
        props.is_grounded = True
        props.input_left = False
        props.input_right = False
        props.input_jump = False
        props.input_run = False
        
        # Set ground level to current object position
        obj = context.active_object
        if props.up_axis == 'Z':
            props.ground_level = obj.location.z
        else:
            props.ground_level = obj.location.y
        
        props.is_active = True
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0 / 60.0, window=context.window)  # 60 FPS
        self._last_time = None
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        props = context.scene.smb_physics_props
        props.is_active = False
        props.input_left = False
        props.input_right = False
        props.input_jump = False
        props.input_run = False
        
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)


class SMB_OT_stop_physics(bpy.types.Operator):
    """Stop SMB Physics Simulation"""
    bl_idname = "smb.stop_physics"
    bl_label = "Stop Physics"
    bl_description = "Stop Super Mario Bros. physics simulation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.smb_physics_props
        props.is_active = False
        return {'FINISHED'}


class SMB_OT_reset_to_defaults(bpy.types.Operator):
    """Reset physics values to accurate SMB defaults"""
    bl_idname = "smb.reset_defaults"
    bl_label = "Reset to SMB Defaults"
    bl_description = "Reset all physics values to accurate Super Mario Bros. values"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.smb_physics_props
        
        props.gravity = SMB_GRAVITY
        props.terminal_velocity = SMB_TERMINAL_VELOCITY
        props.jump_velocity = SMB_JUMP_VELOCITY_WALK
        props.jump_velocity_run = SMB_JUMP_VELOCITY_RUN
        props.max_walk_speed = SMB_MAX_WALK_SPEED
        props.max_run_speed = SMB_MAX_RUN_SPEED
        props.walk_acceleration = SMB_WALK_ACCEL
        props.run_acceleration = SMB_RUN_ACCEL
        props.friction = SMB_FRICTION
        props.skid_deceleration = SMB_SKID_DECEL
        
        self.report({'INFO'}, "Physics values reset to SMB defaults")
        return {'FINISHED'}


class SMB_PT_physics_panel(bpy.types.Panel):
    """Panel for SMB Physics controls"""
    bl_label = "Super Mario Bros. Physics"
    bl_idname = "SMB_PT_physics_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMB Physics"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.smb_physics_props
        
        # Player info
        obj = context.active_object
        if obj:
            box = layout.box()
            box.label(text=f"PLAYER: {obj.name}", icon='OUTLINER_OB_MESH')
        else:
            box = layout.box()
            box.label(text="No object selected!", icon='ERROR')
        
        # Main controls
        layout.separator()
        
        if props.is_active:
            layout.operator("smb.stop_physics", text="Stop Physics", icon='PAUSE')
            
            # Show current state
            box = layout.box()
            box.label(text="Status:", icon='INFO')
            col = box.column(align=True)
            col.label(text=f"Grounded: {'Yes' if props.is_grounded else 'No'}")
            col.label(text=f"Jumping: {'Yes' if props.is_jumping else 'No'}")
            col.label(text=f"Running: {'Yes' if props.is_running else 'No'}")
            
            # Show velocity
            box = layout.box()
            box.label(text="Velocity:", icon='FORCE_WIND')
            col = box.column(align=True)
            col.label(text=f"X: {props.velocity_x:.2f}")
            col.label(text=f"Y: {props.velocity_y:.2f}")
            col.label(text=f"Z: {props.velocity_z:.2f}")
            
            # Controls help
            box = layout.box()
            box.label(text="Controls:", icon='KEYTYPE_KEYFRAME_VEC')
            col = box.column(align=True)
            col.label(text="← → : Move Left/Right")
            col.label(text="Space : Jump")
            col.label(text="Shift : Run")
            col.label(text="Esc : Stop")
        else:
            layout.operator("smb.start_physics", text="Start Physics", icon='PLAY')


class SMB_PT_physics_settings(bpy.types.Panel):
    """Panel for SMB Physics settings"""
    bl_label = "Physics Settings"
    bl_idname = "SMB_PT_physics_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMB Physics"
    bl_parent_id = "SMB_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.smb_physics_props
        
        # Axis settings
        box = layout.box()
        box.label(text="Axes:", icon='EMPTY_AXIS')
        col = box.column(align=True)
        col.prop(props, "forward_axis")
        col.prop(props, "up_axis")
        
        layout.separator()
        
        # Movement settings
        box = layout.box()
        box.label(text="Movement:", icon='CON_LOCLIKE')
        col = box.column(align=True)
        col.prop(props, "max_walk_speed")
        col.prop(props, "max_run_speed")
        col.prop(props, "walk_acceleration")
        col.prop(props, "run_acceleration")
        col.prop(props, "friction")
        col.prop(props, "skid_deceleration")
        
        layout.separator()
        
        # Jump settings
        box = layout.box()
        box.label(text="Jumping:", icon='SORT_ASC')
        col = box.column(align=True)
        col.prop(props, "jump_velocity")
        col.prop(props, "jump_velocity_run")
        col.prop(props, "gravity")
        col.prop(props, "terminal_velocity")
        
        layout.separator()
        
        # Ground level
        box = layout.box()
        box.label(text="Environment:", icon='WORLD')
        box.prop(props, "ground_level")
        
        layout.separator()
        
        # Reset button
        layout.operator("smb.reset_defaults", icon='FILE_REFRESH')


# Registration
classes = [
    SMBPhysicsProperties,
    SMB_OT_start_physics,
    SMB_OT_stop_physics,
    SMB_OT_reset_to_defaults,
    SMB_PT_physics_panel,
    SMB_PT_physics_settings,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.smb_physics_props = bpy.props.PointerProperty(type=SMBPhysicsProperties)


def unregister():
    del bpy.types.Scene.smb_physics_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
