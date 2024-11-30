import PyInstaller.__main__
import os
import shutil
import kivymd

# Get KivyMD path
kivymd_path = os.path.dirname(kivymd.__file__)

# Clean previous builds
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

print(f"KivyMD path: {kivymd_path}")

# Run PyInstaller with spec file only
PyInstaller.__main__.run([
    'build_app.spec',
    '--clean'
])