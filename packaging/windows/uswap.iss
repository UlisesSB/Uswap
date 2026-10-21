; Inno Setup script for the USwap Windows installer.
; Build:  ISCC /DAppVersion=0.1.0 packaging\windows\uswap.iss
; Expects:  dist\uswap\  (PyInstaller --onedir output)  and  build\tools\  (FFmpeg, Pandoc, Poppler)

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{B7D0F2C4-5A2E-4C6B-9A31-0A5F00000001}
AppName=USwap
AppVersion={#AppVersion}
AppPublisher=YOUR NAME
AppPublisherURL=https://uarodriguez.com
AppSupportURL=https://github.com/YOUR-USER/uswap/issues
DefaultDirName={autopf}\USwap
DefaultGroupName=USwap
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=USwap-Setup
SetupIconFile=..\..\assets\uswap.ico
UninstallDisplayIcon={app}\uswap.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "contextmenu"; Description: "Add ""Convert with USwap"" to the right-click menu"; GroupDescription: "Integration:"
Name: "addtopath"; Description: "Add USwap to PATH (use the ""uswap"" command in any terminal)"; GroupDescription: "Integration:"

[Files]
Source: "..\..\dist\uswap\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\build\tools\*"; DestDir: "{app}\tools"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\assets\uswap.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\USwap"; Filename: "{app}\uswap.exe"; IconFilename: "{app}\uswap.ico"

[Registry]
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap"; ValueType: string; ValueName: ""; ValueData: "Convert with USwap"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\uswap.ico"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\USwap\command"; ValueType: string; ValueName: ""; ValueData: """{app}\uswap.exe"" ""%1"""; Tasks: contextmenu
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{app}\uswap.exe"; Parameters: "--doctor"; Description: "Check installed tools"; Flags: postinstall nowait skipifsilent unchecked shellexec

[Code]
function NeedsAddPath(Dir: string): Boolean;
var
  Existing: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(Existing) + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Existing, Dir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing) then
    begin
      Dir := ExpandConstant('{app}');
      StringChangeEx(Existing, ';' + Dir, '', True);
      StringChangeEx(Existing, Dir + ';', '', True);
      StringChangeEx(Existing, Dir, '', True);
      RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Existing);
    end;
  end;
end;
