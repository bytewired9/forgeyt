# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['forgeyt.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('./app', 'app/'),
        ('./assets', 'assets/'),
        ('./utils', 'utils/'),
        ('./vars', 'vars/'),
        ('./ffmpeg/ffmpeg.exe', '.'),
        ('./ffmpeg/ffprobe.exe', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'email', 'pydoc', 'doctest', 'http', 'xml',
        'asyncio', 'sqlite3', 'logging.config', 'distutils'
    ],
    noarchive=False,
    optimize=2,  # Optimize to remove docstrings and asserts
)

pyz = PYZ(a.pure, cipher=None, compress=True)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ForgeYT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,   # strip=True doesn't work on Windows
    upx=True,  # Enable UPX compression
    upx_exclude=['ffmpeg.exe', 'ffprobe.exe'],  # Don't compress ffmpeg.exe
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\ForgeYT.ico'],
)
