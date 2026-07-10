@echo off
REM ====================================================
REM  Servidor de impresion - Tienda POS Fiambreria
REM ====================================================
REM  1. Verifica y descarga actualizaciones desde GitHub
REM  2. Arranca el servidor de impresion
REM ====================================================

title Servidor de Impresion - Tienda POS
cd /d C:\TiendaPOS

echo.
echo  ====================================================
echo   SERVIDOR DE IMPRESION - TIENDA POS
echo  ====================================================
echo.

REM -- Paso 1: verificar actualizaciones --
python actualizar.py

echo.
echo   Iniciando servidor... No cierre esta ventana.
echo.

REM -- Paso 2: arrancar el servidor --
python servidor_impresion.py

echo.
echo   El servidor se detuvo. Presione una tecla para cerrar.
pause >nul
