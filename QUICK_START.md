# Quick Start Guide: Blender 2.79 Modernizer

## Installation (5 minutes)

1. **Download** the addon file:
   - `blender_279_modernizer.py`

2. **Open Blender 2.79**

3. **Install the addon:**
   - Go to `File` → `User Preferences` (or press `Ctrl+Alt+U`)
   - Click the `Add-ons` tab
   - Click `Install Add-on from File...` at the bottom
   - Navigate to and select `blender_279_modernizer.py`
   - Click `Install Add-on from File...`

4. **Enable the addon:**
   - Search for "Modernizer" or scroll to find "System: Blender 2.79 Modernizer"
   - Check the box next to it to enable
   - Click `Save User Settings` at the bottom

5. **Restart Blender** (recommended for keymaps to fully activate)

## First Steps

### Try the Collections Manager

1. Open a scene with some objects
2. Press `T` to open the Tools panel (if not already visible)
3. Look for the "Collections" tab at the top
4. Click "New Collection" and give it a name
5. Select some objects in your scene
6. Click the `+` icon next to your collection to add them

### Test Modern Shortcuts

1. Press `Spacebar` - it should open the search menu!
2. Select an object and press `Numpad .` - it should frame the object
3. Press `Home` - it should frame all objects in view

### Configure Preferences

1. Go back to `File` → `User Preferences` → `Add-ons`
2. Find "Blender 2.79 Modernizer" and expand it
3. Toggle features on/off as you prefer:
   - ☑ Spacebar for Search (recommended)
   - ☑ Collection Manager (recommended)
   - ☑ Modern Transform Tools (UI placeholder)
   - ☑ Left Click Select (UI placeholder)

## Common Usage Patterns

### Organizing Your Scene

**Creating Collections:**
```
1. Select objects you want to group
2. Open Collections panel (T key → Collections tab)
3. Click "New Collection"
4. Name it (e.g., "Lighting", "Characters", "Props")
5. The selected objects are automatically added
```

**Adding Objects Later:**
```
1. Select objects
2. Click the + icon next to the collection name
```

**Removing Objects:**
```
1. Select objects
2. Click the - icon next to the collection name
```

### Modern Navigation Workflow

**Focus on Selection:**
- Select object(s)
- Press `Numpad .`
- View centers on selection

**See Everything:**
- Press `Home`
- View frames all objects

**Quick Command Access:**
- Press `Spacebar`
- Type what you want (e.g., "add cube", "delete", "export")
- Press Enter

## Troubleshooting

### Spacebar Still Plays Animation
- Open User Preferences → Add-ons
- Find Blender 2.79 Modernizer
- Make sure "Spacebar for Search" is checked
- Click "Save User Settings"
- **Restart Blender**

### Collections Panel Not Visible
- Press `T` to toggle the Tools panel
- Make sure you're in Object Mode
- Look for the "Collections" tab at the top of the Tools panel
- Check that "Collection Manager" is enabled in addon preferences

### Addon Not Appearing After Install
- Make sure you selected the right file (`blender_279_modernizer.py`)
- Try searching for "Modernizer" or "2.79" in the addon search
- Check the "System" category filter
- Try installing again

### Keymaps Not Working
- **Always restart Blender** after changing keymap settings
- Check for conflicts with other addons
- Verify the feature is enabled in addon preferences

## Tips & Best Practices

1. **Start with Collections**: Organize your scene into logical collections right from the start
2. **Use Spacebar Search**: Faster than remembering every menu location
3. **Frame Selected Often**: Use `Numpad .` frequently to focus on what you're working on
4. **Save Preferences**: Always click "Save User Settings" after changing addon settings

## What's Not Included (Yet)

This addon provides modern UX improvements, but doesn't change:
- The underlying render engine (still Blender Internal/Cycles 2.79)
- 3D viewport shading (Eevee is 2.80+)
- Node editor functionality
- Modifier system
- Core mesh/object capabilities

These are fundamental Blender changes that can't be backported via addon.

## Need More Help?

- See `README.md` for full feature list
- See `MODERNIZER_OVERVIEW.md` for technical details
- Check Blender 2.79 documentation for general Blender help

## Enjoy Modern Blender 2.79! 🎨
