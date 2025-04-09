import pandas as pd
import numpy as np
from supabase import create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_excel(ruta_archivo):
    """Cargar el archivo Excel de distancias"""
    try:
        try:
            df = pd.read_excel(ruta_archivo, header=1, engine='openpyxl')
        except:
            df = pd.read_excel(ruta_archivo, header=1, engine='xlrd')
        
        print(f"Archivo Excel cargado correctamente. Dimensiones: {df.shape}")
        return df
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return None

def importar_ciudades(df):
    """Importar ciudades a la base de datos y retornar diccionario de mapeo"""
    # Limpiar tabla si es necesario
    try:
        # Usar cláusula WHERE que afecte a todas las filas
        supabase.table('ciudades').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Nota: No se pudo limpiar la tabla: {e}")
    
    # Obtener la lista de ciudades del Excel
    ciudades = []
    for i in range(len(df)):
        # Las ciudades están en la segunda columna (índice 1)
        nombre_ciudad = df.iloc[i, 1]
        indice_original = df.iloc[i, 0]  # La primera columna es el índice original
        
        # Verificar que sean datos válidos (no encabezados)
        if pd.notna(nombre_ciudad) and pd.notna(indice_original):
            try:
                # Intentar convertir a entero, si falla es porque es un encabezado
                indice = int(indice_original)
                ciudades.append({
                    'nombre': str(nombre_ciudad),
                    'indice_original': indice
                })
            except (ValueError, TypeError):
                # Saltar filas que no tienen índice numérico
                continue
    
    # Insertar ciudades en la base de datos
    resultado = supabase.table('ciudades').insert(ciudades).execute()
    
    # Obtener todas las ciudades para crear un mapeo
    respuesta = supabase.table('ciudades').select('id, nombre').execute()
    
    # Crear diccionario para mapear nombre de ciudad a ID
    mapeo_ciudades = {ciudad['nombre']: ciudad['id'] for ciudad in respuesta.data}
    
    print(f"Se importaron {len(ciudades)} ciudades a la base de datos")
    return mapeo_ciudades

def importar_distancias(df, mapeo_ciudades):
    """Importar las distancias entre ciudades a la base de datos"""
    # Limpiar tabla si es necesario
    try:
        supabase.table('distancias').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"Nota: No se pudo limpiar la tabla: {e}")
    
    # Lista para almacenar todas las distancias
    distancias = []
    
    # Obtener nombres de ciudades válidos (omitiendo encabezados)
    ciudades = []
    for i in range(len(df)):
        ciudad = df.iloc[i, 1]
        if pd.notna(ciudad) and ciudad in mapeo_ciudades:
            ciudades.append(ciudad)
    
    print(f"Procesando distancias para {len(ciudades)} ciudades...")
    
    # Para cada par de ciudades, obtener la distancia
    for i, ciudad_origen in enumerate(ciudades):
        for j, ciudad_destino in enumerate(ciudades):
            if i != j:  # No guardar distancia de una ciudad a sí misma
                # La distancia está en la celda [i, j+2]
                distancia = df.iloc[i, j+2]
                
                if pd.notna(distancia) and distancia > 0:
                    # Obtener IDs de las ciudades desde el mapeo
                    origen_id = mapeo_ciudades[ciudad_origen]
                    destino_id = mapeo_ciudades[ciudad_destino]
                    
                    distancias.append({
                        'origen_id': origen_id,
                        'destino_id': destino_id,
                        'distancia': float(distancia)
                    })
    
    # Importar distancias en lotes para evitar límites de tamaño
    tamano_lote = 1000
    for i in range(0, len(distancias), tamano_lote):
        lote = distancias[i:i + tamano_lote]
        supabase.table('distancias').insert(lote).execute()
    
    print(f"Se importaron {len(distancias)} distancias a la base de datos")

def main():
    # Ruta al archivo Excel
    archivo_excel = r"c:\Users\acuri\dev\worksapce\python\IA\Deber\Ecuador_Distancias.xls"
    
    print(f"Procesando archivo: {archivo_excel}")
    
    # Cargar datos del Excel
    df = cargar_excel(archivo_excel)
    if df is None:
        print("Error: No se pudo cargar el archivo Excel.")
        return
    
    # Importar ciudades y obtener mapeo
    print("Importando ciudades...")
    mapeo_ciudades = importar_ciudades(df)
    
    # Importar distancias
    print("Importando distancias...")
    importar_distancias(df, mapeo_ciudades)
    
    print("Importación completada con éxito!")

if __name__ == "__main__":
    main()