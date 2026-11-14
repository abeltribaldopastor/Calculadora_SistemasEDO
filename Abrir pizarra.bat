@echo off
REM ================================================================
REM  Abrir pizarra.bat  -  Pizarra de sistemas de EDOs (Abel Tribaldo)
REM  Doble clic: arranca el servidor local y abre la web.
REM  Para cerrarla, cierra esta ventana negra.
REM ================================================================
title Pizarra de sistemas de EDOs
cd /d "%~dp0"

set PY=python
where python >nul 2>nul || set PY=py

REM Abre el navegador 2 segundos despues, cuando el servidor ya esta listo
start "" /min cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

echo.
echo   Pizarra de sistemas de EDOs en marcha: http://localhost:8000
echo   Deja esta ventana abierta mientras la uses. Para cerrarla, cierrala.
echo.
REM servidor.py = servidor de Python que no deja al navegador usar copias viejas
%PY% servidor.py

REM Si el servidor no ha podido arrancar (por ejemplo, ya estaba abierto), se queda la ventana para leer el error
if errorlevel 1 pause
