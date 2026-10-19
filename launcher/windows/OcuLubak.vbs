' Runs launch.ps1 or stop.ps1 with no console window. The OcuLubak shortcuts point here:
'   wscript.exe OcuLubak.vbs start    (or: stop)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)

script = "launch.ps1"
If WScript.Arguments.Count > 0 Then
  If LCase(WScript.Arguments(0)) = "stop" Then script = "stop.ps1"
End If

sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & here & "\" & script & """", 0, False
