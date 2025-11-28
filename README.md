Rotating ASCII - Export Object as Rotating ASCII python script

pixel2cube - Imports images as colored cubes, best used with sprites. Make sure when you seperate the sprite models to merge by distance, it creates doubles for some reason.

smb_physics - Super Mario Bros. Physics addon that recreates accurate NES Super Mario Bros. physics for a selected object (PLAYER). Features include:
   - Accurate gravity, jump physics with variable height (hold to jump higher)
   - Walking and running speeds with momentum
   - Skid deceleration when changing direction
   - Air control while jumping
   - Collision detection with tagged objects:
     - AABB mode: Fast axis-aligned bounding box collision
     - Raycast mode: Multi-ray collision for complex shapes like stairs (5 rays from player base)
   - Collision types: SOLID, BREAKABLE, SPRING, ENEMY, WATER, FIRE, MOVING, ONE_WAY
   - Surface friction: Set 'smb_friction' property on objects (0.5=icy, 1.0=normal, 2.0=sticky)
   - Swimming mode: Tag objects as WATER to create water zones
   - Physics presets (SMB1, SMB2, SMB3, SMW, NSMB, Luigi styles) with save/load custom presets
   - Custom properties on player object for driver usage (velocity, grounded, facing direction, etc.)
   - Game Mode: Block Blender shortcuts while physics is active for uninterrupted gameplay
   - Customizable physics parameters with reset to SMB defaults
   - Controls: Arrow keys (←→) to move, Space to jump, Shift to run, Esc to stop
