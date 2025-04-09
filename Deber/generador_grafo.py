import networkx as nx
import os
import numpy as np
from dotenv import load_dotenv
from supabase import create_client
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# Cargar variables de entorno
load_dotenv()

# Configurar conexión a Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class GeneradorGrafo:
    """Clase para generar y manipular el grafo de ciudades y distancias"""
    
    @staticmethod
    def cargar_datos_bd():
        """Cargar los datos de ciudades y distancias desde la base de datos"""
        try:
            # Obtener ciudades con coordenadas
            ciudades_response = supabase.table('ciudades').select('id, nombre, latitud, longitud').execute()
            ciudades = ciudades_response.data
            
            # Obtener distancias
            distancias_response = supabase.table('distancias').select('origen_id, destino_id, distancia').execute()
            distancias = distancias_response.data
            
            print(f"Datos cargados: {len(ciudades)} ciudades y {len(distancias)} distancias")
            
            return ciudades, distancias
        except Exception as e:
            print(f"Error al cargar datos: {e}")
            return [], []
    
    @staticmethod
    def crear_grafo():
        """
        Crear un grafo NetworkX a partir de las distancias reales entre ciudades
        """
        ciudades, distancias = GeneradorGrafo.cargar_datos_bd()
        
        if not ciudades or not distancias:
            print("No se pudieron cargar los datos para crear el grafo")
            return None, None, None
        
        G = nx.Graph()
        
        # Diccionarios para mapeo
        id_a_nombre = {ciudad['id']: ciudad['nombre'] for ciudad in ciudades}
        nombre_a_id = {ciudad['nombre']: ciudad['id'] for ciudad in ciudades}
        
        # Diccionario para guardar coordenadas
        coords = {}
        
        # Agregar nodos (ciudades) con atributos
        for ciudad in ciudades:
            nombre = ciudad['nombre']
            G.add_node(nombre, id=ciudad['id'])
            
            # Guardar coordenadas si están disponibles
            if 'latitud' in ciudad and 'longitud' in ciudad and ciudad['latitud'] is not None and ciudad['longitud'] is not None:
                coords[nombre] = (ciudad['latitud'], ciudad['longitud'])
        
        # Agregar aristas usando las distancias reales
        print("Agregando conexiones entre ciudades...")
        
        conexiones_agregadas = set()  # Para evitar duplicados
        
        for distancia in distancias:
            origen_id = distancia['origen_id']
            destino_id = distancia['destino_id']
            
            # Verificar que ambas ciudades existen
            if origen_id in id_a_nombre and destino_id in id_a_nombre:
                origen_nombre = id_a_nombre[origen_id]
                destino_nombre = id_a_nombre[destino_id]
                
                # Evitar agregar la misma conexión dos veces (ya que tenemos registros bidireccionales)
                # Ordenamos los nombres para crear una clave consistente
                clave = tuple(sorted([origen_nombre, destino_nombre]))
                
                if clave not in conexiones_agregadas:
                    # Agregar arista al grafo
                    G.add_edge(origen_nombre, destino_nombre, weight=distancia['distancia'])
                    conexiones_agregadas.add(clave)
                    print(f"  Conexión: {origen_nombre} - {destino_nombre} ({distancia['distancia']:.1f} km)")
        
        print(f"Grafo creado con {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas")
        
        # Comprobar que el grafo esté conectado
        if not nx.is_connected(G):
            print("¡ADVERTENCIA! El grafo no está completamente conectado.")
            componentes = list(nx.connected_components(G))
            print(f"  Hay {len(componentes)} componentes conexas.")
            for i, comp in enumerate(componentes):
                print(f"  Componente {i+1} tiene {len(comp)} ciudades: {', '.join(comp)}")
        
        return G, coords, nombre_a_id
    
    @staticmethod
    def visualizar_grafo(G, coords=None, filename="grafo_ecuador.png"):
        """Visualizar el grafo completo"""
        plt.figure(figsize=(16, 12))
        
        # Usar un layout adecuado
        if coords:
            # Si tenemos coordenadas geográficas, usarlas para el layout
            # Usamos coordenadas negativas en X para longitud porque Ecuador está en el hemisferio occidental
            pos = {node: (-coords[node][1], coords[node][0]) for node in G.nodes() if node in coords}
            
            # Para nodos sin coordenadas, usar spring layout
            nodes_sin_coords = [node for node in G.nodes() if node not in coords]
            if nodes_sin_coords:
                pos_restantes = nx.spring_layout(G.subgraph(nodes_sin_coords), seed=42)
                pos.update(pos_restantes)
        else:
            # Si no hay coordenadas, usar spring layout para todos
            pos = nx.spring_layout(G, seed=42, k=0.8)
        
        # Dibujar aristas con grosor basado en distancia
        for u, v, data in G.edges(data=True):
            # Grosor inversamente proporcional a la distancia (más delgado para distancias mayores)
            width = max(0.5, 5 * (1 / (data['weight'] / 50)))
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=width, alpha=0.6, edge_color='royalblue')
        
        # Dibujar nodos
        nx.draw_networkx_nodes(G, pos, node_size=200, node_color='lightblue', 
                              edgecolors='darkblue', linewidths=1.5)
        
        # Dibujar etiquetas
        nx.draw_networkx_labels(
            G, pos, 
            font_size=9, 
            font_weight='bold',
            bbox=dict(facecolor='white', alpha=0.8, pad=0.5)
        )
        
        plt.title('Red de Carreteras entre Ciudades de Ecuador', fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Grafo guardado como {filename}")
        return filename
    
    @staticmethod
    def visualizar_ruta(G, resultado_ruta, coords=None, filename="ruta_optima.png"):
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
        if coords:
            # Si tenemos coordenadas geográficas, usarlas para el layout
            pos = {node: (-coords[node][1], coords[node][0]) for node in G.nodes() if node in coords}
            
            # Para nodos sin coordenadas, usar spring layout
            nodes_sin_coords = [node for node in G.nodes() if node not in coords]
            if nodes_sin_coords:
                pos_restantes = nx.spring_layout(G.subgraph(nodes_sin_coords), seed=42)
                pos.update(pos_restantes)
        else:
            # Si no hay coordenadas, usar spring layout para todos
            pos = nx.spring_layout(G, seed=42, k=0.8)
        
        # Dibujar grafo completo en gris claro (fondo)
        for u, v, data in G.edges(data=True):
            # No dibujar las aristas que son parte de la ruta (se dibujarán después)
            if (u, v) not in aristas_ruta and (v, u) not in aristas_ruta:
                width = max(0.2, 2 * (1 / (data['weight'] / 50)))
                nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=width, 
                                      alpha=0.15, edge_color='gray')
        
        # Dibujar nodos del grafo (fondo)
        nx.draw_networkx_nodes(G, pos, node_size=120, node_color='lightgray', alpha=0.3)
        
        # Resaltar las aristas de la ruta
        for i, (u, v) in enumerate(aristas_ruta):
            nx.draw_networkx_edges(
                G, pos, 
                edgelist=[(u, v)], 
                width=4, 
                edge_color='red',
                arrows=True,
                arrowsize=20,
                arrowstyle='-|>'
            )
        
        # Resaltar nodos de la ruta
        nx.draw_networkx_nodes(
            G, pos, 
            nodelist=ruta, 
            node_size=300, 
            node_color='lightcoral'
        )
        
        # Destacar origen y destino
        nx.draw_networkx_nodes(
            G, pos, 
            nodelist=[ruta[0], ruta[-1]], 
            node_size=500, 
            node_color='gold',
            edgecolors='darkorange',
            linewidths=2
        )
        
        # Etiquetas de nodos en la ruta
        label_dict = {node: node for node in ruta}
        nx.draw_networkx_labels(
            G, pos, 
            labels=label_dict,
            font_size=10, 
            font_weight='bold',
            bbox=dict(facecolor='white', alpha=0.8, pad=0.5)
        )
        
        # Etiquetas de aristas con distancias
        edge_labels = {(u, v): f"{G[u][v]['weight']:.0f} km" for u, v in aristas_ruta}
        nx.draw_networkx_edge_labels(
            G, pos, 
            edge_labels=edge_labels, 
            font_size=9,
            font_weight='bold',
            bbox=dict(facecolor='white', alpha=0.7, pad=0.2)
        )
        
        # Título e información
        plt.title(f"Ruta {algoritmo}: {ruta[0]} → {ruta[-1]}", fontsize=16, fontweight='bold')
        plt.figtext(0.5, 0.01, f"Distancia total: {distancia_total:.1f} km\nRuta: {' → '.join(ruta)}", 
                   ha='center', fontsize=11, bbox=dict(facecolor='lightyellow', alpha=0.9, pad=0.5))
        
        plt.axis('off')
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Ruta guardada como {filename}")
        return filename