@echo off
REM Batch file to execute the PowerShell script directly
powershell -ExecutionPolicy Bypass -File "%~dp0deploy_container_app_fixed.ps1"
