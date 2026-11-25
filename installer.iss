[Setup]
AppName=Inclusieve Coach
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\InclusieveCoach
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
OutputDir=output
OutputBaseFilename=InclusieveCoach-Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\InclusieveCoach.exe

[Files]
Source: "dist\InclusieveCoach\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "README.md"; DestDir: "{app}"
Source: "tests\audio\*.flac"; DestDir: "{app}\Voorbeelden"

Source: "tests\*.json"; DestDir: "{app}\Voorbeelden"

[Icons]
Name: "{userprograms}\Inclusieve Coach"; Filename: "{app}\InclusieveCoach.exe"
