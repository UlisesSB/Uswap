; USwap - Windows installer (Inno Setup 6)
;
; Built by windows\build.ps1, which first prepares:
;   build\uswap\   uswap.exe made with PyInstaller (--onedir)
;   build\tools\   ffmpeg.exe and ffprobe.exe
; Optional tools (Pandoc, Poppler, Typst, ImageMagick, LibreOffice) are not bundled:
; USwap downloads them from "Optional formats" when the user asks.
;
; Manual build:  ISCC windows\uswap.iss

#ifndef AppVersion
  #define AppVersion "2.1.0"
#endif

[Setup]
AppId={{B7D0F2C4-5A2E-4C6B-9A31-0A5F00000001}
AppName=USwap
AppVersion={#AppVersion}
AppVerName=USwap {#AppVersion}
AppPublisher=Ulises Agustin Rodriguez
AppPublisherURL=https://uarodriguez.com
AppSupportURL=https://github.com/UlisesSB/USwap/issues
AppUpdatesURL=https://github.com/UlisesSB/USwap/releases
DefaultDirName={autopf}\USwap
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=USwap-Setup-{#AppVersion}
SetupIconFile=..\assets\uswap.ico
UninstallDisplayIcon={app}\uswap.ico
LicenseFile=..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
spanish.Integration=Integración:
english.Integration=Integration:
spanish.MenuTask=Agregar "Convert with USwap" al clic derecho (archivos y carpetas)
english.MenuTask=Add "Convert with USwap" to the right-click menu (files and folders)
spanish.SendToTask=Agregar USwap a "Enviar a" (para varios archivos a la vez)
english.SendToTask=Add USwap to "Send to" (for several files at once)
spanish.PathTask=Agregar el comando uswap a la terminal (PATH)
english.PathTask=Add the uswap command to the terminal (PATH)

[Tasks]
Name: "contextmenu"; Description: "{cm:MenuTask}"; GroupDescription: "{cm:Integration}"
Name: "sendto"; Description: "{cm:SendToTask}"; GroupDescription: "{cm:Integration}"
Name: "addtopath"; Description: "{cm:PathTask}"; GroupDescription: "{cm:Integration}"

[Files]
Source: "..\build\uswap\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\build\tools\*"; DestDir: "{app}\tools"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\assets\uswap.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\USwap"; Filename: "{app}\uswap.exe"; IconFilename: "{app}\uswap.ico"
Name: "{usersendto}\USwap"; Filename: "{app}\uswap.exe"; IconFilename: "{app}\uswap.ico"; Tasks: sendto

[Registry]
; files
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap"; ValueType: string; ValueName: ""; ValueData: "Convert with USwap"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\uswap.ico"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap\command"; ValueType: string; ValueName: ""; ValueData: """{app}\uswap.exe"" ""%1"""; Tasks: contextmenu
; folders (converts every file of a kind inside)
Root: HKCU; Subkey: "Software\Classes\Directory\shell\USwap"; ValueType: string; ValueName: ""; ValueData: "Convert with USwap"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\USwap"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\uswap.ico"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\USwap\command"; ValueType: string; ValueName: ""; ValueData: """{app}\uswap.exe"" ""%1"""; Tasks: contextmenu
; PATH
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
function NeedsAddPath(Dir: string): Boolean;
var
  Existing: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing) then
    Result := True
  else
    Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Existing) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Existing, Dir: string;
begin
  if (CurUninstallStep = usPostUninstall) and
     RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing) then
  begin
    Dir := ExpandConstant('{app}');
    StringChangeEx(Existing, ';' + Dir, '', True);
    StringChangeEx(Existing, Dir + ';', '', True);
    StringChangeEx(Existing, Dir, '', True);
    RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing);
  end;
end;
