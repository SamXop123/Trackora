; Trackora Windows Installer Compilation Script (Inno Setup)
; Compiles the build outputs under dist/trackora-dashboard into a professional setup wizard.

[Setup]
AppName=Trackora
AppVersion=2.2.1
AppPublisher=SamXop123
AppPublisherURL=https://github.com/SamXop123/Trackora
DefaultDirName={localappdata}\Programs\Trackora
DefaultGroupName=Trackora
UninstallDisplayIcon={app}\trackora-dashboard.exe
OutputDir=dist-installer
OutputBaseFilename=TrackoraSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableDirPage=no
DisableProgramGroupPage=yes
DirExistsWarning=no
CloseApplications=yes
SetupIconFile=trackora\assets\trackora_logo.ico
ChangesAssociations=yes

[InstallDelete]
; Clean previous internal bundle on upgrade to prevent stale cached PySide / Python DLLs
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\trackora-dashboard\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Trackora"; Filename: "{app}\trackora-dashboard.exe"; IconFilename: "{app}\_internal\trackora\assets\trackora_logo.ico"
Name: "{userdesktop}\Trackora"; Filename: "{app}\trackora-dashboard.exe"; IconFilename: "{app}\_internal\trackora\assets\trackora_logo.ico"

[Run]
Filename: "{app}\trackora-dashboard.exe"; Description: "Launch Trackora"; Flags: postinstall nowait

[Code]
procedure TaskKill(FileName: String);
var
  ResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM ' + FileName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeSetup(): Boolean;
begin
  TaskKill('trackora-dashboard.exe');
  TaskKill('trackora.exe');
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  TaskKill('trackora-dashboard.exe');
  TaskKill('trackora.exe');
  Result := True;
end;
