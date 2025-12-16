# GitHub Actions & Artifacts - Quick Reference

## Overview

Two GitHub Actions workflows have been added to automate testing and distribution of the Blender Internal render engine addon.

## Workflows

### 1. Build Addon (`build-addon.yml`)

**Purpose:** Build and package the addon for multiple platforms and Blender versions

**Platforms:**
- Linux (Ubuntu latest)
- Windows (Visual Studio 2022)
- macOS (latest)

**Blender Versions:**
- 3.6 (LTS)
- 4.0

**What it does:**
1. Clones Blender source for headers
2. Attempts to build native engine (with continue-on-error)
3. Packages addon as clean zip (without build artifacts)
4. Uploads artifacts for 30 days

**Triggers:**
- Push to `main` or `copilot/add-blender-internal-render-addon`
- Pull requests to `main`
- Manual via workflow_dispatch

**Artifacts Generated:**
- `blender-internal-render-linux-blender3.6.zip`
- `blender-internal-render-linux-blender4.0.zip`
- `blender-internal-render-windows-blender3.6.zip`
- `blender-internal-render-windows-blender4.0.zip`
- `blender-internal-render-macos-blender3.6.zip`
- `blender-internal-render-macos-blender4.0.zip`
- `ARTIFACTS_README.md` (installation instructions)

### 2. Test Addon (`test-addon.yml`)

**Purpose:** Validate addon structure and functionality

**What it does:**
1. **Validate Structure:**
   - Checks all required files exist
   - Validates Python syntax
   
2. **Test Installation:**
   - Downloads Blender 3.6
   - Installs addon
   - Enables addon via Python
   - Verifies render engine is registered
   - Runs test render script

**Triggers:**
- Every push to branch
- Every pull request
- Manual via workflow_dispatch

## Using Artifacts

### For Users

1. Go to [GitHub Actions](https://github.com/ExtCan/RandomBlenderAddons/actions)
2. Click latest "Build Blender Internal Render Engine" workflow
3. Scroll to "Artifacts" section
4. Download for your platform and Blender version
5. Extract zip file
6. Copy `blender_internal_render` folder to Blender addons directory:
   - Linux: `~/.config/blender/X.X/scripts/addons/`
   - macOS: `~/Library/Application Support/Blender/X.X/scripts/addons/`
   - Windows: `%APPDATA%\Blender Foundation\Blender\X.X\scripts\addons\`
7. Enable in Blender preferences

### For Developers

**Manually trigger build:**
1. Go to Actions → "Build Blender Internal Render Engine"
2. Click "Run workflow"
3. Select your branch
4. Click "Run workflow"
5. Wait for completion
6. Download artifacts from the run

**Check test results:**
- Every push automatically runs tests
- Check the green checkmark or red X next to commit
- Click for detailed logs

## What's Included in Artifacts

Each artifact contains:
- ✅ All UI modules (render, material, texture, world, lamp, render layer)
- ✅ Python fallback renderer (works immediately)
- ✅ Original C/C++ source code (for optional compilation)
- ✅ Build system (CMake + scripts)
- ✅ Complete documentation (README, BUILD_GUIDE, etc.)
- ✅ Test script

## Artifact Retention

- Artifacts are kept for **30 days**
- Download within this period
- Older artifacts are automatically deleted

## CI/CD Status Badges

You can add these to README:

```markdown
![Build Status](https://github.com/ExtCan/RandomBlenderAddons/actions/workflows/build-addon.yml/badge.svg)
![Test Status](https://github.com/ExtCan/RandomBlenderAddons/actions/workflows/test-addon.yml/badge.svg)
```

## Troubleshooting

**Workflow fails:**
- Check the logs in Actions tab
- Red X indicates failure
- Click for detailed error messages

**Native build fails (expected):**
- Build workflow has `continue-on-error: true` for native compilation
- This is expected until translation layer is complete
- Python fallback is always included

**Artifact not found:**
- Check workflow completed successfully (green checkmark)
- Artifacts only available for 30 days
- Re-run workflow if needed

## Future Improvements

Possible enhancements:
- [ ] Pre-compile native engine when translation layer is complete
- [ ] Create releases with attached binaries
- [ ] Add more Blender versions (4.1, 4.2, etc.)
- [ ] Add code coverage reports
- [ ] Add performance benchmarks

## Documentation

See also:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Full CI/CD documentation
- [README.md](../blender_internal_render/README.md) - Addon documentation
- [BUILD_GUIDE.md](../blender_internal_render/BUILD_GUIDE.md) - Build instructions
