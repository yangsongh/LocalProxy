
#define MyAppName "LocalProxy"
#define MyAppVersion "202606171"
#define MyAppPublisher "Traceless"
#define MyAppExeName "LocalProxy.exe"

[Setup]
AppId={{D11E115C-0971-4C9D-8202-1BE06DF85844}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={userappdata}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
InfoBeforeFile=welcome.txt
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=LocalProxySetup
SolidCompression=yes
WizardStyle=modern dynamic
DirExistsWarning=no
CreateUninstallRegKey=no

[Languages]
Name: "Chinese"; MessagesFile: "compiler:Languages\Chinese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Dirs]
Name: "{app}\logs"; Attribs: hidden system

[Files]
Source: "..\build\LocalProxy\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\LocalProxy\Updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\LocalProxy\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\LocalProxy\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
