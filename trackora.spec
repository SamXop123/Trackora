# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['trackora\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['windows', 'windows.tracker', 'windows.daemon'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'pandas', 'scipy', 'matplotlib', 'pygame', 'onnxruntime', 'keras', 'scikit-learn', 'sympy', 'lxml', 'numba', 'llvmlite', 'networkx', 'scikit-image', 'PIL', 'jinja2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='trackora',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['trackora\\assets\\trackora_logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='trackora',
)
