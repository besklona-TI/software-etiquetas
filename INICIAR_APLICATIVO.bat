@echo off
title SmartLabel Pro - Studio de Etiquetas SAP
chcp 65001 >nul
cls

echo ====================================================================
echo             SMARTLABEL PRO - STUDIO DE ETIQUETAS SAP
echo ====================================================================
echo.
echo   Iniciando o aplicativo para voce...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [+] Python detectado. Iniciando servidor local com suporte a impressoras...
    start "" python servidor.py
) else (
    echo   [!] Python nao detectado no sistema.
    echo   [+] Abrindo o aplicativo em modo local autonomo no navegador...
    start "" "%~dp0app\index.html"
)

echo.
echo   Aplicativo aberto no seu navegador padrao!
echo   Pode minimizar esta janela.
echo ====================================================================
timeout /t 5 >nul

