# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['trackora\\gui\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('trackora/assets', 'trackora/assets')],
    hiddenimports=[],
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
    name='trackora-dashboard',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='trackora-dashboard',
)
