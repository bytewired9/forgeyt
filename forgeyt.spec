# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['forgeyt.py'],
    pathex=['.'],  # The current directory
    binaries=[],
    datas=[
        ('app', 'app'),  # Include the 'app' folder
        ('assets', 'assets'),  # Include the 'assets' folder
        ('utils', 'utils'),  # Include the 'utils' folder
        ('vars', 'vars'),  # Include the 'vars' folder
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['venv'],  # Exclude the 'venv' folder
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='forgeyt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # This hides the console window
    icon='assets/ForgeYT.ico',  # Set the custom icon
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='forgeyt'
)
