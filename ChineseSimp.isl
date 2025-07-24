; *** Inno Setup version 6.1.0+ Chinese Simplified messages ***
;
; To download user-contributed translations of this file, go to:
;   https://jrsoftware.org/files/istrans/
;
; Note: When translating this text, do not add periods (.) to the end of
; messages that didn't have them already, because on those messages Inno
; Setup adds the periods automatically (appending a period would result in
; two periods being displayed).

[LangOptions]
LanguageName=Chinese (Simplified)
LanguageID=$0804
LanguageCodePage=936
DialogFontName=Microsoft YaHei UI
DialogFontSize=9
WelcomeFontName=Microsoft YaHei UI
WelcomeFontSize=12
TitleFontName=Microsoft YaHei UI
TitleFontSize=29
CopyrightFontName=Microsoft YaHei UI
CopyrightFontSize=8

[Messages]
; *** Application titles
SetupAppTitle=安装程序
SetupWindowTitle=%1 安装程序
UninstallAppTitle=卸载程序
UninstallAppFullTitle=%1 卸载程序

; *** Misc. common
InformationTitle=信息
ConfirmTitle=确认
ErrorTitle=错误

; *** SetupLdr messages
SetupLdrStartupMessage=这将安装 %1。您想要继续吗？
LdrCannotCreateTemp=无法创建临时文件。安装程序已中止
LdrCannotExecTemp=无法执行临时目录中的文件。安装程序已中止
HelpTextNote=

; *** Startup error messages
LastErrorMessage=%1.%n%n错误 %2: %3
SetupFileMissing=安装程序目录中缺少文件 %1。请修正此问题或获取程序的新副本。
SetupFileCorrupt=安装程序文件已损坏。请获取程序的新副本。
SetupFileCorruptOrWrongVer=安装程序文件已损坏，或者与此版本的安装程序不兼容。请修正此问题或获取程序的新副本。
InvalidParameter=命令行中传递了无效参数:%n%n%1
SetupAlreadyRunning=安装程序已在运行。
WindowsVersionNotSupported=此程序不支持您正在运行的 Windows 版本。
WindowsServicePackRequired=此程序需要 %1 Service Pack %2 或更高版本。
NotOnThisPlatform=此程序无法在 %1 上运行。
OnlyOnThisPlatform=此程序必须在 %1 上运行。
OnlyOnTheseArchitectures=此程序只能在为以下处理器架构设计的 Windows 版本上安装:%n%n%1
WinVersionTooLowError=此程序需要 %1 版本 %2 或更高版本。
WinVersionTooHighError=此程序无法在 %1 版本 %2 或更高版本上安装。
AdminPrivilegesRequired=您必须以管理员身份登录才能安装此程序。
PowerUserPrivilegesRequired=您必须以管理员或 Power Users 组成员身份登录才能安装此程序。
SetupAppRunningError=安装程序检测到 %1 当前正在运行。%n%n请立即关闭所有实例，然后单击"确定"继续，或单击"取消"退出。
UninstallAppRunningError=卸载程序检测到 %1 当前正在运行。%n%n请立即关闭所有实例，然后单击"确定"继续，或单击"取消"退出。

; *** Startup questions
PrivilegesRequiredOverrideTitle=选择安装程序安装模式
PrivilegesRequiredOverrideInstruction=选择安装模式
PrivilegesRequiredOverrideText1=%1 可以为所有用户安装（需要管理员权限），或者仅为您安装。
PrivilegesRequiredOverrideText2=%1 只能为您安装，或者为所有用户安装（需要管理员权限）。
PrivilegesRequiredOverrideAllUsers=为所有用户安装(&A)
PrivilegesRequiredOverrideAllUsersRecommended=为所有用户安装(&A)（推荐）
PrivilegesRequiredOverrideCurrentUser=仅为我安装(&M)
PrivilegesRequiredOverrideCurrentUserRecommended=仅为我安装(&M)（推荐）

; *** Misc. errors
ErrorCreatingDir=安装程序无法创建目录"%1"
ErrorTooManyFilesInDir=无法在目录"%1"中创建文件，因为它包含太多文件

; *** Setup common messages
ExitSetupTitle=退出安装程序
ExitSetupMessage=安装程序未完成。如果您现在退出，程序将不会安装。%n%n您可以稍后再次运行安装程序来完成安装。%n%n退出安装程序？
AboutSetupMenuItem=关于安装程序(&A)...
AboutSetupTitle=关于安装程序
AboutSetupMessage=%1 版本 %2%n%3%n%n%1 主页:%n%4
AboutSetupNote=
TranslatorNote=

; *** Buttons
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonOK=确定
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonYesToAll=全部选是(&A)
ButtonNo=否(&N)
ButtonNoToAll=全部选否(&O)
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
ButtonWizardBrowse=浏览(&R)...
ButtonNewFolder=新建文件夹(&M)

; *** "Select Language" dialog messages
SelectLanguageTitle=选择安装程序语言
SelectLanguageLabel=选择安装期间要使用的语言。

; *** Common wizard text
ClickNext=单击"下一步"继续，或单击"取消"退出安装程序。
BeveledLabel=
BrowseDialogTitle=浏览文件夹
BrowseDialogLabel=在下面的列表中选择一个文件夹，然后单击"确定"。
NewFolderName=新建文件夹

; *** "Welcome" wizard page
WelcomeLabel1=欢迎使用 [name] 安装向导
WelcomeLabel2=这将在您的计算机上安装 [name/ver]。%n%n建议您在继续之前关闭所有其他应用程序。

; *** "Password" wizard page
WizardPassword=密码
PasswordLabel1=此安装程序受密码保护。
PasswordLabel3=请提供密码，然后单击"下一步"继续。密码区分大小写。
PasswordEditLabel=密码(&P):
IncorrectPassword=您输入的密码不正确。请重试。

; *** "License Agreement" wizard page
WizardLicense=许可协议
LicenseLabel=请在继续之前阅读以下重要信息。
LicenseLabel3=请阅读以下许可协议。您必须接受此协议的条款才能继续安装。
LicenseAccepted=我接受协议(&A)
LicenseNotAccepted=我不接受协议(&D)

; *** "Information" wizard pages
WizardInfoBefore=信息
InfoBeforeLabel=请在继续之前阅读以下重要信息。
InfoBeforeClickLabel=准备好继续安装时，请单击"下一步"。
WizardInfoAfter=信息
InfoAfterLabel=请在继续之前阅读以下重要信息。
InfoAfterClickLabel=准备好继续安装时，请单击"下一步"。

; *** "User Information" wizard page
WizardUserInfo=用户信息
UserInfoDesc=请输入您的信息。
UserInfoName=用户名(&U):
UserInfoOrg=组织(&O):
UserInfoSerial=序列号(&S):
UserInfoNameRequired=您必须输入姓名。

; *** "Select Destination Location" wizard page
WizardSelectDir=选择目标位置
SelectDirDesc=应该将 [name] 安装在哪里？
SelectDirLabel3=安装程序将 [name] 安装到以下文件夹。
SelectDirBrowseLabel=要继续，请单击"下一步"。如果您想选择不同的文件夹，请单击"浏览"。
DiskSpaceMBLabel=至少需要 [mb] MB 的可用磁盘空间。
CannotInstallToNetworkDrive=安装程序无法安装到网络驱动器。
CannotInstallToUNCPath=安装程序无法安装到 UNC 路径。
InvalidPath=您必须输入带有驱动器号的完整路径；例如:%n%nC:\APP%n%n或 UNC 路径，格式为:%n%n\\server\share
InvalidDrive=您选择的驱动器或 UNC 共享不存在或无法访问。请选择另一个。
DiskSpaceWarningTitle=磁盘空间不足
DiskSpaceWarning=安装程序至少需要 %1 KB 的可用空间来安装，但所选驱动器只有 %2 KB 可用。%n%n您仍要继续吗？
DirNameTooLong=文件夹名或路径太长。
InvalidDirName=文件夹名无效。
BadDirName32=文件夹名不能包含以下任何字符:%n%n%1
DirExistsTitle=文件夹存在
DirExists=文件夹:%n%n%1%n%n已存在。您仍要安装到该文件夹吗？
DirDoesntExistTitle=文件夹不存在
DirDoesntExist=文件夹:%n%n%1%n%n不存在。您要创建该文件夹吗？

; *** "Select Components" wizard page
WizardSelectComponents=选择组件
SelectComponentsDesc=应该安装哪些组件？
SelectComponentsLabel2=选择您要安装的组件；清除您不想安装的组件。准备好继续时单击"下一步"。
FullInstallation=完全安装
CompactInstallation=紧凑安装
CustomInstallation=自定义安装
NoUninstallWarningTitle=组件存在
NoUninstallWarning=安装程序检测到以下组件已安装在您的计算机上:%n%n%1%n%n取消选择这些组件不会将它们卸载。%n%n您仍要继续吗？
ComponentSize1=%1 KB
ComponentSize2=%1 MB
ComponentsDiskSpaceMBLabel=当前选择需要至少 [mb] MB 磁盘空间。

; *** "Select Additional Tasks" wizard page
WizardSelectTasks=选择附加任务
SelectTasksDesc=应该执行哪些附加任务？
SelectTasksLabel2=选择您希望安装程序在安装 [name] 时执行的附加任务，然后单击"下一步"。

; *** "Select Start Menu Folder" wizard page
WizardSelectProgramGroup=选择开始菜单文件夹
SelectStartMenuFolderDesc=安装程序应该在哪里放置程序的快捷方式？
SelectStartMenuFolderLabel3=安装程序将在以下开始菜单文件夹中创建程序的快捷方式。
SelectStartMenuFolderBrowseLabel=要继续，请单击"下一步"。如果您想选择不同的文件夹，请单击"浏览"。
MustEnterGroupName=您必须输入文件夹名。
GroupNameTooLong=文件夹名或路径太长。
InvalidGroupName=文件夹名无效。
BadGroupName=文件夹名不能包含以下任何字符:%n%n%1
NoProgramGroupCheck2=不创建开始菜单文件夹(&D)

; *** "Ready to Install" wizard page
WizardReady=准备安装
ReadyLabel1=安装程序现在准备开始在您的计算机上安装 [name]。
ReadyLabel2a=单击"安装"继续安装，或单击"上一步"查看或更改任何设置。
ReadyLabel2b=单击"安装"继续安装。
ReadyMemoUserInfo=用户信息:
ReadyMemoDir=目标位置:
ReadyMemoType=安装类型:
ReadyMemoComponents=所选组件:
ReadyMemoGroup=开始菜单文件夹:
ReadyMemoTasks=附加任务:

; *** TDownloadWizardPage wizard page and DownloadTemporaryFile
WizardDownloading=正在下载
DownloadingLabel=请等待安装程序下载其他文件到您的计算机。
ButtonStopDownload=停止下载(&S)
StopDownload=您确定要停止下载吗？
ErrorDownloadAborted=下载已中止
ErrorDownloadFailed=下载失败: %1 %2
ErrorDownloadSizeFailed=获取大小失败: %1 %2
ErrorFileHash1=文件哈希失败: %1
ErrorFileHash2=无效的文件哈希: 期望 %1，找到 %2
ErrorProgress=无效进度: %1 of %2
ErrorFileSize=无效文件大小: 期望 %1，找到 %2

; *** "Preparing to Install" wizard page
WizardPreparing=准备安装
PreparingDesc=安装程序正在准备将 [name] 安装到您的计算机上。
PreviousInstallNotCompleted=先前程序的安装/卸载未完成。您需要重新启动计算机才能完成该安装。%n%n重新启动计算机后，请再次运行安装程序以完成 [name] 的安装。
CannotContinue=安装程序无法继续。请单击"取消"退出。
ApplicationsFound=以下应用程序正在使用需要由安装程序更新的文件。建议您允许安装程序自动关闭这些应用程序。
ApplicationsFound2=以下应用程序正在使用需要由安装程序更新的文件。建议您允许安装程序自动关闭这些应用程序。安装完成后，安装程序将尝试重新启动应用程序。
CloseApplications=自动关闭应用程序(&A)
DontCloseApplications=不关闭应用程序(&D)
ErrorCloseApplications=安装程序无法自动关闭所有应用程序。建议您在继续之前关闭所有使用需要由安装程序更新的文件的应用程序。
PrepareToInstallNeedsRestart=安装程序必须重新启动您的计算机。重新启动计算机后，请再次运行安装程序以完成 [name] 的安装。%n%n您现在要重新启动吗？

; *** "Installing" wizard page
WizardInstalling=正在安装
InstallingLabel=请等待安装程序将 [name] 安装到您的计算机上。

; *** "Setup Completed" wizard page
FinishedHeadingLabel=完成 [name] 安装向导
FinishedLabelNoIcons=安装程序已完成在您的计算机上安装 [name]。
FinishedLabel=安装程序已完成在您的计算机上安装 [name]。可以通过选择已安装的图标来启动应用程序。
ClickFinish=单击"完成"退出安装程序。
FinishedRestartLabel=要完成 [name] 的安装，安装程序必须重新启动您的计算机。您现在要重新启动吗？
FinishedRestartMessage=要完成 [name] 的安装，安装程序必须重新启动您的计算机。%n%n您现在要重新启动吗？
ShowReadmeCheck=是，我想查看 README 文件
YesRadio=是，立即重新启动计算机(&Y)
NoRadio=否，我将稍后重新启动计算机(&N)
RunEntryExec=运行 %1
RunEntryShellExec=查看 %1

; *** "Setup Needs the Next Disk" stuff
ChangeDiskTitle=安装程序需要下一张磁盘
SelectDiskLabel2=请插入磁盘 %1 并单击"确定"。%n%n如果此磁盘上的文件可以在下面显示的文件夹以外的文件夹中找到，请输入正确的路径或单击"浏览"。
PathLabel=路径(&P):
FileNotInDir2=文件"%1"无法在"%2"中找到。请插入正确的磁盘或选择另一个文件夹。
SelectDirectoryLabel=请指定下一张磁盘的位置。

; *** Installation phase messages
SetupAborted=安装程序未完成。%n%n请修正问题并重新运行安装程序。
AbortRetryIgnoreSelectAction=选择操作
AbortRetryIgnoreRetry=重试(&T)
AbortRetryIgnoreIgnore=忽略错误并继续(&I)
AbortRetryIgnoreCancel=取消安装

; *** Installation status messages
StatusClosingApplications=正在关闭应用程序...
StatusCreateDirs=正在创建目录...
StatusExtractFiles=正在提取文件...
StatusCreateIcons=正在创建快捷方式...
StatusCreateIniEntries=正在创建 INI 条目...
StatusCreateRegistryEntries=正在创建注册表条目...
StatusRegisterFiles=正在注册文件...
StatusSavingUninstall=正在保存卸载信息...
StatusRunProgram=正在完成安装...
StatusRestartingApplications=正在重新启动应用程序...
StatusRollback=正在回滚更改...

; *** Misc. errors
ErrorInternal2=内部错误: %1
ErrorFunctionFailedNoCode=%1 失败
ErrorFunctionFailed=%1 失败；代码 %2
ErrorFunctionFailedWithMessage=%1 失败；代码 %2.%n%3
ErrorExecutingProgram=无法执行文件:%n%1

; *** Registry errors
ErrorRegOpenKey=打开注册表项时出错:%n%1\%2
ErrorRegCreateKey=创建注册表项时出错:%n%1\%2
ErrorRegWriteKey=写入注册表项时出错:%n%1\%2

; *** INI errors
ErrorIniEntry=在文件"%1"中创建 INI 条目时出错。

; *** File copying errors
FileAbortRetryIgnoreSkipNotRecommended=跳过此文件(&S)（不推荐）
FileAbortRetryIgnoreIgnoreNotRecommended=忽略错误并继续(&I)（不推荐）
SourceIsCorrupted=源文件已损坏
SourceDoesntExist=源文件"%1"不存在
ExistingFileReadOnly=现有文件标记为只读。%n%n选择"重试"删除只读属性并重试，选择"忽略"跳过此文件，或选择"取消"退出安装程序。
ExistingFileReadOnlyRetry=删除只读属性并重试(&R)
ExistingFileReadOnlyIgnore=跳过此文件(&S)
ErrorReadingExistingDest=尝试读取现有文件时出错:
FileExists=文件已存在。%n%n您要安装程序覆盖它吗？
ExistingFileNewer=现有文件比安装程序尝试安装的文件更新。建议您保留现有文件。%n%n您要保留现有文件吗？
ErrorChangingAttr=尝试更改现有文件的属性时出错:
ErrorCreatingTemp=尝试在目标目录中创建文件时出错:
ErrorReadingSource=尝试读取源文件时出错:
ErrorCopying=尝试复制文件时出错:
ErrorReplacingExistingFile=尝试替换现有文件时出错:
ErrorRestartReplace=RestartReplace 失败:
ErrorRenamingTemp=尝试重命名目标目录中的文件时出错:
ErrorRegisterServer=无法注册 DLL/OCX: %1
ErrorRegSvr32Failed=RegSvr32 失败，退出代码 %1
ErrorRegisterTypeLib=无法注册类型库: %1

; *** Uninstall display name markings
UninstallDisplayNameMark=%1 (%2)
UninstallDisplayNameMarks=%1 (%2, %3)
UninstallDisplayNameMark32Bit=32-bit
UninstallDisplayNameMark64Bit=64-bit
UninstallDisplayNameMarkAllUsers=所有用户
UninstallDisplayNameMarkCurrentUser=当前用户

[CustomMessages]
NameAndVersion=%1 版本 %2
AdditionalIcons=附加图标:
CreateDesktopIcon=创建桌面图标(&D)
CreateQuickLaunchIcon=创建快速启动图标(&Q)
ProgramOnTheWeb=%1 网站
UninstallProgram=卸载 %1
LaunchProgram=启动 %1
AssocFileExtension=将 %1 与 %2 文件扩展名关联(&A)
AssocingFileExtension=正在将 %1 与 %2 文件扩展名关联...
AutoStartProgramGroupDescription=启动:
AutoStartProgram=自动启动 %1
AddonHostProgramNotFound=在您选择的文件夹中找不到 %1。%n%n您仍要继续吗？
