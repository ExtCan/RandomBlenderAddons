# Contributing to Blender Internal Render Engine

Thank you for your interest in contributing!

## Testing with GitHub Actions

The repository includes automated testing and artifact generation through GitHub Actions.

### Available Workflows

1. **Build Addon** (`.github/workflows/build-addon.yml`)
   - Builds the addon for Linux, Windows, and macOS
   - Creates artifacts for multiple Blender versions (3.6, 4.0)
   - Packages the addon as zip files for easy distribution
   - Runs on: push to main/PR branches, or manually via workflow_dispatch

2. **Test Addon** (`.github/workflows/test-addon.yml`)
   - Validates addon structure and required files
   - Checks Python syntax
   - Tests addon loading in Blender
   - Runs the test script
   - Runs on: every push and pull request

### Accessing Build Artifacts

After a workflow runs successfully:

1. Go to the [Actions tab](https://github.com/ExtCan/RandomBlenderAddons/actions)
2. Click on a workflow run
3. Scroll down to "Artifacts" section
4. Download the artifact for your platform:
   - `blender-internal-render-linux-blenderX.X.zip`
   - `blender-internal-render-windows-blenderX.X.zip`
   - `blender-internal-render-macos-blenderX.X.zip`
   - `ARTIFACTS_README` (installation instructions)

Artifacts are kept for 30 days.

### Manual Workflow Triggers

You can manually trigger the build workflow:

1. Go to Actions → "Build Blender Internal Render Engine"
2. Click "Run workflow"
3. Select branch and click "Run workflow"

This is useful for testing changes on your fork or branch.

## Development Setup

### Prerequisites

- Python 3.10+
- Blender 3.6+ or 4.0+
- Git
- (Optional) CMake and build tools for native engine

### Setting Up

1. Clone the repository:
   ```bash
   git clone https://github.com/ExtCan/RandomBlenderAddons.git
   cd RandomBlenderAddons
   ```

2. Create a symlink to your Blender addons directory:
   ```bash
   # Linux
   ln -s $(pwd)/blender_internal_render ~/.config/blender/3.6/scripts/addons/
   
   # macOS
   ln -s $(pwd)/blender_internal_render ~/Library/Application\ Support/Blender/3.6/scripts/addons/
   
   # Windows (run as admin)
   mklink /D "%APPDATA%\Blender Foundation\Blender\3.6\scripts\addons\blender_internal_render" "%CD%\blender_internal_render"
   ```

3. Enable the addon in Blender preferences

### Testing Your Changes

1. **Test locally in Blender:**
   - Make your changes
   - Restart Blender or reload scripts (F3 → "Reload Scripts")
   - Test the functionality

2. **Run the test script:**
   ```bash
   blender --background --python blender_internal_render/test_render.py
   ```

3. **Check Python syntax:**
   ```bash
   python3 -m py_compile blender_internal_render/*.py
   ```

4. **Push and check CI:**
   - Push your changes to a branch
   - Check the Actions tab for automated test results

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally and ensure CI passes
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### PR Checklist

- [ ] Code follows existing style
- [ ] Added/updated documentation if needed
- [ ] Tested changes in Blender
- [ ] CI tests pass (check Actions tab)
- [ ] No new warnings or errors

## Areas for Contribution

### High Priority
- Complete translation layer implementation
- Improve Python fallback renderer performance
- Add more render features (AO, SSS, etc.)
- Platform-specific build testing and fixes

### Documentation
- Improve BUILD_GUIDE.md
- Add more examples and tutorials
- Document API differences between Blender versions

### Testing
- Add more automated tests
- Test with different Blender versions
- Test on different platforms

### Features
- Viewport rendering support
- Better progress reporting
- Texture baking
- More material types

## Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and small
- Update docstrings when changing functions

## Getting Help

- Open an issue for bugs or questions
- Check existing issues first
- Provide detailed information:
  - Blender version
  - Operating system
  - Steps to reproduce
  - Error messages/logs

## License

By contributing, you agree that your contributions will be licensed under the GNU GPL v2+ license, consistent with the Blender Internal render engine source code.
