[Setup]
; 基础配置
AppName=StudyPlayer
AppVersion=1.0.0
AppPublisher=您的名字/工作室
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\StudyPlayer
DefaultGroupName=StudyPlayer
OutputDir=.\dist
OutputBaseFilename=StudyPlayer_Setup_v1.0
Compression=lzma
SolidCompression=yes
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\StudyPlayer.exe

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
; 将 dist\StudyPlayer 目录下的所有文件打包进安装包
Source: "dist\StudyPlayer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 创建开始菜单快捷方式
Name: "{group}\StudyPlayer"; Filename: "{app}\StudyPlayer.exe"
Name: "{group}\卸载 StudyPlayer"; Filename: "{uninstallexe}"
; 创建桌面快捷方式
Name: "{autodesktop}\StudyPlayer"; Filename: "{app}\StudyPlayer.exe"; Tasks: desktopicon

[Registry]
; 注册应用到 "打开方式" (Recommended Apps)
Root: HKCR; Subkey: "Applications\StudyPlayer.exe\SupportedTypes"; ValueType: string; ValueName: ".mp4"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "Applications\StudyPlayer.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\StudyPlayer.exe"" ""%1"""
Root: HKCR; Subkey: ".mp4\OpenWithProgids"; ValueType: string; ValueName: "StudyPlayer.mp4"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "StudyPlayer.mp4"; ValueType: string; ValueName: ""; ValueData: "MP4 视频文件"; Flags: uninsdeletekey
Root: HKCR; Subkey: "StudyPlayer.mp4\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\StudyPlayer.exe"" ""%1"""
Root: HKCR; Subkey: "StudyPlayer.mp4\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\StudyPlayer.exe,0"

[Run]
; 安装完成后提供运行选项
Filename: "{app}\StudyPlayer.exe"; Description: "运行 StudyPlayer"; Flags: nowait postinstall skipifsilent

[Code]
// 检查系统中是否安装了 VLC 播放器
function InitializeSetup(): Boolean;
var
  VLCInstalled: Boolean;
begin
  VLCInstalled := RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\VideoLAN\VLC') or 
                  RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\VideoLAN\VLC');
  
  if not VLCInstalled then
  begin
    MsgBox('注意：检测到您的电脑上可能未安装 VLC 播放器！' + #13#10 + 
           '本程序的核心解码依赖于 VLC 环境。如果运行黑屏或报错，请前往官网下载安装 VLC (64位)。', 
           mbInformation, MB_OK);
  end;
  Result := True;
end;
