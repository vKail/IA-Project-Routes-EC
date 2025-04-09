import os
from dotenv import load_dotenv
from supabase import create_client
import numpy as np
from geopy.distance import geodesic

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class CiudadesCRUD:
    """Clase para gestionar operaciones CRUD de ciudades"""
    
    @staticmethod
    def listar_ciudades():
        """Obtener todas las ciudades de la base de datos"""
        try:
            response = supabase.table('ciudades').select('*').order('nombre').execute()
            return response.data
        except Exception as e:
            print(f"Error al listar ciudades: {e}")
            return []
    
    @staticmethod
    def obtener_ciudad(ciudad_id):
        """Obtener una ciudad por su ID"""
        try:
            response = supabase.table('ciudades').select('*').eq('id', ciudad_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error al obtener ciudad: {e}")
            return None
    
    @staticmethod
    def buscar_ciudad(nombre):
        """Buscar ciudades por nombre (búsqueda parcial)"""
        try:
            # Usar el operador ILIKE para búsqueda insensible a mayúsculas/minúsculas y parcial
            response = supabase.table('ciudades').select('*').ilike('nombre', f'%{nombre}%').execute()
            return response.data
        except Exception as e:
            print(f"Error al buscar ciudad: {e}")
            return []
    
    @staticmethod
    def crear_ciudad(nombre, latitud, longitud, conexiones=None, indice_original=None):
        """
        Crear una nueva ciudad con sus conexiones
        
        Args:
            nombre: Nombre de la ciudad
            latitud: Latitud de la ciudad
            longitud: Longitud de la ciudad
            conexiones: Lista de diccionarios con conexiones a otras ciudades
                        [{'ciudad_id': id, 'distancia': km}, ...]
            indice_original: Índice original en el Excel
        """
        try:
            # Validar datos
            if not nombre or nombre.strip() == "":
                return {"error": "El nombre de la ciudad es obligatorio"}
            
            if latitud is None or longitud is None:
                return {"error": "Latitud y longitud son obligatorios"}
            
            # Verificar si ya existe una ciudad con el mismo nombre
            existing = supabase.table('ciudades').select('id').eq('nombre', nombre).execute()
            if existing.data:
                return {"error": f"Ya existe una ciudad con el nombre '{nombre}'"}
            
            # Asignar nuevo índice si no se proporciona
            if indice_original is None:
                # Obtener el máximo índice actual
                indices = supabase.table('ciudades').select('indice_original').execute()
                if indices.data:
                    max_indice = max([c['indice_original'] for c in indices.data if c['indice_original'] is not None])
                    indice_original = max_indice + 1
                else:
                    indice_original = 1
            
            # Crear la nueva ciudad
            nueva_ciudad = {
                'nombre': nombre,
                'latitud': latitud,
                'longitud': longitud,
                'indice_original': indice_original
            }
            
            response = supabase.table('ciudades').insert(nueva_ciudad).execute()
            
            if not response.data:
                return {"error": "No se pudo crear la ciudad"}
            
            ciudad_creada = response.data[0]
            
            # Crear conexiones si se proporcionaron
            if conexiones and isinstance(conexiones, list):
                for conexion in conexiones:
                    ciudad2_id = conexion['ciudad_id']
                    distancia = conexion['distancia']
                    
                    # Validar que la ciudad destino existe
                    ciudad_destino = CiudadesCRUD.obtener_ciudad(ciudad2_id)
                    if not ciudad_destino:
                        print(f"Advertencia: Ciudad destino ID {ciudad2_id} no existe")
                        continue
                    
                    # Crear distancia bidireccional (ambas direcciones)
                    supabase.table('distancias').insert({
                        'origen_id': ciudad_creada['id'],
                        'destino_id': ciudad2_id,
                        'distancia': distancia
                    }).execute()
                    
                    supabase.table('distancias').insert({
                        'origen_id': ciudad2_id,
                        'destino_id': ciudad_creada['id'],
                        'distancia': distancia
                    }).execute()
            
            return ciudad_creada
        
        except Exception as e:
            print(f"Error al crear ciudad: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def actualizar_ciudad(ciudad_id, nombre=None, latitud=None, longitud=None):
        """Actualizar una ciudad existente"""
        try:
            # Verificar que la ciudad existe
            ciudad = CiudadesCRUD.obtener_ciudad(ciudad_id)
            if not ciudad:
                return {"error": "Ciudad no encontrada"}
            
            # Preparar datos a actualizar
            datos_actualizados = {}
            
            if nombre is not None and nombre.strip() != "":
                datos_actualizados['nombre'] = nombre
            
            if latitud is not None:
                datos_actualizados['latitud'] = latitud
            
            if longitud is not None:
                datos_actualizados['longitud'] = longitud
            
            # Actualizar la ciudad
            response = supabase.table('ciudades').update(datos_actualizados).eq('id', ciudad_id).execute()
            
            if response.data:
                return response.data[0]
            
            return {"error": "No se pudo actualizar la ciudad"}
        
        except Exception as e:
            print(f"Error al actualizar ciudad: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def eliminar_ciudad(ciudad_id):
        """Eliminar una ciudad y sus distancias asociadas"""
        try:
            # Verificar que la ciudad existe
            ciudad = CiudadesCRUD.obtener_ciudad(ciudad_id)
            if not ciudad:
                return {"error": "Ciudad no encontrada"}
            
            # Eliminar distancias relacionadas con esta ciudad
            supabase.table('distancias').delete().eq('origen_id', ciudad_id).execute()
            supabase.table('distancias').delete().eq('destino_id', ciudad_id).execute()
            
            # Eliminar rutas relacionadas
            # Primero obtenemos IDs de rutas que involucran esta ciudad
            rutas_response = supabase.table('rutas_calculadas').select('id').filter("origen_id", "eq", ciudad_id).filter("destino_id", "eq", ciudad_id).execute()
            if rutas_response.data:
                rutas_ids = [ruta['id'] for ruta in rutas_response.data]
                
                # Eliminar tramos de esas rutas
                for ruta_id in rutas_ids:
                    supabase.table('tramos_ruta').delete().eq('ruta_id', ruta_id).execute()
                
                # Eliminar las rutas
                for ruta_id in rutas_ids:
                    supabase.table('rutas_calculadas').delete().eq('id', ruta_id).execute()
            
            # Eliminar la ciudad
            response = supabase.table('ciudades').delete().eq('id', ciudad_id).execute()
            
            if response.data:
                return {"mensaje": f"Ciudad '{ciudad['nombre']}' eliminada correctamente"}
            
            return {"error": "No se pudo eliminar la ciudad"}
        
        except Exception as e:
            print(f"Error al eliminar ciudad: {e}")
            return {"error": str(e)}