import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def cargar_datos_excel(archivo_excel):
    """Carga datos del archivo Excel de distancias"""
    try:
        # Cargar saltando la primera fila (título)
        try:
            df = pd.read_excel(archivo_excel, skiprows=1, engine='openpyxl')
        except:
            df = pd.read_excel(archivo_excel, skiprows=1, engine='xlrd')
            
        # Renombrar las columnas con los nombres correctos
        df.rename(columns={df.columns[0]: 'No.', df.columns[1]: 'CIUDAD'}, inplace=True)
        
        # Verificar la estructura
        print(f"Columnas del DataFrame (renombradas): {df.columns.tolist()[:5]}...")
        print(f"Forma del DataFrame: {df.shape}")
        
        return df
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return None

def crear_matriz_distancias(df):
    """
    Crea una matriz de distancias correcta a partir del DataFrame
    """
    # Los nombres de las ciudades están en la columna 'CIUDAD'
    ciudades = []
    indices_ciudades = {}
    
    for i, row in df.iterrows():
        # Saltamos la fila de encabezados (i==0)
        if i > 0 and pd.notna(row['No.']) and pd.notna(row['CIUDAD']):
            ciudad = row['CIUDAD']
            indice = int(row['No.'])
            ciudades.append(ciudad)
            indices_ciudades[indice] = ciudad
    
    print(f"Ciudades encontradas: {len(ciudades)}")
    print(f"Primeras 5 ciudades: {ciudades[:5]}")
    
    # Crear matriz de adyacencia con nombres de ciudades
    matriz_distancias = {}
    for i, ciudad_origen in enumerate(ciudades):
        matriz_distancias[ciudad_origen] = {}
        
        # Fila correspondiente a esta ciudad
        fila = df.iloc[i+1]  # +1 para saltar encabezados
        
        # Para cada destino, tomamos el valor de la columna correspondiente
        for j, ciudad_destino in enumerate(ciudades):
            # Índice numérico del destino (columnas 2 en adelante son distancias)
            indice_destino = j + 3  # +3 porque empezamos desde la columna 3 (índice 2)
            
            if indice_destino < len(fila):
                distancia = fila.iloc[indice_destino - 1]  # -1 para ajustar al índice correcto
                
                if pd.notna(distancia) and distancia > 0:
                    matriz_distancias[ciudad_origen][ciudad_destino] = float(distancia)
    
    return matriz_distancias, ciudades

def crear_grafo(matriz_distancias):
    """Crea un grafo a partir de la matriz de distancias"""
    G = nx.Graph()
    
    # Agregar nodos
    for ciudad in matriz_distancias.keys():
        G.add_node(ciudad)
    
    # Agregar aristas con pesos
    for origen, destinos in matriz_distancias.items():
        for destino, distancia in destinos.items():
            if origen != destino and distancia > 0:
                G.add_edge(origen, destino, weight=distancia)
    
    return G

def visualizar_grafo(G, filename="grafo_ecuador.png"):
    """Visualiza el grafo completo"""
    plt.figure(figsize=(16, 12))
    
    # Usar un layout que separe bien los nodos
    pos = nx.spring_layout(G, seed=42, k=0.8)
    
    # Dibujar aristas
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.7, edge_color='gray')
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue')
    
    # Dibujar etiquetas de nodos
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

def encontrar_ruta_optima(G, origen, destino):
    """
    Encuentra la ruta más corta entre dos ciudades.
    Retorna la ruta y la distancia total.
    """
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
    
    try:
        # Calcular la ruta más corta usando el algoritmo de Dijkstra
        ruta = nx.dijkstra_path(G, origen_match, destino_match, weight='weight')
        distancia_total = nx.dijkstra_path_length(G, origen_match, destino_match, weight='weight')
        
        # Calcular distancias por tramos
        tramos = []
        for i in range(len(ruta)-1):
            origen_tramo = ruta[i]
            destino_tramo = ruta[i+1]
            distancia_tramo = G[origen_tramo][destino_tramo]['weight']
            tramos.append((origen_tramo, destino_tramo, distancia_tramo))
        
        return {
            'ruta': ruta,
            'distancia_total': distancia_total,
            'tramos': tramos
        }
    except nx.NetworkXNoPath:
        return f"No existe una ruta entre {origen_match} y {destino_match}"

def visualizar_ruta(G, resultado_ruta, filename="ruta_optima.png"):
    """Visualiza la ruta más corta entre dos ciudades"""
    if isinstance(resultado_ruta, str):
        print(resultado_ruta)
        return None
    
    ruta = resultado_ruta['ruta']
    distancia_total = resultado_ruta['distancia_total']
    
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
    plt.title(f"Ruta Óptima: {ruta[0]} → {ruta[-1]}", fontsize=16, fontweight='bold')
    plt.figtext(0.5, 0.01, f"Distancia total: {distancia_total:.1f} km\nRuta: {' → '.join(ruta)}", 
               ha='center', fontsize=12, bbox=dict(facecolor='lightyellow', alpha=0.9, pad=0.5))
    
    plt.axis('off')
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Ruta guardada como {filename}")
    return filename

def main():
    archivo_excel = r"c:\Users\acuri\dev\worksapce\python\IA\Deber\Ecuador_Distancias.xls"
    
    print(f"Cargando datos desde {archivo_excel}...")
    df = cargar_datos_excel(archivo_excel)
    
    if df is None:
        print("Error: No se pudo cargar el archivo Excel.")
        return
    
    # Crear matriz de distancias correcta
    print("Creando matriz de distancias...")
    matriz_distancias, ciudades = crear_matriz_distancias(df)
    
    # Crear grafo
    print("Creando grafo...")
    G = crear_grafo(matriz_distancias)
    print(f"Grafo creado con {G.number_of_nodes()} ciudades y {G.number_of_edges()} conexiones.")
    
    # Visualizar grafo
    visualizar_grafo(G)
    
    # Calcular y visualizar algunas rutas de ejemplo
    rutas_ejemplo = [
        ("Quito", "Guayaquil"),
        ("Cuenca", "Loja"),
        ("Ambato", "Esmeraldas")
    ]
    
    for origen, destino in rutas_ejemplo:
        print(f"\nBuscando ruta óptima entre {origen} y {destino}...")
        resultado = encontrar_ruta_optima(G, origen, destino)
        
        if isinstance(resultado, dict):
            print(f"Ruta encontrada: {' → '.join(resultado['ruta'])}")
            print(f"Distancia total: {resultado['distancia_total']:.1f} km")
            
            print("Tramos de la ruta:")
            for origen_tramo, destino_tramo, distancia_tramo in resultado['tramos']:
                print(f"  {origen_tramo} → {destino_tramo}: {distancia_tramo:.1f} km")
            
            # Visualizar la ruta
            visualizar_ruta(G, resultado, 
                           filename=f"ruta_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png")
        else:
            print(resultado)
    
    print("\n¡Análisis completado con éxito!")

if __name__ == "__main__":
    main()