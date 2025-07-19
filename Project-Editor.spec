# -*- mode: python ; coding: utf-8 -*-

added_files = [
         ( 'src/resources/' , 'resources'),
         ( 'src/resources/autotrack_models', 'resources/autotrack_models' ),
         ( 'src/resources/3dmodels', 'resources/3dmodels' ),
         ( 'src/resources/data', 'resources/data' ),
         ( 'src/resources/fonts', 'resources/fonts' ),
         ( 'src/resources/icons', 'resources/icons' ),
         ( 'src/configs','configs')
         ]

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=added_files,
    hiddenimports=['controller.utils.json_formatter', 'signal_logging'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Project-Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
