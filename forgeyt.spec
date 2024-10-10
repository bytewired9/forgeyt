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
    hiddenimports=[],  # Include hidden imports if necessary
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['venv'],  # Exclude the 'venv' folder
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,  # Ensure no archive is used, making it fully standalone
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,  # Include all binaries
    name='forgeyt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # No UPX compression to avoid issues with certain binaries
    console=False,  # Hide the console window
    icon='assets/ForgeYT.ico',  # Set the custom icon
)

coll = COLLECT(
    exe,
    a.binaries,  # Include all necessary binaries
    a.zipfiles,
    a.datas,  # Include all necessary data files
    strip=False,
    upx=False,  # No UPX compression
    name='forgeyt'
)
