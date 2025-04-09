import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from supabase import create_client
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_datos_bd():
    """Cargar los datos de ciudades y distancias desde la base de datos"""
    # Obtener ciudades
    ciudades_response = supabase.table('ciudades').select('id, nombre').execute()
    ciudades = ciudades_response.data
    
    # Obtener distancias
    distancias_response = supabase.table('distancias').select('origen_id, destino_id, distancia').execute()
    distancias = distancias_response.data
    
    print(f"Datos cargados: {len(ciudades)} ciudades y {len(distancias)} distancias")
    
    return ciudades, distancias

def crear_grafo(ciudades, distancias):
    """Crear un grafo a partir de los datos de la base de datos"""
    G = nx.Graph()
    
    # Diccionario para mapear IDs a nombres de ciudades
    id_a_nombre = {ciudad['id']: ciudad['nombre'] for ciudad in ciudades}
    
    # Agregar nodos (ciudades)
    for ciudad in ciudades:
        G.add_node(ciudad['nombre'])
    
    # Agregar aristas (distancias)
    for distancia in distancias:
        origen = id_a_nombre[distancia['origen_id']]
        destino = id_a_nombre[distancia['destino_id']]
        valor = distancia['distancia']
        
        G.add_edge(origen, destino, weight=valor)
    
    print(f"Grafo creado con {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas")
    return G, id_a_nombre

def visualizar_grafo(G, filename="grafo_ecuador_bd.png"):
    """Visualizar el grafo completo"""
    plt.figure(figsize=(16, 12))
    
    # Usar layout spring para una buena distribución
    pos = nx.spring_layout(G, seed=42, k=0.8)
    
    # Dibujar aristas
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.7, edge_color='gray')
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue')
    
    # Dibujar etiquetas
    nx.draw_networkx_labels(
        G, pos, 
        font_size=8, 
        font_weight='bold',
        bbox=dict(facecolor='white', alpha=0.7, pad=0.5)
    )
    
    plt.title('Grafo de Distancias entre Ciudades de Ecuador', fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Grafo guardado como {filename}")
    return filename

def busqueda_amplitud(G, origen, destino):
    """
    Implementa búsqueda en amplitud (BFS) para encontrar una ruta entre dos ciudades.
    Esta búsqueda encuentra la ruta con menor número de ciudades intermedias.
    """
    # Buscar ruta usando BFS
    try:
        # nx.shortest_path usa BFS cuando no hay weight
        ruta = nx.shortest_path(G, origen, destino)
        
        # Calcular distancia total sumando los tramos
        distancia_total = 0
        tramos = []
        for i in range(len(ruta)-1):
            origen_tramo = ruta[i]
            destino_tramo = ruta[i+1]
            distancia_tramo = G[origen_tramo][destino_tramo]['weight']
            distancia_total += distancia_tramo
            tramos.append((origen_tramo, destino_tramo, distancia_tramo))
        
        return {
            'ruta': ruta,
            'distancia_total': distancia_total,
            'tramos': tramos,
            'algoritmo': 'BFS'
        }
    except nx.NetworkXNoPath:
        return f"No existe una ruta entre {origen} y {destino}"

def busqueda_profundidad(G, origen, destino):
    """
    Implementa búsqueda en profundidad (DFS) para encontrar una ruta entre dos ciudades.
    """
    # Implementación manual de DFS ya que NetworkX no tiene una función directa
    def dfs_paths(graph, start, goal):
        stack = [(start, [start])]
        visited = set()
        
        while stack:
            vertex, path = stack.pop()
            if vertex not in visited:
                if vertex == goal:
                    return path
                visited.add(vertex)
                for neighbor in graph[vertex]:
                    stack.append((neighbor, path + [neighbor]))
        return None
    
    try:
        # Encontrar una ruta usando DFS
        ruta = dfs_paths(G, origen, destino)
        if not ruta:
            return f"No existe una ruta entre {origen} y {destino}"
        
        # Calcular distancia total sumando los tramos
        distancia_total = 0
        tramos = []
        for i in range(len(ruta)-1):
            origen_tramo = ruta[i]
            destino_tramo = ruta[i+1]
            distancia_tramo = G[origen_tramo][destino_tramo]['weight']
            distancia_total += distancia_tramo
            tramos.append((origen_tramo, destino_tramo, distancia_tramo))
        
        return {
            'ruta': ruta,
            'distancia_total': distancia_total,
            'tramos': tramos,
            'algoritmo': 'DFS'
        }
    except Exception as e:
        return f"Error en DFS: {e}"

def busqueda_costo_uniforme(G, origen, destino):
    """
    Implementa búsqueda de costo uniforme (Dijkstra) para encontrar la ruta
    más corta entre dos ciudades (optimizando la distancia total).
    """
    try:
        # Calcular la ruta más corta usando Dijkstra
        ruta = nx.dijkstra_path(G, origen, destino, weight='weight')
        distancia_total = nx.dijkstra_path_length(G, origen, destino, weight='weight')
        
        # Calcular tramos
        tramos = []
        for i in range(len(ruta)-1):
            origen_tramo = ruta[i]
            destino_tramo = ruta[i+1]
            distancia_tramo = G[origen_tramo][destino_tramo]['weight']
            tramos.append((origen_tramo, destino_tramo, distancia_tramo))
        
        return {
            'ruta': ruta,
            'distancia_total': distancia_total,
            'tramos': tramos,
            'algoritmo': 'Costo Uniforme (Dijkstra)'
        }
    except nx.NetworkXNoPath:
        return f"No existe una ruta entre {origen} y {destino}"

def encontrar_ruta_optima(G, origen, destino, id_a_nombre, nombre_a_id):
    """Encuentra la ruta más corta entre dos ciudades"""
    # Buscar ciudades que coincidan parcialmente con las entradas
    origen_match = None
    destino_match = None
    
    origen_lower = origen.lower()
    destino_lower = destino.lower()
    
    for ciudad in G.nodes():
        if origen_lower in ciudad.lower():
            origen_match = ciudad
            break
    
    for ciudad in G.nodes():
        if destino_lower in ciudad.lower():
            destino_match = ciudad
            break
    
    if not origen_match:
        return f"No se encontró la ciudad de origen '{origen}'"
    
    if not destino_match:
        return f"No se encontró la ciudad de destino '{destino}'"
    
    # Usar búsqueda de costo uniforme (Dijkstra)
    resultado = busqueda_costo_uniforme(G, origen_match, destino_match)
    
    if isinstance(resultado, dict):
        # Guardar resultado en la base de datos
        guardar_ruta_bd(origen_match, destino_match, resultado['distancia_total'], 
                        resultado['tramos'], nombre_a_id)
    
    return resultado

def guardar_ruta_bd(origen, destino, distancia_total, tramos, nombre_a_id):
    """Guarda la ruta calculada en la base de datos"""
    try:
        # Insertar en la tabla rutas_calculadas
        ruta_data = {
            'origen_id': nombre_a_id[origen],
            'destino_id': nombre_a_id[destino],
            'distancia_total': distancia_total
        }
        
        # Verificar si la ruta ya existe
        existe = supabase.table('rutas_calculadas')\
            .select('id')\
            .eq('origen_id', nombre_a_id[origen])\
            .eq('destino_id', nombre_a_id[destino])\
            .execute()
        
        if existe.data:
            # Actualizar ruta existente
            ruta_id = existe.data[0]['id']
            supabase.table('rutas_calculadas')\
                .update(ruta_data)\
                .eq('id', ruta_id)\
                .execute()
                
            # Eliminar tramos antiguos
            supabase.table('tramos_ruta')\
                .delete()\
                .eq('ruta_id', ruta_id)\
                .execute()
        else:
            # Insertar nueva ruta
            resultado = supabase.table('rutas_calculadas')\
                .insert(ruta_data)\
                .execute()
            ruta_id = resultado.data[0]['id']
        
        # Insertar tramos
        for i, (origen_tramo, destino_tramo, distancia) in enumerate(tramos):
            tramo_data = {
                'ruta_id': ruta_id,
                'origen_id': nombre_a_id[origen_tramo],
                'destino_id': nombre_a_id[destino_tramo],
                'distancia': distancia,
                'orden': i + 1
            }
            supabase.table('tramos_ruta').insert(tramo_data).execute()
        
        print(f"Ruta de {origen} a {destino} guardada en la base de datos con ID {ruta_id}")
    except Exception as e:
        print(f"Error al guardar la ruta en la base de datos: {e}")

def visualizar_ruta(G, resultado_ruta, filename="ruta_optima_bd.png"):
    """Visualiza la ruta entre dos ciudades"""
    if isinstance(resultado_ruta, str):
        print(resultado_ruta)
        return None
    
    ruta = resultado_ruta['ruta']
    distancia_total = resultado_ruta['distancia_total']
    algoritmo = resultado_ruta.get('algoritmo', 'No especificado')
    
    aristas_ruta = [(ruta[i], ruta[i+1]) for i in range(len(ruta)-1)]
    
    plt.figure(figsize=(16, 12))
    
    # Posición de los nodos
    pos = nx.spring_layout(G, seed=42, k=0.8)
    
    # Dibujar grafo completo en gris claro (fondo)
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5, edge_color='lightgray')
    nx.draw_networkx_nodes(G, pos, node_size=300, node_color='lightgray', alpha=0.3)
    
    # Resaltar las aristas de la ruta
    nx.draw_networkx_edges(
        G, pos, 
        edgelist=aristas_ruta, 
        width=3, 
        edge_color='red',
        arrows=True,
        arrowstyle='-|>'
    )
    
    # Resaltar nodos de la ruta
    nx.draw_networkx_nodes(
        G, pos, 
        nodelist=ruta, 
        node_size=600, 
        node_color='lightcoral'
    )
    
    # Destacar origen y destino
    nx.draw_networkx_nodes(
        G, pos, 
        nodelist=[ruta[0], ruta[-1]], 
        node_size=700, 
        node_color='gold',
        edgecolors='darkorange',
        linewidths=2
    )
    
    # Etiquetas de nodos en la ruta
    label_dict = {node: node for node in ruta}
    nx.draw_networkx_labels(
        G, pos, 
        labels=label_dict,
        font_size=9, 
        font_weight='bold',
        bbox=dict(facecolor='white', alpha=0.8, pad=0.5)
    )
    
    # Etiquetas de aristas con distancias
    edge_labels = {(u, v): f"{G[u][v]['weight']:.0f} km" for u, v in aristas_ruta}
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=edge_labels, 
        font_size=8,
        font_weight='bold'
    )
    
    # Título e información
    plt.title(f"Ruta {algoritmo}: {ruta[0]} → {ruta[-1]}", fontsize=16, fontweight='bold')
    plt.figtext(0.5, 0.01, f"Distancia total: {distancia_total:.1f} km\nRuta: {' → '.join(ruta)}", 
               ha='center', fontsize=12, bbox=dict(facecolor='lightyellow', alpha=0.9, pad=0.5))
    
    plt.axis('off')
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Ruta guardada como {filename}")
    return filename

def mostrar_resultado(resultado):
    """Muestra los resultados de búsqueda de manera uniforme"""
    if isinstance(resultado, dict):
        print(f"✅ Ruta encontrada usando {resultado['algoritmo']}")
        print(f"   Ciudades: {' → '.join(resultado['ruta'])}")
        print(f"   Número de ciudades: {len(resultado['ruta'])}")
        print(f"   Distancia total: {resultado['distancia_total']:.1f} km")
        
        print("   Tramos de la ruta:")
        for origen_tramo, destino_tramo, distancia_tramo in resultado['tramos']:
            print(f"     • {origen_tramo} → {destino_tramo}: {distancia_tramo:.1f} km")
    else:
        print(f"❌ Error: {resultado}")

def main():
    print("Cargando datos desde la base de datos...")
    ciudades, distancias = cargar_datos_bd()
    
    # Crear grafo
    print("Creando grafo de distancias...")
    G, id_a_nombre = crear_grafo(ciudades, distancias)
    
    # Crear mapeo inverso de nombres a IDs
    nombre_a_id = {v: k for k, v in id_a_nombre.items()}
    
    # Visualizar el grafo completo
    visualizar_grafo(G)
    
    # Calcular y visualizar algunas rutas de ejemplo
    rutas_ejemplo = [
        ("Quito", "Guayaquil"),
        ("Cuenca", "Loja"),
        ("Ambato", "Esmeraldas")
    ]
    
    for origen, destino in rutas_ejemplo:
        print(f"\n{'='*50}")
        print(f"COMPARACIÓN DE ALGORITMOS: {origen} a {destino}")
        print(f"{'='*50}")
        
        # Buscar coincidencias con los nombres de ciudad
        origen_match = None
        destino_match = None
        
        origen_lower = origen.lower()
        destino_lower = destino.lower()
        
        for ciudad in G.nodes():
            if origen_lower in ciudad.lower():
                origen_match = ciudad
                break
        
        for ciudad in G.nodes():
            if destino_lower in ciudad.lower():
                destino_match = ciudad
                break
        
        if not origen_match or not destino_match:
            print(f"Error: No se encontró alguna de las ciudades: {origen} o {destino}")
            continue
        
        # Ejecutar todos los algoritmos de búsqueda
        print(f"\n1. BÚSQUEDA EN AMPLITUD (BFS)")
        print(f"Buscando ruta con menor número de ciudades intermedias...")
        bfs_resultado = busqueda_amplitud(G, origen_match, destino_match)
        mostrar_resultado(bfs_resultado)
        if isinstance(bfs_resultado, dict):
            visualizar_ruta(G, bfs_resultado, 
                          filename=f"ruta_BFS_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png")
        
        print(f"\n2. BÚSQUEDA EN PROFUNDIDAD (DFS)")
        print(f"Buscando una ruta usando exploración en profundidad...")
        dfs_resultado = busqueda_profundidad(G, origen_match, destino_match)
        mostrar_resultado(dfs_resultado)
        if isinstance(dfs_resultado, dict):
            visualizar_ruta(G, dfs_resultado, 
                          filename=f"ruta_DFS_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png")
        
        print(f"\n3. BÚSQUEDA DE COSTO UNIFORME (DIJKSTRA)")
        print(f"Buscando ruta de menor distancia total...")
        ucs_resultado = busqueda_costo_uniforme(G, origen_match, destino_match)
        mostrar_resultado(ucs_resultado)
        if isinstance(ucs_resultado, dict):
            visualizar_ruta(G, ucs_resultado, 
                          filename=f"ruta_UCS_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png")
            
            # Guardar la ruta óptima (costo uniforme) en la base de datos
            guardar_ruta_bd(origen_match, destino_match, ucs_resultado['distancia_total'], 
                           ucs_resultado['tramos'], nombre_a_id)
    
    print("\n¡Análisis completado con éxito!")

if __name__ == "__main__":
    main()