import oracledb
import gspread
import json
import sys
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def registrar_log_csv(comercializadora, filas, estado, detalles):
    archivo_csv = 'historial_ejecuciones.csv'
    existe = os.path.exists(archivo_csv)
    
    with open(archivo_csv, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['Fecha_Hora', 'Comercializadora', 'Filas_Actualizadas', 'Estado', 'Detalles'])
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([fecha_actual, comercializadora, filas, estado, detalles])

def cargar_configuracion():
    ruta_json = 'comercializadoras.json'
    if not os.path.exists(ruta_json):
        error_msg = f"No se encontró el archivo {ruta_json}"
        print(f"Error: {error_msg}")
        registrar_log_csv("SISTEMA", 0, "ERROR FATAL", error_msg)
        sys.exit(1)
    
    with open(ruta_json, 'r', encoding='utf-8') as file:
        return json.load(file)

def obtener_datos_oracle(nombre_comercializadora):
    usuario = os.environ.get("ORACLE_USER")
    clave = os.environ.get("ORACLE_PASSWORD")
    host = os.environ.get("ORACLE_HOST")
    port = os.environ.get("ORACLE_PORT")
    service_name = os.environ.get("ORACLE_SERVICE_NAME")
    lib_dir = os.environ.get("ORACLE_LIB_DIR")

    dsn_tns = f"""(DESCRIPTION =
       (ADDRESS = (PROTOCOL = TCP)(HOST = {host})(PORT = {port}))
       (CONNECT_DATA =
         (SERVER = DEDICATED)
         (SERVICE_NAME = {service_name})
       )
      )"""
      
    try:
        # Nota: Inicializar el cliente solo una vez si se llama múltiples veces. 
        # Si ya se inicializó, oracledb ignorará o lanzará una advertencia.
        try:
            if lib_dir:
                oracledb.init_oracle_client(lib_dir=lib_dir)
            else:
                oracledb.init_oracle_client()
        except Exception:
            pass # Ya inicializado

        conexion = oracledb.connect(user=usuario, password=clave, dsn=dsn_tns)
        cursor = conexion.cursor()

        # Concatenación: NombreCentro/CodigoArch/Seq (ordenado alfabéticamente)
        # Se elimina espacios alrededor de la barra "/" con TRIM
        query = """
            SELECT DISTINCT 
                TRIM(CEX_APELLIDO_PATERNO) || '/' || TRIM(CDI_IDENTIF) || '/' || CDI_CODIGO_SEQ AS DATO_CONCATENADO
            FROM CO.CO_VW_CENTROS_DISTRIB
            WHERE UPPER(DCA_NOM_VIG) IN ('REGISTRADO', 'SUSPENDIDO')
              AND CEX_APELLIDO_PATERNO IS NOT NULL
              AND UPPER(NOMBRE_COM) LIKE :busqueda
            ORDER BY DATO_CONCATENADO ASC
        """
        
        # El parámetro de búsqueda usa '%' para actuar como LIKE '%NOMBRE%'
        parametro_busqueda = f"%{nombre_comercializadora.upper()}%"
        cursor.execute(query, busqueda=parametro_busqueda)
        
        resultados = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        
        # Retornar una lista plana en lugar de lista de tuplas
        return [fila[0] for fila in resultados], None

    except Exception as e:
        error_msg = str(e)
        print(f"Error en consulta Oracle para {nombre_comercializadora}: {error_msg}")
        return None, error_msg

def subir_a_sheets(cliente_gspread, datos, doc_sheet, pestana):
    try:
        hoja_calculo = cliente_gspread.open(doc_sheet)
        
        # Si la pestaña no existe, se podría crear, pero asumimos que ya existe
        try:
            hoja = hoja_calculo.worksheet(pestana)
        except gspread.exceptions.WorksheetNotFound:
            print(f"La pestaña '{pestana}' no existe en '{doc_sheet}'. Creando nueva...")
            hoja = hoja_calculo.add_worksheet(title=pestana, rows="1000", cols="2")
            
        # Preparar datos para Sheets (lista de listas)
        # Añadimos un encabezado
        datos_formateados = [["DATOS CONCATENADOS"]] + [[dato] for dato in datos]
        
        # Limpiar la hoja y actualizar con nuevos datos
        hoja.clear()
        hoja.update(values=datos_formateados, range_name='A1')
        print(f"Se actualizaron {len(datos)} registros en la pestaña '{pestana}'.")
        return True, None
        
    except gspread.exceptions.SpreadsheetNotFound:
        error_msg = f"No se encontró el documento '{doc_sheet}'. Asegúrate de compartirlo con el correo de la cuenta de servicio."
        print(f"Error actualizando Google Sheets ({pestana}): {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = str(e)
        print(f"Error actualizando Google Sheets ({pestana}): {error_msg}")
        return False, error_msg

def main():
    print("=== INICIANDO SINCRONIZACIÓN MULTI-COMERCIALIZADORA ===")
    
    # 1. Cargar Configuración
    configuraciones = cargar_configuracion()
    print(f"Se encontraron {len(configuraciones)} comercializadoras configuradas.")

    # 2. Autenticación Google Sheets (Una sola vez para todo el script)
    print("Autenticando con Google Sheets...")
    try:
        service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "leafy-thunder-507913-s6-2f92ae133845.json")
        cliente_gspread = gspread.service_account(
            filename=service_account_file
        )
    except Exception as e:
        error_msg = f"Error de autenticación con Google Sheets: {e}"
        print(error_msg)
        print(f"Asegúrate de tener el archivo '{service_account_file}' válido.")
        registrar_log_csv("SISTEMA", 0, "ERROR FATAL", error_msg)
        sys.exit(1)

    # 3. Procesar cada comercializadora
    for conf in configuraciones:
        nombre = conf['nombre_busqueda']
        print(f"\nProcesando: {nombre}...")
        
        # Obtener datos de Oracle
        datos, error_oracle = obtener_datos_oracle(nombre)
        
        if error_oracle:
            registrar_log_csv(nombre, 0, "ERROR", f"Error Oracle: {error_oracle}")
            continue
            
        if not datos:
            print(f"No se encontraron registros para {nombre}.")
            registrar_log_csv(nombre, 0, "ADVERTENCIA", "No se encontraron registros en Oracle")
            continue
            
        print(f"Se obtuvieron {len(datos)} registros de Oracle.")
        
        # Opcional: Mostrar los 3 primeros registros para validación visual
        print("Muestra:")
        for d in datos[:3]:
            print(f"  - {d}")
        
        # Subir a Google Sheets
        exito_sheets, error_sheets = subir_a_sheets(cliente_gspread, datos, conf['doc_sheet'], conf['pestana'])
        
        if exito_sheets:
            registrar_log_csv(nombre, len(datos), "EXITO", "Sincronización completada correctamente")
        else:
            registrar_log_csv(nombre, len(datos), "ERROR", f"Error Sheets: {error_sheets}")

    print("\n=== PROCESO FINALIZADO ===")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main()
