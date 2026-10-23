Option Explicit

Dim shell, fso, appRoot, keyFile, attempt
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appRoot = fso.GetParentFolderName(WScript.ScriptFullName)
keyFile = fso.BuildPath(appRoot, "app\data\.api-key")

For attempt = 1 To 30
  If fso.FileExists(keyFile) Then
    shell.Run "notepad.exe " & Chr(34) & keyFile & Chr(34), 1, False
    WScript.Quit 0
  End If
  WScript.Sleep 1000
Next

MsgBox "A chave ainda não foi criada. Abra o KAIRON WA, aguarde a inicialização e tente novamente.", vbInformation, "KAIRON WA"
