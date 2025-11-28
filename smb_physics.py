# Super Mario Bros. Physics Addon for Blender
# Recreates accurate Super Mario Bros. physics for selected object
# The selected object will be considered as the PLAYER

import bpy
import time
import json
import os
from mathutils import Vector
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
# Walking acceleration: 0x0018 (0.09375 pixels/frame²) 
# Running acceleration: 0x0024 (0.140625 pixels/frame²)
# Note: These are per-frame acceleration values from the NES
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

# Collision detection constants
STANDING_TOLERANCE = 0.1  # Tolerance for detecting if player is standing on surface
RAYCAST_GROUND_DISTANCE = 0.2  # Max distance for raycast ground detection


# ==============================================================================
# Built-in Physics Presets
# ==============================================================================
PHYSICS_PRESETS = {
    'SMB1': {
        'name': 'Super Mario Bros. 1',
        'gravity': SMB_GRAVITY,
        'terminal_velocity': SMB_TERMINAL_VELOCITY,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN,
        'max_walk_speed': SMB_MAX_WALK_SPEED,
        'max_run_speed': SMB_MAX_RUN_SPEED,
        'walk_acceleration': SMB_WALK_ACCEL,
        'run_acceleration': SMB_RUN_ACCEL,
        'friction': SMB_FRICTION,
        'skid_deceleration': SMB_SKID_DECEL,
    },
    'SMB2': {
        'name': 'Super Mario Bros. 2 (USA)',
        # SMB2 USA has floatier physics, higher jumps, can pick up enemies
        'gravity': SMB_GRAVITY * 0.75,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.85,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.3,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.35,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 0.9,
        'max_run_speed': SMB_MAX_RUN_SPEED * 0.95,
        'walk_acceleration': SMB_WALK_ACCEL * 0.9,
        'run_acceleration': SMB_RUN_ACCEL * 0.9,
        'friction': SMB_FRICTION * 0.8,
        'skid_deceleration': SMB_SKID_DECEL * 0.7,
    },
    'SMB3': {
        'name': 'Super Mario Bros. 3',
        # SMB3 has slightly different physics - floatier jumps
        'gravity': SMB_GRAVITY * 0.85,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.9,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.1,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.15,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 1.05,
        'max_run_speed': SMB_MAX_RUN_SPEED * 1.1,
        'walk_acceleration': SMB_WALK_ACCEL * 1.1,
        'run_acceleration': SMB_RUN_ACCEL * 1.1,
        'friction': SMB_FRICTION * 0.9,
        'skid_deceleration': SMB_SKID_DECEL * 0.85,
    },
    'SMW': {
        'name': 'Super Mario World',
        # SMW has more momentum, spin jumps, cape flying
        'gravity': SMB_GRAVITY * 0.9,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.95,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.15,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.2,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 1.1,
        'max_run_speed': SMB_MAX_RUN_SPEED * 1.2,
        'walk_acceleration': SMB_WALK_ACCEL * 1.0,
        'run_acceleration': SMB_RUN_ACCEL * 1.1,
        'friction': SMB_FRICTION * 0.85,
        'skid_deceleration': SMB_SKID_DECEL * 0.9,
    },
    'NSMB': {
        'name': 'New Super Mario Bros.',
        # NSMB has more floaty physics, wall jumps, ground pound
        'gravity': SMB_GRAVITY * 0.8,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.85,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.2,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.25,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 1.05,
        'max_run_speed': SMB_MAX_RUN_SPEED * 1.15,
        'walk_acceleration': SMB_WALK_ACCEL * 1.0,
        'run_acceleration': SMB_RUN_ACCEL * 1.05,
        'friction': SMB_FRICTION * 0.75,
        'skid_deceleration': SMB_SKID_DECEL * 0.8,
    },
    'LUIGI_SMB1': {
        'name': 'Luigi (SMB1 Style)',
        # Luigi has higher jumps but less traction
        'gravity': SMB_GRAVITY * 0.85,
        'terminal_velocity': SMB_TERMINAL_VELOCITY,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.25,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.3,
        'max_walk_speed': SMB_MAX_WALK_SPEED,
        'max_run_speed': SMB_MAX_RUN_SPEED,
        'walk_acceleration': SMB_WALK_ACCEL * 0.85,
        'run_acceleration': SMB_RUN_ACCEL * 0.85,
        'friction': SMB_FRICTION * 0.5,  # Slippery!
        'skid_deceleration': SMB_SKID_DECEL * 0.6,
    },
    'LUIGI_SMB2': {
        'name': 'Luigi (SMB2 Style)',
        # SMB2 Luigi has flutter jump, highest jumps
        'gravity': SMB_GRAVITY * 0.6,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.75,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.5,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.55,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 0.85,
        'max_run_speed': SMB_MAX_RUN_SPEED * 0.9,
        'walk_acceleration': SMB_WALK_ACCEL * 0.8,
        'run_acceleration': SMB_RUN_ACCEL * 0.8,
        'friction': SMB_FRICTION * 0.4,  # Very slippery!
        'skid_deceleration': SMB_SKID_DECEL * 0.5,
    },
    'FLOATY': {
        'name': 'Floaty (Low Gravity)',
        'gravity': SMB_GRAVITY * 0.5,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 0.6,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 0.8,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 0.85,
        'max_walk_speed': SMB_MAX_WALK_SPEED,
        'max_run_speed': SMB_MAX_RUN_SPEED,
        'walk_acceleration': SMB_WALK_ACCEL * 0.8,
        'run_acceleration': SMB_RUN_ACCEL * 0.8,
        'friction': SMB_FRICTION * 0.5,
        'skid_deceleration': SMB_SKID_DECEL * 0.6,
    },
    'TIGHT': {
        'name': 'Tight Controls',
        'gravity': SMB_GRAVITY * 1.3,
        'terminal_velocity': SMB_TERMINAL_VELOCITY * 1.2,
        'jump_velocity': SMB_JUMP_VELOCITY_WALK * 1.2,
        'jump_velocity_run': SMB_JUMP_VELOCITY_RUN * 1.2,
        'max_walk_speed': SMB_MAX_WALK_SPEED * 1.2,
        'max_run_speed': SMB_MAX_RUN_SPEED * 1.2,
        'walk_acceleration': SMB_WALK_ACCEL * 1.5,
        'run_acceleration': SMB_RUN_ACCEL * 1.5,
        'friction': SMB_FRICTION * 1.5,
        'skid_deceleration': SMB_SKID_DECEL * 1.3,
    },
}


def get_presets_directory():
    """Get the directory for storing custom presets"""
    # Use Blender's config directory for user presets
    config_dir = bpy.utils.user_resource('CONFIG')
    presets_dir = os.path.join(config_dir, 'smb_physics_presets')
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)
    return presets_dir


def get_custom_presets():
    """Load all custom presets from the presets directory"""
    presets = {}
    presets_dir = get_presets_directory()
    if os.path.exists(presets_dir):
        for filename in os.listdir(presets_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(presets_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        preset = json.load(f)
                        preset_name = filename[:-5]  # Remove .json
                        presets[preset_name] = preset
                except (json.JSONDecodeError, IOError):
                    pass
    return presets


def update_player_custom_properties(obj, props):
    """Update custom properties on the player object for driver usage"""
    if obj is None:
        return
    
    # Physics state properties (can be used with drivers)
    obj['smb_velocity_x'] = props.velocity_x
    obj['smb_velocity_y'] = props.velocity_y
    obj['smb_velocity_z'] = props.velocity_z
    obj['smb_speed'] = (props.velocity_x ** 2 + props.velocity_y ** 2 + props.velocity_z ** 2) ** 0.5
    obj['smb_horizontal_speed'] = abs(props.velocity_x) if props.forward_axis == 'X' else abs(props.velocity_y)
    obj['smb_is_grounded'] = 1.0 if props.is_grounded else 0.0
    obj['smb_is_jumping'] = 1.0 if props.is_jumping else 0.0
    obj['smb_is_running'] = 1.0 if props.is_running else 0.0
    obj['smb_is_skidding'] = 1.0 if props.is_skidding else 0.0
    obj['smb_is_falling'] = 1.0 if props.is_falling else 0.0
    obj['smb_is_swimming'] = 1.0 if props.is_swimming else 0.0
    obj['smb_is_moving_left'] = 1.0 if props.input_left else 0.0
    obj['smb_is_moving_right'] = 1.0 if props.input_right else 0.0
    # Facing direction based on the configured forward axis
    horizontal_vel = props.velocity_x if props.forward_axis == 'X' else props.velocity_y
    obj['smb_facing_direction'] = 1.0 if horizontal_vel >= 0 else -1.0
    obj['smb_is_facing_left'] = 1.0 if horizontal_vel < 0 else 0.0
    obj['smb_is_facing_right'] = 1.0 if horizontal_vel >= 0 else 0.0
    obj['smb_physics_active'] = 1.0 if props.is_active else 0.0


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
    is_skidding: bpy.props.BoolProperty(name="Is Skidding", default=False)
    is_falling: bpy.props.BoolProperty(name="Is Falling", default=False)
    
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
    
    # Collision settings
    enable_collision: bpy.props.BoolProperty(
        name="Enable Collision",
        description="Enable collision detection with objects tagged as 'smb_collision'",
        default=True
    )
    
    collision_padding: bpy.props.FloatProperty(
        name="Collision Padding",
        description="Extra padding around collision boxes",
        default=0.01,
        min=0.0
    )
    
    use_raycast_collision: bpy.props.BoolProperty(
        name="Use Raycast Collision",
        description="Use raycasting for more precise collision (slower but more accurate for complex shapes)",
        default=False
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
    
    # Preset name for saving
    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name for saving the current physics settings as a preset",
        default="My Preset"
    )
    
    # Block Blender shortcuts in game mode
    block_shortcuts: bpy.props.BoolProperty(
        name="Block Shortcuts",
        description="Block Blender shortcuts while physics is active (Game Mode)",
        default=True
    )
    
    # Swimming mode
    is_swimming: bpy.props.BoolProperty(
        name="Is Swimming",
        description="Whether the player is currently in water",
        default=False
    )
    
    swim_gravity: bpy.props.FloatProperty(
        name="Swim Gravity",
        description="Gravity while swimming (units/sec²)",
        default=SMB_GRAVITY * 0.3,
        min=0.0
    )
    
    swim_speed: bpy.props.FloatProperty(
        name="Swim Speed",
        description="Maximum swimming speed (units/sec)",
        default=SMB_MAX_WALK_SPEED * 0.7,
        min=0.0
    )
    
    swim_acceleration: bpy.props.FloatProperty(
        name="Swim Acceleration",
        description="Acceleration while swimming (units/sec²)",
        default=SMB_WALK_ACCEL * 0.6,
        min=0.0
    )


# Collision type constants
COLLISION_TYPES = {
    'SOLID': 'Standard solid collision',
    'BREAKABLE': 'Can be broken by hitting from below',
    'SPRING': 'Bounces player upward',
    'ENEMY': 'Damages player on side contact, defeated by jumping on',
    'WATER': 'Enables swimming mode when entered',
    'FIRE': 'Damages player on any contact',
    'MOVING': 'Moving platform that carries player',
    'ONE_WAY': 'Can pass through from below',
}


class SMBPhysicsEngine:
    """Core physics engine implementing SMB physics with collision detection"""
    
    @staticmethod
    def get_object_bounds(obj):
        """Get AABB (Axis-Aligned Bounding Box) for an object in world space"""
        # Get the bounding box corners in local space
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        # Find min/max for each axis
        min_x = min(corner.x for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)
        
        return (min_x, max_x, min_y, max_y, min_z, max_z)
    
    @staticmethod
    def check_aabb_collision(bounds1, bounds2):
        """Check if two AABBs are colliding"""
        min_x1, max_x1, min_y1, max_y1, min_z1, max_z1 = bounds1
        min_x2, max_x2, min_y2, max_y2, min_z2, max_z2 = bounds2
        
        return (min_x1 <= max_x2 and max_x1 >= min_x2 and
                min_y1 <= max_y2 and max_y1 >= min_y2 and
                min_z1 <= max_z2 and max_z1 >= min_z2)
    
    @staticmethod
    def get_collision_objects(context, player_obj):
        """Get all objects tagged for collision with their collision type"""
        collision_objects = []
        for obj in context.scene.objects:
            if obj == player_obj:
                continue
            # Check if object is tagged for collision
            if 'smb_collision' in obj.name.lower() or obj.get('smb_collision', False):
                # Get collision type (default to SOLID)
                collision_type = obj.get('smb_collision_type', 'SOLID')
                collision_objects.append((obj, collision_type))
        return collision_objects
    
    @staticmethod
    def get_water_boxes(context, player_obj):
        """Get all objects tagged as water boxes"""
        water_boxes = []
        for obj in context.scene.objects:
            if obj == player_obj:
                continue
            if obj.get('smb_collision_type') == 'WATER' or 'smb_water' in obj.name.lower():
                water_boxes.append(obj)
        return water_boxes
    
    @staticmethod
    def check_in_water(context, player_obj, props):
        """Check if player is inside any water box"""
        water_boxes = SMBPhysicsEngine.get_water_boxes(context, player_obj)
        player_bounds = SMBPhysicsEngine.get_object_bounds(player_obj)
        
        for water_obj in water_boxes:
            water_bounds = SMBPhysicsEngine.get_object_bounds(water_obj)
            if SMBPhysicsEngine.check_aabb_collision(player_bounds, water_bounds):
                return True
        return False
    
    @staticmethod
    def check_standing_on(player_bounds, obstacle_bounds, up_axis):
        """Check if player is standing on top of an obstacle (for grounded detection)"""
        p_min_x, p_max_x, p_min_y, p_max_y, p_min_z, p_max_z = player_bounds
        o_min_x, o_max_x, o_min_y, o_max_y, o_min_z, o_max_z = obstacle_bounds
        
        # Check horizontal overlap (must be overlapping in X and Y for standing)
        if not (p_min_x <= o_max_x and p_max_x >= o_min_x):
            return False
        if not (p_min_y <= o_max_y and p_max_y >= o_min_y):
            return False
        
        # Check if player bottom is near obstacle top
        if up_axis == 'Z':
            # Player's bottom should be at or near obstacle's top
            return abs(p_min_z - o_max_z) < STANDING_TOLERANCE
        else:  # Y is up
            return abs(p_min_y - o_max_y) < STANDING_TOLERANCE
    
    @staticmethod
    def raycast_ground_check(context, obj, up_axis, max_distance=RAYCAST_GROUND_DISTANCE):
        """
        Use raycasting to check if player is standing on ground.
        More accurate for complex mesh shapes.
        Returns: (is_grounded, ground_object, hit_location)
        """
        from mathutils import Vector
        
        # Cast ray downward from player center
        origin = obj.location.copy()
        
        # Ray direction is down along the up axis
        if up_axis == 'Z':
            direction = Vector((0, 0, -1))
        else:
            direction = Vector((0, -1, 0))
        
        # Use scene raycast
        depsgraph = context.evaluated_depsgraph_get()
        result, location, normal, index, hit_obj, matrix = context.scene.ray_cast(
            depsgraph, origin, direction, distance=max_distance
        )
        
        if result and hit_obj:
            # Check if hit object is a collision object (property check is authoritative)
            if hit_obj.get('smb_collision', False):
                return True, hit_obj, location
        
        return False, None, None
    
    @staticmethod
    def get_collision_friction(obstacle):
        """Get friction multiplier from collision object"""
        # Default friction is 1.0 (normal friction)
        return obstacle.get('smb_friction', 1.0)
    
    @staticmethod
    def resolve_collision(player_bounds, obstacle_bounds, velocity, forward_axis, up_axis, collision_type='SOLID'):
        """
        Resolve collision between player and obstacle.
        Returns: (new_pos_offset, new_velocity, is_grounded_on_top, special_action)
        
        SMB-style collision resolution:
        - Landing on top of objects (like platforms/blocks)
        - Hitting head on bottom of objects
        - Horizontal wall collision
        
        Special collision types:
        - SPRING: Bounces player upward
        - ONE_WAY: Only collide from above
        - ENEMY: Can stomp from above
        """
        p_min_x, p_max_x, p_min_y, p_max_y, p_min_z, p_max_z = player_bounds
        o_min_x, o_max_x, o_min_y, o_max_y, o_min_z, o_max_z = obstacle_bounds
        
        vel_x, vel_y, vel_z = velocity
        offset_x, offset_y, offset_z = 0.0, 0.0, 0.0
        is_grounded = False
        special_action = None  # Can be 'bounce', 'stomp', 'damage', 'break'
        
        # Calculate overlap on each axis
        overlap_x = min(p_max_x - o_min_x, o_max_x - p_min_x)
        overlap_y = min(p_max_y - o_min_y, o_max_y - p_min_y)
        overlap_z = min(p_max_z - o_min_z, o_max_z - p_min_z)
        
        # For Z axis (vertical in default config)
        if up_axis == 'Z':
            player_center_z = (p_min_z + p_max_z) / 2
            obstacle_center_z = (o_min_z + o_max_z) / 2
            is_above = player_center_z > obstacle_center_z
            is_below = player_center_z < obstacle_center_z
            
            # Handle ONE_WAY platforms - only collide from above
            if collision_type == 'ONE_WAY':
                if not is_above or vel_z > 0:
                    return (0, 0, 0), velocity, False, None
            
            if overlap_z <= overlap_x and overlap_z <= overlap_y:
                if is_above:
                    # Player is above - land on top
                    offset_z = o_max_z - p_min_z
                    
                    if collision_type == 'SPRING':
                        # Bounce upward
                        vel_z = abs(vel_z) * 2.0 if abs(vel_z) > 1.0 else 15.0
                        special_action = 'bounce'
                    elif collision_type == 'ENEMY':
                        vel_z = 8.0  # Stomp bounce
                        special_action = 'stomp'
                    else:
                        if vel_z < 0:
                            vel_z = 0
                        is_grounded = True
                else:
                    # Player is below - hit head
                    offset_z = o_min_z - p_max_z
                    if vel_z > 0:
                        vel_z = 0
                    
                    if collision_type == 'BREAKABLE':
                        special_action = 'break'
                    elif collision_type == 'ENEMY':
                        special_action = 'damage'
            else:
                # Horizontal collision
                if collision_type == 'ENEMY' or collision_type == 'FIRE':
                    special_action = 'damage'
                
                if forward_axis == 'X':
                    player_center_x = (p_min_x + p_max_x) / 2
                    obstacle_center_x = (o_min_x + o_max_x) / 2
                    if player_center_x > obstacle_center_x:
                        offset_x = o_max_x - p_min_x
                    else:
                        offset_x = o_min_x - p_max_x
                    vel_x = 0
                else:
                    player_center_y = (p_min_y + p_max_y) / 2
                    obstacle_center_y = (o_min_y + o_max_y) / 2
                    if player_center_y > obstacle_center_y:
                        offset_y = o_max_y - p_min_y
                    else:
                        offset_y = o_min_y - p_max_y
                    vel_y = 0
        else:
            # Y is up axis
            player_center_y = (p_min_y + p_max_y) / 2
            obstacle_center_y = (o_min_y + o_max_y) / 2
            is_above = player_center_y > obstacle_center_y
            
            # Handle ONE_WAY platforms
            if collision_type == 'ONE_WAY':
                if not is_above or vel_y > 0:
                    return (0, 0, 0), velocity, False, None
            
            if overlap_y <= overlap_x and overlap_y <= overlap_z:
                if is_above:
                    offset_y = o_max_y - p_min_y
                    
                    if collision_type == 'SPRING':
                        vel_y = abs(vel_y) * 2.0 if abs(vel_y) > 1.0 else 15.0
                        special_action = 'bounce'
                    elif collision_type == 'ENEMY':
                        vel_y = 8.0
                        special_action = 'stomp'
                    else:
                        if vel_y < 0:
                            vel_y = 0
                        is_grounded = True
                else:
                    offset_y = o_min_y - p_max_y
                    if vel_y > 0:
                        vel_y = 0
                    
                    if collision_type == 'BREAKABLE':
                        special_action = 'break'
                    elif collision_type == 'ENEMY':
                        special_action = 'damage'
            else:
                # Horizontal resolution
                if collision_type == 'ENEMY' or collision_type == 'FIRE':
                    special_action = 'damage'
                    
                player_center_x = (p_min_x + p_max_x) / 2
                obstacle_center_x = (o_min_x + o_max_x) / 2
                if player_center_x > obstacle_center_x:
                    offset_x = o_max_x - p_min_x
                else:
                    offset_x = o_min_x - p_max_x
                vel_x = 0
        
        return (offset_x, offset_y, offset_z), (vel_x, vel_y, vel_z), is_grounded, special_action
    
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
        # Prevent axis conflict: if forward_axis is Y, force up_axis to Z
        effective_up_axis = props.up_axis
        if props.forward_axis == 'Y' and props.up_axis == 'Y':
            effective_up_axis = 'Z'
        
        if props.forward_axis == 'X':
            horizontal_vel = props.velocity_x
        else:
            horizontal_vel = props.velocity_y
            
        if effective_up_axis == 'Z':
            vertical_vel = props.velocity_z
        else:
            vertical_vel = props.velocity_y
        
        # Store last frame's grounded state for this frame's physics
        # Will be updated by collision detection
        was_grounded_last_frame = props.is_grounded
        ground_friction_mult = 1.0  # Default friction multiplier
        
        # Check if grounded (initial check - will be updated by collision)
        if effective_up_axis == 'Z':
            props.is_grounded = pos_z <= props.ground_level + 0.01
        else:
            props.is_grounded = pos_y <= props.ground_level + 0.01
        
        # Pre-check collision for grounded state BEFORE applying horizontal physics
        # This fixes the friction bug when standing on collision objects
        if props.enable_collision:
            if props.use_raycast_collision:
                # Use raycast for more precise ground detection
                is_on_ground, ground_obj, hit_loc = SMBPhysicsEngine.raycast_ground_check(
                    context, obj, effective_up_axis
                )
                if is_on_ground:
                    props.is_grounded = True
                    ground_friction_mult = SMBPhysicsEngine.get_collision_friction(ground_obj)
            else:
                # Use AABB for ground detection
                collision_objects = SMBPhysicsEngine.get_collision_objects(context, obj)
                for obstacle, collision_type in collision_objects:
                    if collision_type == 'WATER':
                        continue
                    player_bounds = SMBPhysicsEngine.get_object_bounds(obj)
                    obstacle_bounds = SMBPhysicsEngine.get_object_bounds(obstacle)
                    
                    # Check if player is standing on this object
                    if SMBPhysicsEngine.check_standing_on(player_bounds, obstacle_bounds, effective_up_axis):
                        props.is_grounded = True
                        ground_friction_mult = SMBPhysicsEngine.get_collision_friction(obstacle)
                        break
        
        # Check if in water
        was_swimming = props.is_swimming
        props.is_swimming = SMBPhysicsEngine.check_in_water(context, obj, props)
        
        # Horizontal movement (now with correct grounded state for friction)
        horizontal_vel = SMBPhysicsEngine.update_horizontal(
            props, horizontal_vel, delta_time, ground_friction_mult
        )
        
        # Vertical movement (jumping/gravity/swimming)
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
            
        if effective_up_axis == 'Z':
            pos_z += vertical_vel * delta_time
            props.velocity_z = vertical_vel
        else:
            pos_y += vertical_vel * delta_time
            props.velocity_y = vertical_vel
        
        # Update position before collision detection
        obj.location.x = pos_x
        obj.location.y = pos_y
        obj.location.z = pos_z
        
        # Object collision detection
        if props.enable_collision:
            collision_objects = SMBPhysicsEngine.get_collision_objects(context, obj)
            padding = props.collision_padding
            
            for obstacle, collision_type in collision_objects:
                # Skip WATER type in normal collision (handled separately)
                if collision_type == 'WATER':
                    continue
                    
                # Recalculate player bounds each iteration (position may change from previous collision)
                player_bounds = SMBPhysicsEngine.get_object_bounds(obj)
                obstacle_bounds = SMBPhysicsEngine.get_object_bounds(obstacle)
                
                # Apply padding to shrink the effective player collision box slightly
                player_bounds = (
                    player_bounds[0] + padding, player_bounds[1] - padding,
                    player_bounds[2] + padding, player_bounds[3] - padding,
                    player_bounds[4] + padding, player_bounds[5] - padding
                )
                
                if SMBPhysicsEngine.check_aabb_collision(player_bounds, obstacle_bounds):
                    # Get current velocity
                    vel = (props.velocity_x, props.velocity_y, props.velocity_z)
                    
                    # Resolve collision with type
                    offset, new_vel, is_grounded, special_action = SMBPhysicsEngine.resolve_collision(
                        player_bounds, obstacle_bounds, vel,
                        props.forward_axis, effective_up_axis, collision_type
                    )
                    
                    # Handle special actions
                    if special_action == 'break':
                        # Hide or mark the object as broken
                        obstacle['smb_broken'] = True
                        obstacle.hide_viewport = True
                        obstacle.hide_render = True
                    elif special_action == 'stomp':
                        # Mark enemy as defeated
                        obstacle['smb_defeated'] = True
                        obstacle.hide_viewport = True
                        obstacle.hide_render = True
                    
                    # Apply offset
                    obj.location.x += offset[0]
                    obj.location.y += offset[1]
                    obj.location.z += offset[2]
                    
                    # Update velocity
                    props.velocity_x = new_vel[0]
                    props.velocity_y = new_vel[1]
                    props.velocity_z = new_vel[2]
                    
                    # Update grounded state if landed on top
                    if is_grounded:
                        props.is_grounded = True
                        props.is_jumping = False
        
        # Ground plane collision (fallback)
        if effective_up_axis == 'Z':
            if obj.location.z < props.ground_level:
                obj.location.z = props.ground_level
                props.velocity_z = 0
                props.is_grounded = True
                props.is_jumping = False
        else:
            if obj.location.y < props.ground_level:
                obj.location.y = props.ground_level
                props.velocity_y = 0
                props.is_grounded = True
                props.is_jumping = False
        
        # Update custom properties on player object for driver usage
        update_player_custom_properties(obj, props)
    
    @staticmethod
    def update_horizontal(props, velocity, delta_time, friction_multiplier=1.0):
        """Update horizontal velocity based on input"""
        # Determine target direction
        direction = 0
        if props.input_left:
            direction -= 1
        if props.input_right:
            direction += 1
        
        # Swimming mode uses different physics
        if props.is_swimming:
            max_speed = props.swim_speed
            acceleration = props.swim_acceleration
            friction = props.swim_acceleration * 0.5  # Less friction in water
            
            if direction != 0:
                velocity += direction * acceleration * delta_time
                velocity = max(-max_speed, min(max_speed, velocity))
            else:
                # Apply water resistance
                if velocity > 0:
                    velocity = max(0, velocity - friction * delta_time)
                elif velocity < 0:
                    velocity = min(0, velocity + friction * delta_time)
            
            return velocity
        
        # Normal movement
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
            props.is_skidding = is_skidding and props.is_grounded  # Only skid when grounded
            
            if is_skidding:
                # Apply skid deceleration
                decel = props.skid_deceleration * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - decel)
                else:
                    velocity = min(0, velocity + decel)
            else:
                # Not skidding - clear the flag
                props.is_skidding = False
                # Apply acceleration
                velocity += direction * acceleration * delta_time
                
                # Clamp to max speed
                velocity = max(-max_speed, min(max_speed, velocity))
        else:
            # No input - not skidding
            props.is_skidding = False
            # Apply friction (with surface friction multiplier)
            if props.is_grounded:
                friction = props.friction * friction_multiplier * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - friction)
                elif velocity < 0:
                    velocity = min(0, velocity + friction)
        
        return velocity
    
    @staticmethod
    def update_vertical(props, velocity, delta_time):
        """Update vertical velocity (jumping, gravity, and swimming)"""
        
        # Swimming mode
        if props.is_swimming:
            # In water, pressing jump swims upward
            if props.input_jump:
                velocity = props.swim_speed * 0.8  # Swim upward
            else:
                # Slowly sink in water
                velocity -= props.swim_gravity * delta_time
                velocity = max(-props.swim_speed * 0.5, velocity)  # Cap sinking speed
            return velocity
        
        # Normal jump/gravity
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
            
            # Update is_falling (falling = not grounded and moving downward)
            props.is_falling = velocity < 0
        else:
            props.is_falling = False
        
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
            current_time = time.time()
            if self._last_time is not None:
                delta_time = min(current_time - self._last_time, 0.1)  # Cap delta to prevent physics explosion
                SMBPhysicsEngine.update_physics(context, delta_time)
            self._last_time = current_time
            
            # Force viewport update
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        
        # Handle keyboard input for movement (PRESS sets True, RELEASE sets False)
        handled = False
        if event.type == 'LEFT_ARROW':
            if event.value == 'PRESS':
                props.input_left = True
            elif event.value == 'RELEASE':
                props.input_left = False
            handled = True
        elif event.type == 'RIGHT_ARROW':
            if event.value == 'PRESS':
                props.input_right = True
            elif event.value == 'RELEASE':
                props.input_right = False
            handled = True
        elif event.type == 'SPACE':
            if event.value == 'PRESS':
                props.input_jump = True
            elif event.value == 'RELEASE':
                props.input_jump = False
            handled = True
        elif event.type == 'LEFT_SHIFT':
            if event.value == 'PRESS':
                props.input_run = True
            elif event.value == 'RELEASE':
                props.input_run = False
            handled = True
        elif event.type in {'ESC'}:
            props.is_active = False
            self.cancel(context)
            return {'CANCELLED'}
        
        # Block Blender shortcuts in game mode if enabled
        if props.block_shortcuts:
            # Allow mouse events and timer events to pass through
            if event.type in {'TIMER', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 
                              'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE',
                              'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                              'WINDOW_DEACTIVATE', 'NONE'}:
                return {'PASS_THROUGH'}
            # Block all keyboard events except our game controls
            if event.type not in {'LEFT_ARROW', 'RIGHT_ARROW', 'SPACE', 'LEFT_SHIFT', 'ESC'}:
                return {'RUNNING_MODAL'}
            # If we handled a game control, consume it
            if handled:
                return {'RUNNING_MODAL'}
        
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
        
        # Initialize custom properties on player object
        update_player_custom_properties(obj, props)
        
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
        
        # Update custom properties to reflect inactive state
        obj = context.active_object
        if obj:
            update_player_custom_properties(obj, props)
        
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


class SMB_OT_load_preset(bpy.types.Operator):
    """Load a physics preset"""
    bl_idname = "smb.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load a physics preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_key: bpy.props.StringProperty(
        name="Preset Key",
        description="Key of the preset to load"
    )
    
    def execute(self, context):
        props = context.scene.smb_physics_props
        
        # Check built-in presets first
        if self.preset_key in PHYSICS_PRESETS:
            preset = PHYSICS_PRESETS[self.preset_key]
        else:
            # Check custom presets
            custom_presets = get_custom_presets()
            if self.preset_key in custom_presets:
                preset = custom_presets[self.preset_key]
            else:
                self.report({'ERROR'}, f"Preset '{self.preset_key}' not found")
                return {'CANCELLED'}
        
        # Apply preset values
        props.gravity = preset.get('gravity', SMB_GRAVITY)
        props.terminal_velocity = preset.get('terminal_velocity', SMB_TERMINAL_VELOCITY)
        props.jump_velocity = preset.get('jump_velocity', SMB_JUMP_VELOCITY_WALK)
        props.jump_velocity_run = preset.get('jump_velocity_run', SMB_JUMP_VELOCITY_RUN)
        props.max_walk_speed = preset.get('max_walk_speed', SMB_MAX_WALK_SPEED)
        props.max_run_speed = preset.get('max_run_speed', SMB_MAX_RUN_SPEED)
        props.walk_acceleration = preset.get('walk_acceleration', SMB_WALK_ACCEL)
        props.run_acceleration = preset.get('run_acceleration', SMB_RUN_ACCEL)
        props.friction = preset.get('friction', SMB_FRICTION)
        props.skid_deceleration = preset.get('skid_deceleration', SMB_SKID_DECEL)
        
        preset_name = preset.get('name', self.preset_key)
        self.report({'INFO'}, f"Loaded preset: {preset_name}")
        return {'FINISHED'}


class SMB_OT_save_preset(bpy.types.Operator):
    """Save current physics settings as a preset"""
    bl_idname = "smb.save_preset"
    bl_label = "Save Preset"
    bl_description = "Save current physics settings as a custom preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.smb_physics_props
        
        preset_name = props.preset_name.strip()
        if not preset_name:
            self.report({'ERROR'}, "Please enter a preset name")
            return {'CANCELLED'}
        
        # Create preset data
        preset = {
            'name': preset_name,
            'gravity': props.gravity,
            'terminal_velocity': props.terminal_velocity,
            'jump_velocity': props.jump_velocity,
            'jump_velocity_run': props.jump_velocity_run,
            'max_walk_speed': props.max_walk_speed,
            'max_run_speed': props.max_run_speed,
            'walk_acceleration': props.walk_acceleration,
            'run_acceleration': props.run_acceleration,
            'friction': props.friction,
            'skid_deceleration': props.skid_deceleration,
        }
        
        # Save to file
        presets_dir = get_presets_directory()
        # Sanitize filename
        safe_name = "".join(c for c in preset_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filepath = os.path.join(presets_dir, f"{safe_name}.json")
        
        try:
            with open(filepath, 'w') as f:
                json.dump(preset, f, indent=2)
            self.report({'INFO'}, f"Saved preset: {preset_name}")
            return {'FINISHED'}
        except IOError as e:
            self.report({'ERROR'}, f"Failed to save preset: {e}")
            return {'CANCELLED'}


class SMB_OT_delete_preset(bpy.types.Operator):
    """Delete a custom preset"""
    bl_idname = "smb.delete_preset"
    bl_label = "Delete Preset"
    bl_description = "Delete a custom preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_key: bpy.props.StringProperty(
        name="Preset Key",
        description="Key of the preset to delete"
    )
    
    def execute(self, context):
        presets_dir = get_presets_directory()
        filepath = os.path.join(presets_dir, f"{self.preset_key}.json")
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.report({'INFO'}, f"Deleted preset: {self.preset_key}")
                return {'FINISHED'}
            except IOError as e:
                self.report({'ERROR'}, f"Failed to delete preset: {e}")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, f"Preset file not found: {self.preset_key}")
            return {'CANCELLED'}


class SMB_OT_tag_collision(bpy.types.Operator):
    """Tag selected objects as collision objects"""
    bl_idname = "smb.tag_collision"
    bl_label = "Tag as Collision"
    bl_description = "Tag selected objects as collision objects for SMB physics (SOLID type)"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            obj['smb_collision'] = True
            obj['smb_collision_type'] = 'SOLID'
            count += 1
        self.report({'INFO'}, f"Tagged {count} object(s) for SOLID collision")
        return {'FINISHED'}


class SMB_OT_untag_collision(bpy.types.Operator):
    """Remove collision tag from selected objects"""
    bl_idname = "smb.untag_collision"
    bl_label = "Remove Collision Tag"
    bl_description = "Remove collision tag from selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            removed = False
            if 'smb_collision' in obj:
                del obj['smb_collision']
                removed = True
            if 'smb_collision_type' in obj:
                del obj['smb_collision_type']
                removed = True
            if removed:
                count += 1
        self.report({'INFO'}, f"Removed collision tag from {count} object(s)")
        return {'FINISHED'}


class SMB_OT_set_collision_type(bpy.types.Operator):
    """Set collision type for selected objects"""
    bl_idname = "smb.set_collision_type"
    bl_label = "Set Collision Type"
    bl_description = "Set the collision type for selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    collision_type: bpy.props.EnumProperty(
        name="Collision Type",
        description="Type of collision behavior",
        items=[
            ('SOLID', "Solid", "Standard solid collision"),
            ('BREAKABLE', "Breakable", "Can be broken by hitting from below"),
            ('SPRING', "Spring", "Bounces player upward"),
            ('ENEMY', "Enemy", "Damages player on side contact, defeated by jumping on"),
            ('WATER', "Water", "Enables swimming mode when entered"),
            ('FIRE', "Fire", "Damages player on any contact"),
            ('MOVING', "Moving Platform", "Moving platform that carries player"),
            ('ONE_WAY', "One-Way", "Can pass through from below"),
        ],
        default='SOLID'
    )
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            obj['smb_collision'] = True
            obj['smb_collision_type'] = self.collision_type
            count += 1
        self.report({'INFO'}, f"Set {count} object(s) to {self.collision_type} collision")
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
            col.label(text=f"Skidding: {'Yes' if props.is_skidding else 'No'}")
            col.label(text=f"Falling: {'Yes' if props.is_falling else 'No'}")
            col.label(text=f"Swimming: {'Yes' if props.is_swimming else 'No'}")
            
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
            col.label(text="Space : Jump (or Swim Up)")
            col.label(text="Shift : Run")
            col.label(text="Esc : Stop")
            
            # Game mode indicator
            if props.block_shortcuts:
                box = layout.box()
                box.label(text="🎮 GAME MODE ACTIVE", icon='PLAY')
                box.label(text="Blender shortcuts blocked")
        else:
            layout.operator("smb.start_physics", text="Start Physics", icon='PLAY')
            
            # Game mode option
            layout.prop(props, "block_shortcuts")


class SMB_PT_presets_panel(bpy.types.Panel):
    """Panel for SMB Physics presets"""
    bl_label = "Presets"
    bl_idname = "SMB_PT_presets_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMB Physics"
    bl_parent_id = "SMB_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.smb_physics_props
        
        # Built-in presets
        box = layout.box()
        box.label(text="Built-in Presets:", icon='PRESET')
        col = box.column(align=True)
        for key, preset in PHYSICS_PRESETS.items():
            op = col.operator("smb.load_preset", text=preset['name'], icon='PLAY')
            op.preset_key = key
        
        layout.separator()
        
        # Custom presets
        box = layout.box()
        box.label(text="Custom Presets:", icon='USER')
        
        custom_presets = get_custom_presets()
        if custom_presets:
            for key, preset in custom_presets.items():
                row = box.row(align=True)
                op = row.operator("smb.load_preset", text=preset.get('name', key), icon='PLAY')
                op.preset_key = key
                op = row.operator("smb.delete_preset", text="", icon='X')
                op.preset_key = key
        else:
            box.label(text="No custom presets", icon='INFO')
        
        layout.separator()
        
        # Save preset
        box = layout.box()
        box.label(text="Save Current Settings:", icon='FILE_NEW')
        box.prop(props, "preset_name", text="Name")
        box.operator("smb.save_preset", icon='FILE_TICK')


class SMB_PT_driver_props_panel(bpy.types.Panel):
    """Panel showing driver-compatible properties"""
    bl_label = "Driver Properties"
    bl_idname = "SMB_PT_driver_props_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMB Physics"
    bl_parent_id = "SMB_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if not obj:
            layout.label(text="No object selected", icon='ERROR')
            return
        
        box = layout.box()
        box.label(text="Player Custom Properties:", icon='DRIVER')
        box.label(text="(For use with drivers)", icon='INFO')
        
        col = box.column(align=True)
        
        # List available properties
        driver_props = [
            ('smb_velocity_x', 'Velocity X'),
            ('smb_velocity_y', 'Velocity Y'),
            ('smb_velocity_z', 'Velocity Z'),
            ('smb_speed', 'Total Speed'),
            ('smb_horizontal_speed', 'Horizontal Speed'),
            ('smb_is_grounded', 'Is Grounded (0/1)'),
            ('smb_is_jumping', 'Is Jumping (0/1)'),
            ('smb_is_running', 'Is Running (0/1)'),
            ('smb_is_skidding', 'Is Skidding (0/1)'),
            ('smb_is_falling', 'Is Falling (0/1)'),
            ('smb_is_swimming', 'Is Swimming (0/1)'),
            ('smb_is_moving_left', 'Moving Left (0/1)'),
            ('smb_is_moving_right', 'Moving Right (0/1)'),
            ('smb_is_facing_left', 'Facing Left (0/1)'),
            ('smb_is_facing_right', 'Facing Right (0/1)'),
            ('smb_facing_direction', 'Facing Direction (-1/1)'),
            ('smb_physics_active', 'Physics Active (0/1)'),
        ]
        
        for prop_name, prop_label in driver_props:
            row = col.row()
            value = obj.get(prop_name, 'N/A')
            if isinstance(value, float):
                row.label(text=f"{prop_label}: {value:.2f}")
            else:
                row.label(text=f"{prop_label}: {value}")
        
        layout.separator()
        box = layout.box()
        box.label(text="Driver Path Example:", icon='QUESTION')
        box.label(text='bpy.data.objects["' + obj.name + '"]["smb_velocity_x"]')


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


class SMB_PT_collision_panel(bpy.types.Panel):
    """Panel for SMB Collision settings"""
    bl_label = "Collision"
    bl_idname = "SMB_PT_collision_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SMB Physics"
    bl_parent_id = "SMB_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.smb_physics_props
        
        # Collision toggle
        layout.prop(props, "enable_collision")
        
        if props.enable_collision:
            layout.prop(props, "collision_padding")
            layout.prop(props, "use_raycast_collision")
            
            layout.separator()
            
            # Tag/Untag buttons
            box = layout.box()
            box.label(text="Collision Objects:", icon='MOD_PHYSICS')
            col = box.column(align=True)
            col.operator("smb.tag_collision", text="Tag as Solid", icon='ADD')
            col.operator("smb.untag_collision", icon='REMOVE')
            
            layout.separator()
            
            # Collision type buttons
            box = layout.box()
            box.label(text="Set Collision Type:", icon='PHYSICS')
            col = box.column(align=True)
            
            # Row 1
            row = col.row(align=True)
            op = row.operator("smb.set_collision_type", text="Solid")
            op.collision_type = 'SOLID'
            op = row.operator("smb.set_collision_type", text="One-Way")
            op.collision_type = 'ONE_WAY'
            
            # Row 2
            row = col.row(align=True)
            op = row.operator("smb.set_collision_type", text="Breakable")
            op.collision_type = 'BREAKABLE'
            op = row.operator("smb.set_collision_type", text="Spring")
            op.collision_type = 'SPRING'
            
            # Row 3
            row = col.row(align=True)
            op = row.operator("smb.set_collision_type", text="Enemy")
            op.collision_type = 'ENEMY'
            op = row.operator("smb.set_collision_type", text="Fire")
            op.collision_type = 'FIRE'
            
            # Row 4
            row = col.row(align=True)
            op = row.operator("smb.set_collision_type", text="Water")
            op.collision_type = 'WATER'
            op = row.operator("smb.set_collision_type", text="Moving")
            op.collision_type = 'MOVING'
            
            # Surface friction info
            layout.separator()
            box = layout.box()
            box.label(text="Surface Friction:", icon='FORCE_DRAG')
            box.label(text="Set 'smb_friction' property on objects")
            box.label(text="Default: 1.0 (normal), 0.5 (icy), 2.0 (sticky)")
            
            # List collision objects in scene
            layout.separator()
            box = layout.box()
            box.label(text="Tagged Objects:", icon='OUTLINER_OB_MESH')
            
            collision_count = 0
            for obj in context.scene.objects:
                if obj.get('smb_collision', False) or 'smb_collision' in obj.name.lower():
                    collision_count += 1
                    row = box.row()
                    col_type = obj.get('smb_collision_type', 'SOLID')
                    friction = obj.get('smb_friction', 1.0)
                    row.label(text=f"{obj.name} [{col_type}] F:{friction:.1f}", icon='CUBE')
            
            if collision_count == 0:
                box.label(text="No collision objects", icon='INFO')
            
            # Swimming settings
            layout.separator()
            box = layout.box()
            box.label(text="Swimming Settings:", icon='MOD_FLUID')
            col = box.column(align=True)
            col.prop(props, "swim_gravity")
            col.prop(props, "swim_speed")
            col.prop(props, "swim_acceleration")


# Registration
classes = [
    SMBPhysicsProperties,
    SMB_OT_start_physics,
    SMB_OT_stop_physics,
    SMB_OT_reset_to_defaults,
    SMB_OT_load_preset,
    SMB_OT_save_preset,
    SMB_OT_delete_preset,
    SMB_OT_tag_collision,
    SMB_OT_untag_collision,
    SMB_OT_set_collision_type,
    SMB_PT_physics_panel,
    SMB_PT_presets_panel,
    SMB_PT_driver_props_panel,
    SMB_PT_physics_settings,
    SMB_PT_collision_panel,
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
