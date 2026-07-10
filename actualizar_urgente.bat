@echo off
REM ====================================================
REM  ACTUALIZAR IMPRESORA - Uso urgente
REM ====================================================
REM  Descarga la ultima version del servidor y lo reinicia.
REM  Usar solo si JP indica que hay una correccion urgente.
REM ====================================================

title Actualizar Impresora - Tienda POS
cd /d C:\TiendaPOS

echo.
echo   Actualizando servidor de impresion...
echo.

REM Cerrar el servidor que este corriendo
taskkill /F /IM python.exe /T >nul 2>&1

REM Descargar ultima version
python actualizar.py

echo.
echo   Listo. Reiniciando servidor...
echo.

REM Reiniciar el servidor
start "" "C:\TiendaPOS\iniciar_servidor.bat"

timeout /t 3 >nul
