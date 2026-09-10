# Sistema de Automatización de Formularios y Sincronización

Este proyecto se encarga de extraer registros desde una base de datos Oracle y sincronizarlos automáticamente en diferentes archivos de Google Sheets, separados por comercializadora.

---

## 1. ¿Cómo hacer que funcione? (Requisitos)

Para que el programa funcione correctamente, necesitas:

### A) El Archivo de Variables (`.env`)
Debe existir un archivo llamado `.env` en esta misma carpeta, el cual contiene las credenciales de la base de datos Oracle y la ruta al archivo del token de Google. Debe lucir así:

```env
ORACLE_USER=TU_USUARIO
ORACLE_PASSWORD=TU_CLAVE
ORACLE_HOST=IP_DEL_SERVIDOR
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ARCHDB
ORACLE_LIB_DIR=C:\oracle\instantclient-basic-windows.x64-19.32.0.0.0dbru\instantclient_19_32
GOOGLE_SERVICE_ACCOUNT_FILE=leafy-thunder-507913-s6-2f92ae133845.json
```

### B) El Archivo de Configuración (`comercializadoras.json`)
Aquí se define la lista de comercializadoras que se buscarán en Oracle, y en qué archivo de Google Sheets y pestaña se van a pegar. 

### C) El Token de Google (Cuenta de Servicio)
Debe existir el archivo JSON del token (ej. `leafy-thunder-507913-s6-2f92ae133845.json`). Este archivo le permite al programa conectarse silenciosamente a Google Sheets sin pedir contraseñas.

---

## 2. ¿Cómo ejecutar el proceso?

### Proceso Principal
Abre una terminal o consola de comandos en esta carpeta y ejecuta:
```bash
python sincronizador_multi.py
```
*(El script procesará todas las comercializadoras configuradas).*

### Consultas Individuales (Reportes CSV)
Si solo quieres generar un CSV rápido para una comercializadora:
1. Abre el archivo `temp_query.py` en tu editor de código.
2. Modifica la variable `COMERCIALIZADORA = "Nombre"` con la que deseas consultar.
3. Ejecuta: 
   ```bash
   python temp_query.py
   ```
4. Tu reporte se guardará automáticamente en la carpeta `Consultas estaciones`.

---

## 3. Posibles errores y cómo solucionarlos

###  Error: "No se encontró el documento '[Nombre del Excel]'"
**SOLUCIÓN:**  
El programa utiliza un "robot" (cuenta de servicio) para leer y escribir los Google Sheets. Ese robot tiene un correo:  
`sincronizador@leafy-thunder-507913-s6.iam.gserviceaccount.com`

Ve a tu Google Drive, busca el archivo que menciona el error, dale al botón "Compartir", y agrega ese correo dándole permisos de **"Editor"**. *(Tip: Si metes todos tus reportes en una sola carpeta de Drive, puedes compartir directamente toda la carpeta con ese correo).*

###  Error: "Falta GOOGLE_SERVICE_ACCOUNT_FILE" o "No se encontró el archivo leafy-thunder..."
**SOLUCIÓN:**  
Revisa que el archivo JSON del token se encuentre en la carpeta principal del proyecto y que su nombre esté correctamente escrito en el archivo `.env`.

###  Error: Fallo de conexión a Oracle o Timeout
**SOLUCIÓN:**
1. Verifica que estés conectado a la **VPN** si la base de datos es interna.
2. Asegúrate de que las credenciales (IP, usuario y clave) en el archivo `.env` sigan siendo válidas.
3. Verifica que la ruta `ORACLE_LIB_DIR` en el `.env` exista en tu computadora y sea correcta.

###  Error: "No module named oracledb / gspread"
**SOLUCIÓN:**  
Faltan instalar las librerías en tu entorno de Python. Ejecuta en tu consola:
```bash
pip install oracledb gspread python-dotenv
```

---

## 4. Historial de Ejecuciones

Cada vez que el sincronizador principal se ejecuta, dejará un registro en el archivo `historial_ejecuciones.csv`. Ahí puedes revisar rápidamente a qué hora corrió y cuántas filas se actualizaron (o si hubo fallos) en cada comercializadora.
