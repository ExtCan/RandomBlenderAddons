# Sonic The Hedgehog Physics Addon for Blender
# Recreates accurate Sonic physics for selected object
# The selected object will be considered as the PLAYER

import bpy
import time
import json
import os
from mathutils import Vector
from bpy.app.handlers import persistent

bl_info = {
    "name": "Sonic The Hedgehog Physics",
    "author": "Pink",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Sonic Physics",
    "description": "Recreates accurate Sonic The Hedgehog physics for the selected object (PLAYER)",
    "category": "Physics",
}

# ==============================================================================
# Sonic The Hedgehog Physics Constants
# All values are derived from the original Sega Genesis Sonic games
# Original game runs at 60fps with specific subpixel physics
# 
# Reference: Sonic Physics Guide (SPG)
# https://info.sonicretro.org/Sonic_Physics_Guide
# ==============================================================================

# Scale factor to convert Genesis pixel units to Blender units
PIXEL_TO_BLENDER = 0.0625  # 1 pixel = 0.0625 Blender units (1/16)

# Gravity - Sonic uses 0x00038 per frame (0.21875 pixels/frame²)
SONIC_GRAVITY = 0.21875 * PIXEL_TO_BLENDER * 60 * 60

# Air drag threshold - Sonic experiences air drag when Y velocity < -4 and X speed >= 0.125
SONIC_AIR_DRAG_THRESHOLD = 4.0 * PIXEL_TO_BLENDER * 60

# Jump force - Initial jump velocity is 6.5 pixels/frame
SONIC_JUMP_VELOCITY = 6.5 * PIXEL_TO_BLENDER * 60

# Horizontal movement speeds (in pixels/frame)
# Top speed: 6 pixels/frame (normal), 12 pixels/frame (Speed Shoes/Super)
SONIC_TOP_SPEED = 6.0 * PIXEL_TO_BLENDER * 60
SONIC_TOP_SPEED_SUPER = 10.0 * PIXEL_TO_BLENDER * 60

# Acceleration: 0.046875 pixels/frame²
SONIC_ACCELERATION = 0.046875 * PIXEL_TO_BLENDER * 60 * 60

# Deceleration: 0.5 pixels/frame² (when pressing opposite direction)
SONIC_DECELERATION = 0.5 * PIXEL_TO_BLENDER * 60 * 60

# Friction: 0.046875 pixels/frame² (same as acceleration)
SONIC_FRICTION = 0.046875 * PIXEL_TO_BLENDER * 60 * 60

# Air acceleration: 0.09375 pixels/frame² (2x ground acceleration)
SONIC_AIR_ACCELERATION = 0.09375 * PIXEL_TO_BLENDER * 60 * 60

# Rolling friction: 0.0234375 pixels/frame² (half of normal friction)
SONIC_ROLL_FRICTION = 0.0234375 * PIXEL_TO_BLENDER * 60 * 60

# Rolling deceleration: 0.125 pixels/frame²
SONIC_ROLL_DECEL = 0.125 * PIXEL_TO_BLENDER * 60 * 60

# Slope factor (affects speed on slopes)
# Normal: 0.125 pixels/frame² when walking/running
# Rolling uphill: 0.078125, Rolling downhill: 0.3125
SONIC_SLOPE_FACTOR = 0.125 * PIXEL_TO_BLENDER * 60 * 60
SONIC_SLOPE_ROLL_UP = 0.078125 * PIXEL_TO_BLENDER * 60 * 60
SONIC_SLOPE_ROLL_DOWN = 0.3125 * PIXEL_TO_BLENDER * 60 * 60

# Spin dash power levels (8 levels, from 8 to 12 pixels/frame)
SONIC_SPINDASH_MIN = 8.0 * PIXEL_TO_BLENDER * 60
SONIC_SPINDASH_MAX = 12.0 * PIXEL_TO_BLENDER * 60

# Terminal velocity (max falling speed) - typically around 16 pixels/frame
SONIC_TERMINAL_VELOCITY = 16.0 * PIXEL_TO_BLENDER * 60

# Variable jump - releasing jump button caps upward velocity at 4 pixels/frame
SONIC_JUMP_RELEASE_SPEED = 4.0 * PIXEL_TO_BLENDER * 60

# Collision detection constants
STANDING_TOLERANCE = 0.15
RAYCAST_GROUND_DISTANCE = 0.3
RAYCAST_GROUNDED_SNAP = 0.05


# ==============================================================================
# Built-in Physics Presets
# ==============================================================================
PHYSICS_PRESETS = {
    'SONIC1': {
        'name': 'Sonic 1',
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY,
        'top_speed': SONIC_TOP_SPEED,
        'acceleration': SONIC_ACCELERATION,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'SONIC2': {
        'name': 'Sonic 2',
        # Sonic 2 has spin dash and slightly different physics
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY,
        'top_speed': SONIC_TOP_SPEED * 1.1,
        'acceleration': SONIC_ACCELERATION * 1.1,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'SONIC3': {
        'name': 'Sonic 3 & Knuckles',
        # S3K has instashield and slightly tighter controls
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 1.05,
        'top_speed': SONIC_TOP_SPEED,
        'acceleration': SONIC_ACCELERATION * 1.1,
        'deceleration': SONIC_DECELERATION * 1.1,
        'friction': SONIC_FRICTION * 1.1,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'SONIC_CD': {
        'name': 'Sonic CD',
        # CD has figure-8 peel-out, slightly floatier
        'gravity': SONIC_GRAVITY * 0.95,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 1.1,
        'top_speed': SONIC_TOP_SPEED * 1.05,
        'acceleration': SONIC_ACCELERATION,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION * 0.9,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'TAILS': {
        'name': 'Tails',
        # Tails can fly, slightly slower
        'gravity': SONIC_GRAVITY * 0.9,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY * 0.8,
        'jump_velocity': SONIC_JUMP_VELOCITY,
        'top_speed': SONIC_TOP_SPEED * 0.9,
        'acceleration': SONIC_ACCELERATION,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'KNUCKLES': {
        'name': 'Knuckles',
        # Knuckles can glide and climb, lower jump
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 0.85,
        'top_speed': SONIC_TOP_SPEED,
        'acceleration': SONIC_ACCELERATION,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'AMY': {
        'name': 'Amy Rose',
        # Amy is slower but has hammer
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 0.9,
        'top_speed': SONIC_TOP_SPEED * 0.8,
        'acceleration': SONIC_ACCELERATION * 0.9,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION * 0.9,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'SUPER_SONIC': {
        'name': 'Super Sonic',
        # Super Sonic has double jump height and speed
        'gravity': SONIC_GRAVITY * 0.8,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 1.5,
        'top_speed': SONIC_TOP_SPEED_SUPER,
        'acceleration': SONIC_ACCELERATION * 2.0,
        'deceleration': SONIC_DECELERATION * 2.0,
        'friction': SONIC_FRICTION * 0.75,
        'air_acceleration': SONIC_AIR_ACCELERATION * 2.0,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
    'SONIC_MANIA': {
        'name': 'Sonic Mania',
        # Modern classic physics
        'gravity': SONIC_GRAVITY,
        'terminal_velocity': SONIC_TERMINAL_VELOCITY,
        'jump_velocity': SONIC_JUMP_VELOCITY * 1.05,
        'top_speed': SONIC_TOP_SPEED * 1.1,
        'acceleration': SONIC_ACCELERATION * 1.15,
        'deceleration': SONIC_DECELERATION,
        'friction': SONIC_FRICTION,
        'air_acceleration': SONIC_AIR_ACCELERATION,
        'roll_friction': SONIC_ROLL_FRICTION,
        'roll_deceleration': SONIC_ROLL_DECEL,
    },
}


def get_presets_directory():
    """Get the directory for storing custom presets"""
    config_dir = bpy.utils.user_resource('CONFIG')
    presets_dir = os.path.join(config_dir, 'sonic_physics_presets')
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
                        preset_name = filename[:-5]
                        presets[preset_name] = preset
                except (json.JSONDecodeError, IOError):
                    pass
    return presets


def update_player_custom_properties(obj, props):
    """Update custom properties on the player object for driver usage"""
    if obj is None:
        return
    
    # Physics state properties
    obj['sonic_velocity_x'] = props.velocity_x
    obj['sonic_velocity_y'] = props.velocity_y
    obj['sonic_velocity_z'] = props.velocity_z
    obj['sonic_ground_speed'] = props.ground_speed
    obj['sonic_speed'] = (props.velocity_x ** 2 + props.velocity_y ** 2 + props.velocity_z ** 2) ** 0.5
    obj['sonic_is_grounded'] = 1.0 if props.is_grounded else 0.0
    obj['sonic_is_jumping'] = 1.0 if props.is_jumping else 0.0
    obj['sonic_is_rolling'] = 1.0 if props.is_rolling else 0.0
    obj['sonic_is_spindashing'] = 1.0 if props.is_spindashing else 0.0
    obj['sonic_is_falling'] = 1.0 if props.is_falling else 0.0
    obj['sonic_spindash_charge'] = props.spindash_charge
    
    # Facing direction
    horizontal_vel = props.velocity_x if props.forward_axis == 'X' else props.velocity_y
    velocity_threshold = 0.01
    if abs(horizontal_vel) > velocity_threshold:
        props.last_facing_direction = 1.0 if horizontal_vel > 0 else -1.0
    
    facing = props.last_facing_direction
    obj['sonic_facing_direction'] = facing
    obj['sonic_is_facing_left'] = 1.0 if facing < 0 else 0.0
    obj['sonic_is_facing_right'] = 1.0 if facing > 0 else 0.0
    obj['sonic_physics_active'] = 1.0 if props.is_active else 0.0


class SonicPhysicsProperties(bpy.types.PropertyGroup):
    """Properties for Sonic Physics simulation"""
    
    is_active: bpy.props.BoolProperty(name="Physics Active", default=False)
    
    # Velocity
    velocity_x: bpy.props.FloatProperty(name="Velocity X", default=0.0)
    velocity_y: bpy.props.FloatProperty(name="Velocity Y", default=0.0)
    velocity_z: bpy.props.FloatProperty(name="Velocity Z", default=0.0)
    ground_speed: bpy.props.FloatProperty(name="Ground Speed", default=0.0)
    
    # State
    is_grounded: bpy.props.BoolProperty(name="Is Grounded", default=True)
    is_jumping: bpy.props.BoolProperty(name="Is Jumping", default=False)
    is_rolling: bpy.props.BoolProperty(name="Is Rolling", default=False)
    is_spindashing: bpy.props.BoolProperty(name="Is Spindashing", default=False)
    is_falling: bpy.props.BoolProperty(name="Is Falling", default=False)
    jump_held: bpy.props.BoolProperty(name="Jump Held", default=False)
    spindash_charge: bpy.props.FloatProperty(name="Spindash Charge", default=0.0, min=0.0, max=1.0)
    
    last_facing_direction: bpy.props.FloatProperty(name="Last Facing Direction", default=1.0)
    
    # Input
    input_left: bpy.props.BoolProperty(name="Move Left", default=False)
    input_right: bpy.props.BoolProperty(name="Move Right", default=False)
    input_jump: bpy.props.BoolProperty(name="Jump", default=False)
    input_down: bpy.props.BoolProperty(name="Down (Roll/Spindash)", default=False)
    
    # Ground level
    ground_level: bpy.props.FloatProperty(name="Ground Level", default=0.0, unit='LENGTH')
    
    # Collision settings
    enable_collision: bpy.props.BoolProperty(name="Enable Collision", default=True)
    collision_padding: bpy.props.FloatProperty(name="Collision Padding", default=0.01, min=0.0)
    use_raycast_collision: bpy.props.BoolProperty(name="Use Raycast Collision", default=False)
    
    # Physics values
    gravity: bpy.props.FloatProperty(name="Gravity", default=SONIC_GRAVITY, min=0.0)
    terminal_velocity: bpy.props.FloatProperty(name="Terminal Velocity", default=SONIC_TERMINAL_VELOCITY, min=0.0)
    jump_velocity: bpy.props.FloatProperty(name="Jump Velocity", default=SONIC_JUMP_VELOCITY)
    top_speed: bpy.props.FloatProperty(name="Top Speed", default=SONIC_TOP_SPEED, min=0.0)
    acceleration: bpy.props.FloatProperty(name="Acceleration", default=SONIC_ACCELERATION, min=0.0)
    deceleration: bpy.props.FloatProperty(name="Deceleration", default=SONIC_DECELERATION, min=0.0)
    friction: bpy.props.FloatProperty(name="Friction", default=SONIC_FRICTION, min=0.0)
    air_acceleration: bpy.props.FloatProperty(name="Air Acceleration", default=SONIC_AIR_ACCELERATION, min=0.0)
    roll_friction: bpy.props.FloatProperty(name="Roll Friction", default=SONIC_ROLL_FRICTION, min=0.0)
    roll_deceleration: bpy.props.FloatProperty(name="Roll Deceleration", default=SONIC_ROLL_DECEL, min=0.0)
    
    # Axis settings
    forward_axis: bpy.props.EnumProperty(
        name="Forward Axis",
        items=[('X', "X Axis", "Move along X axis"), ('Y', "Y Axis", "Move along Y axis")],
        default='X'
    )
    up_axis: bpy.props.EnumProperty(
        name="Up Axis",
        items=[('Y', "Y Axis", "Jump along Y axis"), ('Z', "Z Axis", "Jump along Z axis")],
        default='Z'
    )
    
    preset_name: bpy.props.StringProperty(name="Preset Name", default="My Preset")
    block_shortcuts: bpy.props.BoolProperty(name="Block Shortcuts", default=True)


# Collision types
COLLISION_TYPES = {
    'SOLID': 'Standard solid collision',
    'SPRING_UP': 'Launches Sonic upward',
    'SPRING_SIDE': 'Launches Sonic horizontally',
    'RING': 'Collectible ring',
    'SPIKES': 'Damages Sonic',
    'BUMPER': 'Bounces Sonic away',
    'LOOP': 'Loop path trigger',
    'CHECKPOINT': 'Checkpoint marker',
}


class SonicPhysicsEngine:
    """Core physics engine implementing Sonic physics"""
    
    @staticmethod
    def get_object_bounds(obj):
        """Get AABB for an object in world space"""
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
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
        """Get all objects tagged for collision"""
        collision_objects = []
        for obj in context.scene.objects:
            if obj == player_obj:
                continue
            if 'sonic_collision' in obj.name.lower() or obj.get('sonic_collision', False):
                collision_type = obj.get('sonic_collision_type', 'SOLID')
                collision_objects.append((obj, collision_type))
        return collision_objects
    
    @staticmethod
    def resolve_collision(player_bounds, obstacle_bounds, velocity, forward_axis, up_axis, collision_type='SOLID'):
        """Resolve collision between player and obstacle"""
        p_min_x, p_max_x, p_min_y, p_max_y, p_min_z, p_max_z = player_bounds
        o_min_x, o_max_x, o_min_y, o_max_y, o_min_z, o_max_z = obstacle_bounds
        
        vel_x, vel_y, vel_z = velocity
        offset_x, offset_y, offset_z = 0.0, 0.0, 0.0
        is_grounded = False
        special_action = None
        
        overlap_x = min(p_max_x - o_min_x, o_max_x - p_min_x)
        overlap_y = min(p_max_y - o_min_y, o_max_y - p_min_y)
        overlap_z = min(p_max_z - o_min_z, o_max_z - p_min_z)
        
        if up_axis == 'Z':
            player_center_z = (p_min_z + p_max_z) / 2
            obstacle_center_z = (o_min_z + o_max_z) / 2
            is_above = player_center_z > obstacle_center_z
            
            if collision_type == 'SPRING_UP':
                if is_above:
                    vel_z = 16.0 * PIXEL_TO_BLENDER * 60
                    special_action = 'spring'
                    return (0, 0, 0), (vel_x, vel_y, vel_z), False, special_action
            elif collision_type == 'SPIKES':
                special_action = 'damage'
            elif collision_type == 'RING':
                special_action = 'collect_ring'
                return (0, 0, 0), velocity, False, special_action
            elif collision_type == 'BUMPER':
                # Bounce away from bumper
                vel_x = -vel_x * 1.5
                vel_z = abs(vel_z) * 1.2 if vel_z < 0 else vel_z
                special_action = 'bumper'
                return (0, 0, 0), (vel_x, vel_y, vel_z), False, special_action
            
            if overlap_z <= overlap_x and overlap_z <= overlap_y:
                if is_above:
                    offset_z = o_max_z - p_min_z
                    if vel_z < 0:
                        vel_z = 0
                    is_grounded = True
                else:
                    offset_z = o_min_z - p_max_z
                    if vel_z > 0:
                        vel_z = 0
            else:
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
        
        return (offset_x, offset_y, offset_z), (vel_x, vel_y, vel_z), is_grounded, special_action
    
    @staticmethod
    def update_physics(context, delta_time):
        """Update physics for one frame"""
        obj = context.active_object
        if not obj:
            return
        
        props = context.scene.sonic_physics_props
        if not props.is_active:
            return
        
        pos_x = obj.location.x
        pos_y = obj.location.y
        pos_z = obj.location.z
        
        effective_up_axis = props.up_axis
        if props.forward_axis == 'Y' and props.up_axis == 'Y':
            effective_up_axis = 'Z'
        
        # Ground check
        if effective_up_axis == 'Z':
            props.is_grounded = pos_z <= props.ground_level + 0.01
        else:
            props.is_grounded = pos_y <= props.ground_level + 0.01
        
        # Horizontal movement
        horizontal_vel = SonicPhysicsEngine.update_horizontal(props, delta_time)
        
        # Vertical movement
        vertical_vel = SonicPhysicsEngine.update_vertical(props, delta_time)
        
        # Apply velocities
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
        
        obj.location.x = pos_x
        obj.location.y = pos_y
        obj.location.z = pos_z
        
        # Collision detection
        if props.enable_collision:
            collision_objects = SonicPhysicsEngine.get_collision_objects(context, obj)
            padding = props.collision_padding
            
            for obstacle, collision_type in collision_objects:
                player_bounds = SonicPhysicsEngine.get_object_bounds(obj)
                obstacle_bounds = SonicPhysicsEngine.get_object_bounds(obstacle)
                
                player_bounds = (
                    player_bounds[0] + padding, player_bounds[1] - padding,
                    player_bounds[2] + padding, player_bounds[3] - padding,
                    player_bounds[4] + padding, player_bounds[5] - padding
                )
                
                if SonicPhysicsEngine.check_aabb_collision(player_bounds, obstacle_bounds):
                    vel = (props.velocity_x, props.velocity_y, props.velocity_z)
                    offset, new_vel, is_grounded, special_action = SonicPhysicsEngine.resolve_collision(
                        player_bounds, obstacle_bounds, vel,
                        props.forward_axis, effective_up_axis, collision_type
                    )
                    
                    if special_action == 'collect_ring':
                        obstacle['sonic_collected'] = True
                        obstacle.hide_viewport = True
                        obstacle.hide_render = True
                    
                    obj.location.x += offset[0]
                    obj.location.y += offset[1]
                    obj.location.z += offset[2]
                    
                    props.velocity_x = new_vel[0]
                    props.velocity_y = new_vel[1]
                    props.velocity_z = new_vel[2]
                    
                    if is_grounded:
                        props.is_grounded = True
                        props.is_jumping = False
        
        # Ground plane collision
        if effective_up_axis == 'Z':
            if obj.location.z < props.ground_level:
                obj.location.z = props.ground_level
                props.velocity_z = 0
                props.is_grounded = True
                props.is_jumping = False
                props.is_rolling = False
        else:
            if obj.location.y < props.ground_level:
                obj.location.y = props.ground_level
                props.velocity_y = 0
                props.is_grounded = True
                props.is_jumping = False
                props.is_rolling = False
        
        update_player_custom_properties(obj, props)
    
    @staticmethod
    def update_horizontal(props, delta_time):
        """Update horizontal velocity"""
        velocity = props.velocity_x if props.forward_axis == 'X' else props.velocity_y
        
        direction = 0
        if props.input_left:
            direction -= 1
        if props.input_right:
            direction += 1
        
        # Spindash logic
        if props.is_spindashing:
            if props.input_jump:
                # Charge spindash
                props.spindash_charge = min(1.0, props.spindash_charge + delta_time * 2)
            else:
                # Release spindash
                release_speed = SONIC_SPINDASH_MIN + (SONIC_SPINDASH_MAX - SONIC_SPINDASH_MIN) * props.spindash_charge
                velocity = release_speed * props.last_facing_direction
                props.is_spindashing = False
                props.is_rolling = True
                props.spindash_charge = 0
            return velocity
        
        # Start spindash if grounded, pressing down, and pressing jump
        if props.is_grounded and props.input_down and props.input_jump and abs(velocity) < 0.5:
            props.is_spindashing = True
            props.spindash_charge = 0
            return 0
        
        # Rolling
        if props.is_grounded and props.input_down and abs(velocity) > props.top_speed * 0.3:
            props.is_rolling = True
        
        if props.is_rolling:
            if props.is_grounded:
                # Apply roll friction
                friction = props.roll_friction * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - friction)
                elif velocity < 0:
                    velocity = min(0, velocity + friction)
                
                # Stop rolling if too slow
                if abs(velocity) < 0.5:
                    props.is_rolling = False
            return velocity
        
        # Normal movement
        if props.is_grounded:
            if direction != 0:
                # Check if changing direction (skidding)
                if (velocity > 0 and direction < 0) or (velocity < 0 and direction > 0):
                    # Deceleration
                    velocity += direction * props.deceleration * delta_time
                else:
                    # Acceleration
                    velocity += direction * props.acceleration * delta_time
                
                # Clamp to top speed
                velocity = max(-props.top_speed, min(props.top_speed, velocity))
            else:
                # Apply friction
                friction = props.friction * delta_time
                if velocity > 0:
                    velocity = max(0, velocity - friction)
                elif velocity < 0:
                    velocity = min(0, velocity + friction)
        else:
            # Air control (2x ground acceleration)
            if direction != 0:
                velocity += direction * props.air_acceleration * delta_time
                velocity = max(-props.top_speed, min(props.top_speed, velocity))
        
        props.ground_speed = abs(velocity)
        return velocity
    
    @staticmethod
    def update_vertical(props, delta_time):
        """Update vertical velocity"""
        velocity = props.velocity_z if props.up_axis == 'Z' else props.velocity_y
        
        # Handle jump
        if props.input_jump and props.is_grounded and not props.is_jumping and not props.is_spindashing:
            props.is_jumping = True
            props.jump_held = True
            velocity = props.jump_velocity
            if props.is_rolling:
                props.is_rolling = False  # Jump out of roll
        
        # Variable jump height - releasing jump caps upward velocity
        if not props.input_jump:
            if props.jump_held and velocity > SONIC_JUMP_RELEASE_SPEED:
                velocity = SONIC_JUMP_RELEASE_SPEED
            props.jump_held = False
        
        # Apply gravity
        if not props.is_grounded:
            velocity -= props.gravity * delta_time
            velocity = max(-props.terminal_velocity, velocity)
            props.is_falling = velocity < 0
        else:
            props.is_falling = False
        
        return velocity


class SONIC_OT_start_physics(bpy.types.Operator):
    """Start Sonic Physics Simulation"""
    bl_idname = "sonic.start_physics"
    bl_label = "Start Physics"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _last_time = None
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def modal(self, context, event):
        props = context.scene.sonic_physics_props
        
        if not props.is_active:
            self.cancel(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            current_time = time.time()
            if self._last_time is not None:
                delta_time = min(current_time - self._last_time, 0.1)
                SonicPhysicsEngine.update_physics(context, delta_time)
            self._last_time = current_time
            
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        
        # Input handling
        handled = False
        if event.type == 'LEFT_ARROW':
            props.input_left = event.value == 'PRESS'
            handled = True
        elif event.type == 'RIGHT_ARROW':
            props.input_right = event.value == 'PRESS'
            handled = True
        elif event.type == 'SPACE':
            props.input_jump = event.value == 'PRESS'
            handled = True
        elif event.type == 'DOWN_ARROW':
            props.input_down = event.value == 'PRESS'
            handled = True
        elif event.type in {'ESC'}:
            props.is_active = False
            self.cancel(context)
            return {'CANCELLED'}
        
        if props.block_shortcuts:
            if event.type in {'TIMER', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 
                              'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE',
                              'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                              'WINDOW_DEACTIVATE', 'NONE'}:
                return {'PASS_THROUGH'}
            if event.type not in {'LEFT_ARROW', 'RIGHT_ARROW', 'SPACE', 'DOWN_ARROW', 'ESC'}:
                return {'RUNNING_MODAL'}
            if handled:
                return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        props = context.scene.sonic_physics_props
        
        if props.is_active:
            props.is_active = False
            return {'CANCELLED'}
        
        # Reset
        props.velocity_x = 0
        props.velocity_y = 0
        props.velocity_z = 0
        props.ground_speed = 0
        props.is_jumping = False
        props.is_rolling = False
        props.is_spindashing = False
        props.is_grounded = True
        props.spindash_charge = 0
        props.input_left = False
        props.input_right = False
        props.input_jump = False
        props.input_down = False
        
        obj = context.active_object
        if props.up_axis == 'Z':
            props.ground_level = obj.location.z
        else:
            props.ground_level = obj.location.y
        
        update_player_custom_properties(obj, props)
        props.is_active = True
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0 / 60.0, window=context.window)
        self._last_time = None
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        props = context.scene.sonic_physics_props
        props.is_active = False
        props.input_left = False
        props.input_right = False
        props.input_jump = False
        props.input_down = False
        
        obj = context.active_object
        if obj:
            update_player_custom_properties(obj, props)
        
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)


class SONIC_OT_stop_physics(bpy.types.Operator):
    """Stop Sonic Physics Simulation"""
    bl_idname = "sonic.stop_physics"
    bl_label = "Stop Physics"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.sonic_physics_props.is_active = False
        return {'FINISHED'}


class SONIC_OT_reset_to_defaults(bpy.types.Operator):
    """Reset physics values to Sonic 1 defaults"""
    bl_idname = "sonic.reset_defaults"
    bl_label = "Reset to Sonic 1 Defaults"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.sonic_physics_props
        props.gravity = SONIC_GRAVITY
        props.terminal_velocity = SONIC_TERMINAL_VELOCITY
        props.jump_velocity = SONIC_JUMP_VELOCITY
        props.top_speed = SONIC_TOP_SPEED
        props.acceleration = SONIC_ACCELERATION
        props.deceleration = SONIC_DECELERATION
        props.friction = SONIC_FRICTION
        props.air_acceleration = SONIC_AIR_ACCELERATION
        props.roll_friction = SONIC_ROLL_FRICTION
        props.roll_deceleration = SONIC_ROLL_DECEL
        self.report({'INFO'}, "Physics values reset to Sonic 1 defaults")
        return {'FINISHED'}


class SONIC_OT_load_preset(bpy.types.Operator):
    """Load a physics preset"""
    bl_idname = "sonic.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_key: bpy.props.StringProperty(name="Preset Key")
    
    def execute(self, context):
        props = context.scene.sonic_physics_props
        
        if self.preset_key in PHYSICS_PRESETS:
            preset = PHYSICS_PRESETS[self.preset_key]
        else:
            custom_presets = get_custom_presets()
            if self.preset_key in custom_presets:
                preset = custom_presets[self.preset_key]
            else:
                self.report({'ERROR'}, f"Preset '{self.preset_key}' not found")
                return {'CANCELLED'}
        
        props.gravity = preset.get('gravity', SONIC_GRAVITY)
        props.terminal_velocity = preset.get('terminal_velocity', SONIC_TERMINAL_VELOCITY)
        props.jump_velocity = preset.get('jump_velocity', SONIC_JUMP_VELOCITY)
        props.top_speed = preset.get('top_speed', SONIC_TOP_SPEED)
        props.acceleration = preset.get('acceleration', SONIC_ACCELERATION)
        props.deceleration = preset.get('deceleration', SONIC_DECELERATION)
        props.friction = preset.get('friction', SONIC_FRICTION)
        props.air_acceleration = preset.get('air_acceleration', SONIC_AIR_ACCELERATION)
        props.roll_friction = preset.get('roll_friction', SONIC_ROLL_FRICTION)
        props.roll_deceleration = preset.get('roll_deceleration', SONIC_ROLL_DECEL)
        
        self.report({'INFO'}, f"Loaded preset: {preset.get('name', self.preset_key)}")
        return {'FINISHED'}


class SONIC_OT_save_preset(bpy.types.Operator):
    """Save current physics settings as a preset"""
    bl_idname = "sonic.save_preset"
    bl_label = "Save Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.sonic_physics_props
        preset_name = props.preset_name.strip()
        if not preset_name:
            self.report({'ERROR'}, "Please enter a preset name")
            return {'CANCELLED'}
        
        preset = {
            'name': preset_name,
            'gravity': props.gravity,
            'terminal_velocity': props.terminal_velocity,
            'jump_velocity': props.jump_velocity,
            'top_speed': props.top_speed,
            'acceleration': props.acceleration,
            'deceleration': props.deceleration,
            'friction': props.friction,
            'air_acceleration': props.air_acceleration,
            'roll_friction': props.roll_friction,
            'roll_deceleration': props.roll_deceleration,
        }
        
        presets_dir = get_presets_directory()
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


class SONIC_OT_tag_collision(bpy.types.Operator):
    """Tag selected objects as collision objects"""
    bl_idname = "sonic.tag_collision"
    bl_label = "Tag as Collision"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            obj['sonic_collision'] = True
            obj['sonic_collision_type'] = 'SOLID'
            count += 1
        self.report({'INFO'}, f"Tagged {count} object(s) for collision")
        return {'FINISHED'}


class SONIC_OT_set_collision_type(bpy.types.Operator):
    """Set collision type for selected objects"""
    bl_idname = "sonic.set_collision_type"
    bl_label = "Set Collision Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    collision_type: bpy.props.EnumProperty(
        name="Collision Type",
        items=[
            ('SOLID', "Solid", "Standard solid collision"),
            ('SPRING_UP', "Spring (Up)", "Launches Sonic upward"),
            ('RING', "Ring", "Collectible ring"),
            ('SPIKES', "Spikes", "Damages Sonic"),
            ('BUMPER', "Bumper", "Bounces Sonic away"),
        ],
        default='SOLID'
    )
    
    @classmethod
    def poll(cls, context):
        return context.selected_objects
    
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            obj['sonic_collision'] = True
            obj['sonic_collision_type'] = self.collision_type
            count += 1
        self.report({'INFO'}, f"Set {count} object(s) to {self.collision_type}")
        return {'FINISHED'}


class SONIC_PT_physics_panel(bpy.types.Panel):
    """Panel for Sonic Physics controls"""
    bl_label = "Sonic The Hedgehog Physics"
    bl_idname = "SONIC_PT_physics_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sonic Physics"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.sonic_physics_props
        
        obj = context.active_object
        if obj:
            box = layout.box()
            box.label(text=f"PLAYER: {obj.name}", icon='OUTLINER_OB_MESH')
        else:
            box = layout.box()
            box.label(text="No object selected!", icon='ERROR')
        
        layout.separator()
        
        if props.is_active:
            layout.operator("sonic.stop_physics", text="Stop Physics", icon='PAUSE')
            
            box = layout.box()
            box.label(text="Status:", icon='INFO')
            col = box.column(align=True)
            col.label(text=f"Grounded: {'Yes' if props.is_grounded else 'No'}")
            col.label(text=f"Jumping: {'Yes' if props.is_jumping else 'No'}")
            col.label(text=f"Rolling: {'Yes' if props.is_rolling else 'No'}")
            col.label(text=f"Spindashing: {'Yes' if props.is_spindashing else 'No'}")
            col.label(text=f"Falling: {'Yes' if props.is_falling else 'No'}")
            col.label(text=f"Ground Speed: {props.ground_speed:.2f}")
            
            box = layout.box()
            box.label(text="Controls:", icon='KEYTYPE_KEYFRAME_VEC')
            col = box.column(align=True)
            col.label(text="← → : Move Left/Right")
            col.label(text="↓ : Roll / Crouch")
            col.label(text="Space : Jump")
            col.label(text="↓ + Space : Spindash")
            col.label(text="Esc : Stop")
            
            if props.block_shortcuts:
                box = layout.box()
                box.label(text="🎮 GAME MODE ACTIVE", icon='PLAY')
        else:
            layout.operator("sonic.start_physics", text="Start Physics", icon='PLAY')
            layout.prop(props, "block_shortcuts")


class SONIC_PT_presets_panel(bpy.types.Panel):
    """Panel for Sonic Physics presets"""
    bl_label = "Presets"
    bl_idname = "SONIC_PT_presets_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sonic Physics"
    bl_parent_id = "SONIC_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.sonic_physics_props
        
        box = layout.box()
        box.label(text="Built-in Presets:", icon='PRESET')
        col = box.column(align=True)
        for key, preset in PHYSICS_PRESETS.items():
            op = col.operator("sonic.load_preset", text=preset['name'], icon='PLAY')
            op.preset_key = key
        
        layout.separator()
        box = layout.box()
        box.label(text="Save Current Settings:", icon='FILE_NEW')
        box.prop(props, "preset_name", text="Name")
        box.operator("sonic.save_preset", icon='FILE_TICK')


class SONIC_PT_physics_settings(bpy.types.Panel):
    """Panel for Sonic Physics settings"""
    bl_label = "Physics Settings"
    bl_idname = "SONIC_PT_physics_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sonic Physics"
    bl_parent_id = "SONIC_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.sonic_physics_props
        
        box = layout.box()
        box.label(text="Axes:", icon='EMPTY_AXIS')
        col = box.column(align=True)
        col.prop(props, "forward_axis")
        col.prop(props, "up_axis")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Movement:", icon='CON_LOCLIKE')
        col = box.column(align=True)
        col.prop(props, "top_speed")
        col.prop(props, "acceleration")
        col.prop(props, "deceleration")
        col.prop(props, "friction")
        col.prop(props, "air_acceleration")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Rolling:", icon='MESH_CIRCLE')
        col = box.column(align=True)
        col.prop(props, "roll_friction")
        col.prop(props, "roll_deceleration")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Jumping:", icon='SORT_ASC')
        col = box.column(align=True)
        col.prop(props, "jump_velocity")
        col.prop(props, "gravity")
        col.prop(props, "terminal_velocity")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Environment:", icon='WORLD')
        box.prop(props, "ground_level")
        
        layout.separator()
        layout.operator("sonic.reset_defaults", icon='FILE_REFRESH')


class SONIC_PT_collision_panel(bpy.types.Panel):
    """Panel for Sonic Collision settings"""
    bl_label = "Collision"
    bl_idname = "SONIC_PT_collision_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sonic Physics"
    bl_parent_id = "SONIC_PT_physics_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.sonic_physics_props
        
        layout.prop(props, "enable_collision")
        
        if props.enable_collision:
            layout.prop(props, "collision_padding")
            layout.prop(props, "use_raycast_collision")
            
            layout.separator()
            
            box = layout.box()
            box.label(text="Collision Objects:", icon='MOD_PHYSICS')
            col = box.column(align=True)
            col.operator("sonic.tag_collision", text="Tag as Solid", icon='ADD')
            
            layout.separator()
            
            box = layout.box()
            box.label(text="Set Collision Type:", icon='PHYSICS')
            col = box.column(align=True)
            
            row = col.row(align=True)
            op = row.operator("sonic.set_collision_type", text="Solid")
            op.collision_type = 'SOLID'
            op = row.operator("sonic.set_collision_type", text="Spring")
            op.collision_type = 'SPRING_UP'
            
            row = col.row(align=True)
            op = row.operator("sonic.set_collision_type", text="Ring")
            op.collision_type = 'RING'
            op = row.operator("sonic.set_collision_type", text="Spikes")
            op.collision_type = 'SPIKES'
            
            row = col.row(align=True)
            op = row.operator("sonic.set_collision_type", text="Bumper")
            op.collision_type = 'BUMPER'
            
            layout.separator()
            box = layout.box()
            box.label(text="Tagged Objects:", icon='OUTLINER_OB_MESH')
            
            collision_count = 0
            for obj in context.scene.objects:
                if obj.get('sonic_collision', False) or 'sonic_collision' in obj.name.lower():
                    collision_count += 1
                    row = box.row()
                    col_type = obj.get('sonic_collision_type', 'SOLID')
                    row.label(text=f"{obj.name} [{col_type}]", icon='CUBE')
            
            if collision_count == 0:
                box.label(text="No collision objects", icon='INFO')


# Registration
classes = [
    SonicPhysicsProperties,
    SONIC_OT_start_physics,
    SONIC_OT_stop_physics,
    SONIC_OT_reset_to_defaults,
    SONIC_OT_load_preset,
    SONIC_OT_save_preset,
    SONIC_OT_tag_collision,
    SONIC_OT_set_collision_type,
    SONIC_PT_physics_panel,
    SONIC_PT_presets_panel,
    SONIC_PT_physics_settings,
    SONIC_PT_collision_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sonic_physics_props = bpy.props.PointerProperty(type=SonicPhysicsProperties)


def unregister():
    del bpy.types.Scene.sonic_physics_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
