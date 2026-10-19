@echo off
REM OcuLubak installer for Windows. Double-click this file.
REM It sets up the project once and creates OcuLubak shortcuts on the Desktop and in the
REM Start menu. The work is done by launcher\windows\install.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\windows\install.ps1"
echo.
pause
