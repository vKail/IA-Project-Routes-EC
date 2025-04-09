import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Coordenadas geográficas de las ciudades ecuatorianas
# Formato: nombre_ciudad: (latitud, longitud)
# Coordenadas en formato decimal (grados)
COORDENADAS_CIUDADES = {
    "Ambato": (-1.2426, -78.6283),
    "Azogues": (-2.7408, -78.8453),
    "Babahoyo": (-1.8016, -79.5347),
    "Cuenca": (-2.9001, -79.0059),
    "Esmeraldas": (0.9595, -79.6539),
    "Guaranda": (-1.5923, -79.0006),
    "Guayaquil": (-2.1962, -79.8862),
    "Ibarra": (0.3507, -78.1223),
    "Latacunga": (-0.9354, -78.6124),
    "Loja": (-3.9931, -79.2042),
    "Macas": (-2.3093, -78.1188),
    "Machala": (-3.2562, -79.9597),
    "Nueva Loja": (0.0875, -76.8915),
    "Portoviejo": (-1.0543, -80.4544),
    "Pto. Fco. De Orellana": (-0.4669, -76.9866),  # Puerto Francisco de Orellana (Coca)
    "Puyo": (-1.4874, -77.9969),
    "Quito": (-0.1807, -78.4678),
    "Riobamba": (-1.6740, -78.6483),
    "Tena": (-0.9945, -77.8134),
    "Tulcán": (0.8111, -77.7173),
    "Zamora": (-4.0661, -78.9554),
    "Aloag": (-0.4577, -78.5814),
    "Sto. Domingo": (-0.2541, -79.1715),  # Santo Domingo de los Tsáchilas
    "Baños": (-1.3928, -78.4269),  # Baños de Agua Santa
    "Bahía de Caraquez": (-0.6021, -80.4231),
    "Baeza": (-0.4663, -77.8910),
    "Rumichaca": (0.8200, -77.6700),  # Puente Rumichaca (frontera con Colombia)
    "Macara": (-4.3773, -79.9436),
    "Huaquillas": (-3.4775, -80.2306),
    "Manta": (-0.9676, -80.7089),
    "Otavalo": (0.2341, -78.2628),
    "Salinas": (-2.2167, -80.9686),
    "San Lorenzo": (1.2867, -78.8358),
    "Quevedo": (-1.0285, -79.4642),
    "Quininde": (0.3151, -79.4821),
    "Pte. San Miguel": (0.1960, -76.8812),  # Puente San Miguel
    "Pto. Putumayo": (-0.0018, -75.5154),  # Puerto Putumayo
    "Pto. Morona": (-2.9000, -77.7300),  # Puerto Morona
    "Muisne": (0.6159, -80.0264),
    "Pedernales": (0.0739, -80.0522)
}

def actualizar_coordenadas():
    """Actualiza las coordenadas de las ciudades en la base de datos"""
    print("Iniciando actualización de coordenadas...")
    
    # Obtener todas las ciudades de la base de datos
    respuesta = supabase.table('ciudades').select('id, nombre').execute()
    ciudades = respuesta.data
    
    contador_actualizaciones = 0
    ciudades_no_encontradas = []
    
    # Actualizar cada ciudad
    for ciudad in ciudades:
        nombre_ciudad = ciudad['nombre']
        
        # Buscar las coordenadas para esta ciudad
        if nombre_ciudad in COORDENADAS_CIUDADES:
            latitud, longitud = COORDENADAS_CIUDADES[nombre_ciudad]
            
            # Actualizar la base de datos
            supabase.table('ciudades').update({
                'latitud': latitud,
                'longitud': longitud
            }).eq('id', ciudad['id']).execute()
            
            contador_actualizaciones += 1
            print(f"Actualizada: {nombre_ciudad} ({latitud}, {longitud})")
        else:
            ciudades_no_encontradas.append(nombre_ciudad)
    
    print(f"\nActualización completada. {contador_actualizaciones} ciudades actualizadas.")
    
    if ciudades_no_encontradas:
        print(f"Advertencia: No se encontraron coordenadas para {len(ciudades_no_encontradas)} ciudades:")
        for ciudad in ciudades_no_encontradas:
            print(f"  - {ciudad}")

if __name__ == "__main__":
    actualizar_coordenadas()