; Trackora Windows Installer Compilation Script (Inno Setup)
; Compiles the build outputs under dist/trackora-dashboard into a professional setup wizard.

[Setup]
AppName=Trackora
AppVersion=2.0.0
AppPublisher=SamXop123
AppPublisherURL=https://github.com/SamXop123/Trackora
DefaultDirName={localappdata}\Programs\Trackora
DefaultGroupName=Trackora
UninstallDisplayIcon={app}\trackora-dashboard.exe
OutputDir=dist-installer
OutputBaseFilename=TrackoraSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
SetupIconFile=trackora\assets\trackora_logo.ico

[Files]
Source: "dist\trackora-dashboard\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Trackora"; Filename: "{app}\trackora-dashboard.exe"; IconFilename: "{app}\_internal\trackora\assets\trackora_logo.png"
Name: "{userdesktop}\Trackora"; Filename: "{app}\trackora-dashboard.exe"; IconFilename: "{app}\_internal\trackora\assets\trackora_logo.png"

[Run]
Filename: "{app}\trackora-dashboard.exe"; Description: "Launch Trackora"; Flags: postinstall nowait
