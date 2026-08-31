# -*- mode: python ; coding: utf-8 -*-
"""Spec macOS - siostrzany plik poe-price-check.spec, ale dla .app.

Roznice od wersji windowsowej, i dlaczego:

- BUNDLE zamiast samego EXE: to jest mechanizm PyInstallera specyficzny dla
  macOS, ktory sklada folder .app z poprawnym Info.plist. Wymaga trybu
  "onedir" (EXE z exclude_binaries=True + COLLECT), bo BUNDLE nie umie
  zapakowac buildu onefile.
- Ikona: .icns, nie .ico - Windows i macOS uzywaja innych formatow. Plik
  build/icon.icns jest generowany w CI z icon.png (sips + iconutil, oba
  dostepne tylko na macOS), a nie trzymany w repo jako binarka.
- NSAppleEventsUsageDescription w Info.plist: macOS pokazuje ten tekst w
  oknie proszenia o uprawnienie Accessibility/Automation, ktorego program
  potrzebuje do wykrywania okna na wierzchu i przywracania fokusu
  (winutil_macos.py, przez System Events). Bez tego klucza system i tak
  o to zapyta, ale bez wyjasnienia po co.
- Brak zasobu wersji jak na Windows (StringFileInfo) - to mechanizm PE,
  macOS bierze wersje z CFBundleShortVersionString/CFBundleVersion nizej.
"""

import pathlib
import sys

from PyInstaller.utils.hooks import collect_submodules

HERE = pathlib.Path(SPECPATH)
sys.path.insert(0, str(HERE))
from paths import APP_VERSION

hiddenimports = []
# Nie 'keyboard' - na macOS uzywamy 'pynput' (patrz hotkeys_macos.py).
# pynput laduje swoj backend Quartz/Cocoa dynamicznie po nazwie modulu,
# co PyInstaller bez hiddenimports czesto gubi.
hiddenimports += collect_submodules('pynput')

ICNS = HERE / 'build' / 'icon.icns'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.example.json', '.'), ('icon.png', '.')],
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
    [],
    exclude_binaries=True,
    name='poe-price-check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Jak na Windows: UPX-owanie zwieksza szanse na falszywy alarm skanera
    # (na macOS to Gatekeeper/XProtect), a oszczednosc nie jest tego warta.
    upx=False,
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
    upx=False,
    name='poe-price-check',
)

app = BUNDLE(
    coll,
    name='PoE Price Check.app',
    icon=str(ICNS) if ICNS.exists() else None,
    bundle_identifier='eu.poepricecheck.app',
    version=APP_VERSION,
    info_plist={
        'CFBundleName': 'PoE Price Check',
        'CFBundleDisplayName': 'PoE Price Check',
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': (
            'PoE Price Check needs to control System Events to detect the '
            'foreground window and restore focus to the game after a price '
            'check.'
        ),
    },
)
