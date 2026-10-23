Option Explicit

Dim shell, fso, appRoot, appDir, dataDir, logDir, nodePath, mainPath
Dim url, backgroundOnly, edgePath, commandLine, servicePid, createResult
Dim wmi, startupInfo, processClass, pidFile, stream, attempt

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appRoot = fso.GetParentFolderName(WScript.ScriptFullName)
appDir = fso.BuildPath(appRoot, "app")
dataDir = fso.BuildPath(appDir, "data")
logDir = fso.BuildPath(dataDir, "logs")
nodePath = fso.BuildPath(appRoot, "runtime\node.exe")
mainPath = fso.BuildPath(appDir, "dist\main.js")
pidFile = fso.BuildPath(dataDir, "kairon-wa.pid")
url = "http://127.0.0.1:2785"
backgroundOnly = HasArgument("--background")

EnsureFolder dataDir
EnsureFolder logDir

If ServerReady(url) Then
  If Not backgroundOnly Then OpenDashboard url
  WScript.Quit 0
End If

If Not fso.FileExists(nodePath) Or Not fso.FileExists(mainPath) Then
  MsgBox "A instalação do KAIRON WA está incompleta. Reinstale o aplicativo.", vbCritical, "KAIRON WA"
  WScript.Quit 2
End If

edgePath = FindBrowserEngine()
If edgePath <> "" Then
  shell.Environment("PROCESS")("PUPPETEER_EXECUTABLE_PATH") = edgePath
End If

commandLine = "cmd.exe /d /s /c " & Chr(34) & Chr(34) & nodePath & Chr(34) & " " & Chr(34) & mainPath & Chr(34) & " >> " & Chr(34) & fso.BuildPath(logDir, "kairon-wa.log") & Chr(34) & " 2>&1" & Chr(34)

Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set startupInfo = wmi.Get("Win32_ProcessStartup").SpawnInstance_
startupInfo.ShowWindow = 0
Set processClass = wmi.Get("Win32_Process")
createResult = processClass.Create(commandLine, appDir, startupInfo, servicePid)

If createResult <> 0 Then
  MsgBox "Não foi possível iniciar o KAIRON WA. Código: " & createResult, vbCritical, "KAIRON WA"
  WScript.Quit 3
End If

Set stream = fso.CreateTextFile(pidFile, True, False)
stream.Write CStr(servicePid)
stream.Close

For attempt = 1 To 90
  If ServerReady(url) Then
    If Not backgroundOnly Then OpenDashboard url
    WScript.Quit 0
  End If
  WScript.Sleep 1000
Next

If Not backgroundOnly Then
  MsgBox "O KAIRON WA demorou mais que o esperado para iniciar. Consulte o arquivo de log na pasta de dados do aplicativo.", vbExclamation, "KAIRON WA"
End If
WScript.Quit 4

Function HasArgument(expected)
  Dim i
  HasArgument = False
  For i = 0 To WScript.Arguments.Count - 1
    If LCase(WScript.Arguments(i)) = LCase(expected) Then
      HasArgument = True
      Exit Function
    End If
  Next
End Function

Sub EnsureFolder(path)
  If Not fso.FolderExists(path) Then fso.CreateFolder path
End Sub

Function ServerReady(address)
  Dim request
  On Error Resume Next
  Set request = CreateObject("WinHttp.WinHttpRequest.5.1")
  request.SetTimeouts 800, 800, 800, 800
  request.Open "GET", address, False
  request.Send
  ServerReady = (Err.Number = 0 And request.Status >= 200 And request.Status < 500)
  Err.Clear
  On Error GoTo 0
End Function

Sub OpenDashboard(address)
  shell.Run address, 1, False
End Sub

Function FindBrowserEngine()
  Dim candidates, item
  candidates = Array( _
    shell.ExpandEnvironmentStrings("%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"), _
    shell.ExpandEnvironmentStrings("%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"), _
    shell.ExpandEnvironmentStrings("%ProgramFiles%\Google\Chrome\Application\chrome.exe"), _
    shell.ExpandEnvironmentStrings("%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"), _
    shell.ExpandEnvironmentStrings("%LocalAppData%\Google\Chrome\Application\chrome.exe") _
  )
  FindBrowserEngine = ""
  For Each item In candidates
    If fso.FileExists(item) Then
      FindBrowserEngine = item
      Exit Function
    End If
  Next
End Function
