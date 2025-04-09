import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Definir las conexiones reales entre ciudades ecuatorianas
# Formato: (ciudad1, ciudad2, distancia_km)
CONEXIONES_REALES = [
    # Región Sierra Norte
    ("Quito", "Aloag", 25),
    ("Quito", "Latacunga", 89),
    ("Quito", "Otavalo", 110),
    ("Quito", "Ibarra", 126),
    ("Ibarra", "Otavalo", 26),
    ("Ibarra", "Tulcán", 127),
    ("Tulcán", "Rumichaca", 10),  # Frontera con Colombia
    
    # Región Sierra Centro
    ("Latacunga", "Ambato", 43),
    ("Ambato", "Riobamba", 54),
    ("Ambato", "Baños", 41),
    ("Riobamba", "Guaranda", 65),
    
    # Región Sierra Sur
    ("Riobamba", "Azogues", 145),
    ("Azogues", "Cuenca", 37),
    ("Cuenca", "Loja", 205),
    ("Loja", "Zamora", 65),
    ("Loja", "Macara", 195),  # Frontera con Perú
    
    # Región Costa Norte
    ("Quito", "Sto. Domingo", 133),
    ("Sto. Domingo", "Esmeraldas", 177),
    ("Esmeraldas", "San Lorenzo", 139),
    ("Esmeraldas", "Muisne", 91),
    ("Sto. Domingo", "Quininde", 113),
    ("Quininde", "Esmeraldas", 99),
    
    # Región Costa Centro
    ("Sto. Domingo", "Quevedo", 140),
    ("Quevedo", "Babahoyo", 116),
    ("Babahoyo", "Guayaquil", 88),
    ("Aloag", "Sto. Domingo", 108),
    ("Sto. Domingo", "Portoviejo", 159),
    ("Portoviejo", "Manta", 44),
    ("Portoviejo", "Bahía de Caraquez", 85),
    ("Manta", "Bahía de Caraquez", 88),
    
    # Región Costa Sur
    ("Guayaquil", "Salinas", 140),
    ("Guayaquil", "Machala", 195),
    ("Machala", "Huaquillas", 73),  # Frontera con Perú
    
    # Conexiones Sierra-Oriente
    ("Baños", "Puyo", 61),
    ("Quito", "Baeza", 105),
    ("Baeza", "Tena", 110),
    ("Latacunga", "Tena", 145),
    
    # Región Oriente
    ("Tena", "Puyo", 77),
    ("Tena", "Pto. Fco. De Orellana", 140),  # Puerto Francisco de Orellana (Coca)
    ("Puyo", "Macas", 133),
    ("Macas", "Zamora", 210),
    ("Macas", "Pto. Morona", 90),  # Puerto en la frontera con Perú
    
    # Conexiones Norte Amazónico
    ("Baeza", "Nueva Loja", 134),
    ("Nueva Loja", "Pte. San Miguel", 42),  # Frontera con Colombia
    ("Nueva Loja", "Pto. Putumayo", 200),  # Puerto en la frontera con Colombia/Perú
    
    # Conexiones adicionales
    ("Guaranda", "Babahoyo", 125),
    ("Cuenca", "Machala", 164),
    ("Guayaquil", "Cuenca", 198),
    ("Pedernales", "Bahía de Caraquez", 114),
    ("Pedernales", "Muisne", 134)
]

def migrar_tabla_distancias():
    """
    Vaciar la tabla de distancias y llenarla solo con las conexiones reales.
    """
    print("Iniciando migración de la tabla de distancias...")
    
    # 1. Obtener todas las ciudades
    print("Obteniendo lista de ciudades...")
    respuesta_ciudades = supabase.table('ciudades').select('id, nombre').execute()
    ciudades = respuesta_ciudades.data
    
    if not ciudades:
        print("Error: No hay ciudades en la base de datos.")
        return False
    
    # Crear diccionario para mapear nombres a IDs
    nombre_a_id = {ciudad['nombre']: ciudad['id'] for ciudad in ciudades}
    
    # 2. Vaciar la tabla de distancias
    print("Vaciando la tabla de distancias...")
    try:
        # Para eliminar todos los registros en PostgreSQL/Supabase, necesitamos usar un truco
        # porque DELETE requiere una cláusula WHERE
        supabase.table('distancias').delete().neq('id', 0).execute()
        print("Tabla de distancias vaciada correctamente.")
    except Exception as e:
        print(f"Error al vaciar la tabla: {e}")
        print("Intentando un enfoque alternativo...")
        try:
            # Enfoque alternativo: obtener todos los IDs y eliminarlos uno por uno
            todos_ids = supabase.table('distancias').select('id').execute()
            if todos_ids.data:
                for registro in todos_ids.data:
                    supabase.table('distancias').delete().eq('id', registro['id']).execute()
            print("Tabla de distancias vaciada correctamente.")
        except Exception as e2:
            print(f"Error al usar el enfoque alternativo: {e2}")
            return False
    
    # 3. Insertar las conexiones reales
    print("Insertando conexiones reales...")
    conexiones_creadas = 0
    conexiones_no_creadas = []
    
    for ciudad1, ciudad2, distancia in CONEXIONES_REALES:
        # Verificar que ambas ciudades existen
        if ciudad1 not in nombre_a_id:
            print(f"Advertencia: Ciudad '{ciudad1}' no existe en la base de datos.")
            conexiones_no_creadas.append((ciudad1, ciudad2, distancia))
            continue
            
        if ciudad2 not in nombre_a_id:
            print(f"Advertencia: Ciudad '{ciudad2}' no existe en la base de datos.")
            conexiones_no_creadas.append((ciudad1, ciudad2, distancia))
            continue
        
        # Crear registro de distancia bidireccional (en ambas direcciones)
        try:
            # Dirección 1: ciudad1 -> ciudad2
            supabase.table('distancias').insert({
                'origen_id': nombre_a_id[ciudad1],
                'destino_id': nombre_a_id[ciudad2],
                'distancia': distancia
            }).execute()
            
            # Dirección 2: ciudad2 -> ciudad1
            supabase.table('distancias').insert({
                'origen_id': nombre_a_id[ciudad2],
                'destino_id': nombre_a_id[ciudad1],
                'distancia': distancia
            }).execute()
            
            conexiones_creadas += 1
            print(f"Conexión creada: {ciudad1} - {ciudad2} ({distancia} km)")
            
        except Exception as e:
            print(f"Error al crear conexión {ciudad1} - {ciudad2}: {e}")
            conexiones_no_creadas.append((ciudad1, ciudad2, distancia))
    
    print(f"\nMigración completada. {conexiones_creadas} conexiones creadas de {len(CONEXIONES_REALES)}")
    
    if conexiones_no_creadas:
        print(f"Advertencia: {len(conexiones_no_creadas)} conexiones no se pudieron crear:")
        for c1, c2, d in conexiones_no_creadas:
            print(f"  - {c1} - {c2} ({d} km)")
    
    return True

def verificar_con_usuario():
    """Verificar con el usuario antes de vaciar la tabla"""
    print("\n¡ATENCIÓN! Este script va a ELIMINAR TODOS LOS DATOS de la tabla 'distancias'.")
    print("La tabla se rellenará con solo las conexiones reales entre ciudades.")
    print("Este proceso no se puede deshacer.")
    
    respuesta = input("\n¿Está seguro que desea continuar? (s/n): ")
    return respuesta.lower() == 's'

# Función principal
if __name__ == "__main__":
    print("=== MIGRACIÓN DE TABLA DE DISTANCIAS ===")
    
    if verificar_con_usuario():
        if migrar_tabla_distancias():
            print("\nMigración completada con éxito.")
        else:
            print("\nOcurrió un error durante la migración.")
    else:
        print("\nOperación cancelada por el usuario.")
        