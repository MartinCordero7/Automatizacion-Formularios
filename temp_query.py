import oracledb
import sys
import csv
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# PARÁMETRO CONFIGURABLE POR EL USUARIO
# ==========================================
# Cambia esta variable por la comercializadora que desees consultar
COMERCIALIZADORA = "PRIMAX"
# ==========================================

def main():
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
        print(f"Conectando a Oracle para consultar datos de: {COMERCIALIZADORA}...")
        try:
            if lib_dir:
                oracledb.init_oracle_client(lib_dir=lib_dir)
            else:
                oracledb.init_oracle_client()
        except Exception:
            pass # Ya inicializado

        conexion = oracledb.connect(user=usuario, password=clave, dsn=dsn_tns)
        cursor = conexion.cursor()

        # Filtros: REGISTRADO, AUTOMOTRIZ, ordenado por Centro de Distribución
        query = """
            SELECT DISTINCT 
                NOMBRE_COM,
                CEX_APELLIDO_PATERNO,
                CDI_IDENTIF,
                DCA_NOM_VIG,
                SEG_NOMBRE,
                TRIM(CEX_APELLIDO_PATERNO) || '/' || TRIM(CDI_IDENTIF) || '/' || CDI_CODIGO_SEQ AS DATO_CONCATENADO
            FROM CO.CO_VW_CENTROS_DISTRIB
            WHERE UPPER(DCA_NOM_VIG) IN ('REGISTRADO', 'SUSPENDIDO')
              AND CEX_APELLIDO_PATERNO IS NOT NULL
              AND UPPER(NOMBRE_COM) LIKE :busqueda
            ORDER BY CEX_APELLIDO_PATERNO ASC
        """
        
        parametro_busqueda = f"%{COMERCIALIZADORA.upper()}%"
        cursor.execute(query, busqueda=parametro_busqueda)
        registros = cursor.fetchall()
        
        if not registros:
            print(f"\n No se encontraron registros para la comercializadora '{COMERCIALIZADORA}'.")
            return

        print(f"\n=== SE ENCONTRARON {len(registros)} REGISTROS ===")
        print("Imprimiendo todos los datos concatenados en consola:")
        for r in registros:
            print(f" -> {r[-1]}")
            
        # Generar nombre de archivo dinámico basado en la comercializadora
        nombre_limpio = COMERCIALIZADORA.lower().replace(' ', '_')
        directorio_salida = "Consultas estaciones"
        
        if not os.path.exists(directorio_salida):
            os.makedirs(directorio_salida)
            
        nombre_archivo = os.path.join(directorio_salida, f"consulta_{nombre_limpio}.csv")
        
        # Guardar en CSV
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['COMERCIALIZADORA', 'NOMBRE CENTRO DE DISTRIBUCIÓN', 'CÓDIGO ARCH', 'ESTADO', 'SEGMENTO', 'DATO_CONCATENADO'])
            writer.writerows(registros)

        print(f"\n ¡Archivo '{nombre_archivo}' generado exitosamente!")

        cursor.close()
        conexion.close()
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main()
