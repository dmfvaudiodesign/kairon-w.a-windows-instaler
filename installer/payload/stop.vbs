Option Explicit

Dim shell, fso, appRoot, pidFile, stream, servicePid
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appRoot = fso.GetParentFolderName(WScript.ScriptFullName)
pidFile = fso.BuildPath(appRoot, "app\data\kairon-wa.pid")

If fso.FileExists(pidFile) Then
  Set stream = fso.OpenTextFile(pidFile, 1, False)
  servicePid = Trim(stream.ReadAll)
  stream.Close
  If IsNumeric(servicePid) Then
    shell.Run "taskkill.exe /PID " & servicePid & " /T /F", 0, True
  End If
  On Error Resume Next
  fso.DeleteFile pidFile, True
  On Error GoTo 0
End If
