@echo off
REM Przebudowa poe-price-check.exe. Wymaga Pythona i: pip install -r requirements.txt pyinstaller
REM Efekt: dist\poe-price-check.exe (jeden plik, bez zaleznosci)

cd /d "%~dp0"

REM --windowed : bez czarnego okna konsoli. Tryby diagnostyczne (--test-keys itd.)
REM              same podpinaja konsole, patrz applog.py.
REM -u         : bez buforowania, zeby log leciec na biezaco.
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name poe-price-check ^
  --icon icon.ico ^
  --add-data "config.example.json;." ^
  --add-data "icon.ico;." ^
  --collect-submodules keyboard ^
  --python-option u ^
  --noconfirm ^
  main.py

if errorlevel 1 (
  echo.
  echo BUILD NIEUDANY
  exit /b 1
)

echo.
echo Gotowe: dist\poe-price-check.exe
