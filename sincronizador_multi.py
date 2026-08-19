import oracledb
import gspread
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def cargar_configuracion():
    ruta_json = 'comercializadoras.json'
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontró el archivo {ruta_json}")
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
            WHERE UPPER(DCA_NOM_VIG) = 'REGISTRADO'
              AND UPPER(SEG_NOMBRE) LIKE '%AUTOMOTRIZ%'
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
        return [fila[0] for fila in resultados]

    except Exception as e:
        print(f"Error en consulta Oracle para {nombre_comercializadora}: {e}")
        return []

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
        
    except Exception as e:
        print(f"Error actualizando Google Sheets ({pestana}): {e}")

def main():
    print("=== INICIANDO SINCRONIZACIÓN MULTI-COMERCIALIZADORA ===")
    
    # 1. Cargar Configuración
    configuraciones = cargar_configuracion()
    print(f"Se encontraron {len(configuraciones)} comercializadoras configuradas.")

    # 2. Autenticación Google Sheets (Una sola vez para todo el script)
    print("Autenticando con Google Sheets...")
    try:
        cliente_gspread = gspread.oauth(
            credentials_filename='credenciales.json',
            authorized_user_filename='token.json'
        )
    except Exception as e:
        print(f"Error de autenticación con Google Sheets: {e}")
        print("Asegúrate de tener credenciales.json y token.json válidos.")
        sys.exit(1)

    # 3. Procesar cada comercializadora
    for conf in configuraciones:
        nombre = conf['nombre_busqueda']
        print(f"\nProcesando: {nombre}...")
        
        # Obtener datos de Oracle
        datos = obtener_datos_oracle(nombre)
        
        if not datos:
            print(f"No se encontraron registros para {nombre}.")
            continue
            
        print(f"Se obtuvieron {len(datos)} registros de Oracle.")
        
        # Opcional: Mostrar los 3 primeros registros para validación visual
        print("Muestra:")
        for d in datos[:3]:
            print(f"  - {d}")
        
        # Subir a Google Sheets
        subir_a_sheets(cliente_gspread, datos, conf['doc_sheet'], conf['pestana'])

    print("\n=== PROCESO FINALIZADO ===")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main()
