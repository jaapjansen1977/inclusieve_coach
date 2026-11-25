$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt
if ($LASTEXITCODE) { throw "Installatie van bouwpakketten mislukt" }
python -m unittest discover -s tests
if ($LASTEXITCODE) { throw "Tests mislukt" }
python -m PyInstaller --clean --noconfirm --windowed --onedir --name InclusieveCoach --collect-all vosk --collect-all _sounddevice_data --collect-all _soundfile_data --add-data "rubric.json;." coach.py
if ($LASTEXITCODE) { throw "Bundelen mislukt" }
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer.iss
if ($LASTEXITCODE) { throw "Installer bouwen mislukt" }
