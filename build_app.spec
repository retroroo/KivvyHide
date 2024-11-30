from kivy_deps import sdl2, glew
import os
import kivymd

# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

# Get KivyMD path
kivymd_path = os.path.dirname(kivymd.__file__)

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (kivymd_path, 'kivymd'),
    ],
    hiddenimports=[
        'plyer.platforms.win.filechooser',
        'kivymd',
        'kivymd.uix.button',
        'kivymd.uix.label',
        'kivymd.icon_definitions',
        'PIL._tkinter_finder',
        'stegano.lsb',
        'stegano.exif',
        'stegano.tools',
        'scipy.stats'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name='StegKivy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
