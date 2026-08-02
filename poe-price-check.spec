# -*- mode: python ; coding: utf-8 -*-
import pathlib
import sys

from PyInstaller.utils.hooks import collect_submodules

HERE = pathlib.Path(SPECPATH)
sys.path.insert(0, str(HERE))
from paths import APP_VERSION

hiddenimports = []
hiddenimports += collect_submodules('keyboard')

# Zasob wersji wpisywany w plik .exe.
#
# Bez niego wlasciwosci pliku w Windowsie sa puste, a SignPath wymaga, zeby
# podpisywane binaria mialy nazwe produktu i wersje. Generujemy go z
# APP_VERSION, zeby przy podbiciu numeru nie zostal stary - reczny plik
# rozjechalby sie przy pierwszym wydaniu, o ktorym ktos zapomni.
_parts = tuple(int(p) for p in APP_VERSION.split('.'))[:3]
_quad = _parts + (0,) * (4 - len(_parts))

VERSION_FILE = HERE / 'build' / 'version_info.txt'
VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
VERSION_FILE.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_quad}, prodvers={_quad},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'poepricecheck.eu'),
      StringStruct('FileDescription', 'Price checking for Path of Exile on cloud gaming'),
      StringStruct('FileVersion', '{APP_VERSION}'),
      StringStruct('InternalName', 'poe-price-check'),
      StringStruct('LegalCopyright', 'MIT License'),
      StringStruct('OriginalFilename', 'poe-price-check.exe'),
      StringStruct('ProductName', 'PoE Price Check'),
      StringStruct('ProductVersion', '{APP_VERSION}'),
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding='utf-8')


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
    version=str(VERSION_FILE),
)
