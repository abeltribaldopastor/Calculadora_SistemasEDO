@echo off
REM ================================================================
REM  Abrir pizarra en el movil.bat  -  Pizarra de sistemas de EDOs
REM  Doble clic: arranca el servidor y lo deja abierto a tu Wi-Fi,
REM  para abrir la pizarra desde el movil (mismo Wi-Fi que el PC).
REM  La direccion que hay que escribir en el movil sale en esta ventana.
REM  Para cerrarla, cierra esta ventana negra.
REM ================================================================
title Pizarra de sistemas de EDOs (movil)
cd /d "%~dp0"

set PY=python
where python >nul 2>nul || set PY=py

echo.
%PY% servidor.py --movil

if errorlevel 1 pause
