# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('keyboard')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.example.json', '.'), ('icon.ico', '.')],
    hiddenimports=hiddenimports,
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
    [('u', None, 'OPTION')],
    name='poe-price-check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX celowo wylaczone. Pakowanie nim to jeden z czestszych powodow
    # falszywych alarmow antywirusow - zlosliwe oprogramowanie uzywa go
    # notorycznie, wiec silniki traktuja sama obecnosc UPX jako sygnal.
    # Oszczednosc kilku MB nie jest warta ostrzezen przy kazdym pobraniu.
    # (Dotad ratowal nas przypadek: upx=True, ale UPX nie byl zainstalowany.)
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
