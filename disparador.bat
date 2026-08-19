@echo off
chcp 65001 > nul

REM Nombre del archivo donde se guardara el historial
set ARCHIVO_LOG=historial_ejecuciones.txt

echo ===================================================
echo Iniciando sincronizacion Oracle - Google Sheets
echo Los detalles se estan guardando en %ARCHIVO_LOG%...
echo ===================================================

REM Registrar la fecha y hora de inicio en el archivo TXT
echo. >> %ARCHIVO_LOG%
echo =================================================== >> %ARCHIVO_LOG%
echo EJECUCION INICIADA: %date% %time% >> %ARCHIVO_LOG%
echo =================================================== >> %ARCHIVO_LOG%

REM 1. Moverse a la unidad Z y a la carpeta exacta
cd /d "Z:\2 Gestión de Administracion de la Información\Regulación y Normativa\Sistema de Adquisición de Información de OEC\AUTOMATIZACION FORMULARIOS"

REM 2. Ejecutar el script y enviar TODA la salida al TXT
python sincronizador_multi.py >> %ARCHIVO_LOG% 2>&1

REM Registrar la fecha y hora de fin en el archivo TXT
echo EJECUCION FINALIZADA: %date% %time% >> %ARCHIVO_LOG%
echo --------------------------------------------------- >> %ARCHIVO_LOG%

echo Sincronizacion terminada. Revisa "%ARCHIVO_LOG%" para ver si hubo errores.
exit