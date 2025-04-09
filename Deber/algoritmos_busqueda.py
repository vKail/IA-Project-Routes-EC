import networkx as nx
import numpy as np
import heapq
from geopy.distance import geodesic

class AlgoritmosBusqueda:
    """Clase para implementar diferentes algoritmos de búsqueda de rutas"""
    
    @staticmethod
    def dijkstra(G, origen, destino):
        """
        Búsqueda de costo uniforme (Dijkstra) para encontrar la ruta de menor distancia.
        Ya implementado en NetworkX.
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
                'algoritmo': 'Dijkstra'
            }
        except nx.NetworkXNoPath:
            return f"No existe una ruta entre {origen} y {destino}"
    
    @staticmethod
    def busqueda_voraz(G, origen, destino, coords):
        """
        Implementación de búsqueda voraz (Greedy Best-First Search).
        Utiliza la distancia geodésica directa al destino como heurística.
        
        Args:
            G: Grafo NetworkX
            origen: Nodo de origen
            destino: Nodo de destino
            coords: Diccionario con coordenadas de los nodos {nodo: (lat, lon)}
        """
        # Verificar que el origen y destino existen
        if origen not in G or destino not in G:
            return f"El origen o destino no existen en el grafo"
        
        # Coordenadas del destino
        dest_coords = coords[destino]
        
        # Cola de prioridad para nodos por explorar
        frontera = [(0, origen, [origen], 0)]  # (prioridad, nodo, camino, distancia_acumulada)
        visitados = set()
        
        while frontera:
            # Obtener el nodo con menor valor heurístico (más cercano al destino)
            _, actual, camino, dist_acumulada = heapq.heappop(frontera)
            
            # Si llegamos al destino, hemos encontrado la ruta
            if actual == destino:
                # Calcular tramos
                tramos = []
                for i in range(len(camino)-1):
                    origen_tramo = camino[i]
                    destino_tramo = camino[i+1]
                    distancia_tramo = G[origen_tramo][destino_tramo]['weight']
                    tramos.append((origen_tramo, destino_tramo, distancia_tramo))
                
                return {
                    'ruta': camino,
                    'distancia_total': dist_acumulada,
                    'tramos': tramos,
                    'algoritmo': 'Búsqueda Voraz'
                }
            
            # Omitir nodos ya visitados
            if actual in visitados:
                continue
            
            visitados.add(actual)
            
            # Explorar vecinos
            for vecino in G[actual]:
                if vecino not in visitados:
                    # Distancia acumulada hasta este vecino
                    nueva_dist = dist_acumulada + G[actual][vecino]['weight']
                    
                    # Distancia geodésica directa al destino (heurística)
                    heuristica = geodesic(coords[vecino], dest_coords).kilometers
                    
                    # En búsqueda voraz solo usamos la heurística como criterio de decisión
                    # (no consideramos la distancia acumulada para la prioridad)
                    heapq.heappush(frontera, (heuristica, vecino, camino + [vecino], nueva_dist))
        
        return f"No existe una ruta entre {origen} y {destino}"
    
    @staticmethod
    def a_estrella(G, origen, destino, coords):
        """
        Implementación del algoritmo A* (A estrella).
        Combina el costo del camino recorrido y una heurística para estimar 
        la distancia restante hasta el destino.
        
        Args:
            G: Grafo NetworkX
            origen: Nodo de origen
            destino: Nodo de destino
            coords: Diccionario con coordenadas de los nodos {nodo: (lat, lon)}
        """
        # Verificar que el origen y destino existen
        if origen not in G or destino not in G:
            return f"El origen o destino no existen en el grafo"
        
        # Coordenadas del destino
        dest_coords = coords[destino]
        
        # Cola de prioridad para nodos por explorar
        # (f_score, nodo, camino, g_score)
        # f_score = g_score + h_score (costo total estimado)
        # g_score = costo real acumulado hasta el nodo
        # h_score = heurística (estimación del costo restante)
        frontera = [(0, origen, [origen], 0)]
        visitados = set()
        
        # Diccionario para guardar el mejor g_score conocido para cada nodo
        g_scores = {origen: 0}
        
        while frontera:
            # Obtener el nodo con menor f_score (más prometedor)
            _, actual, camino, g_score = heapq.heappop(frontera)
            
            # Si llegamos al destino, hemos encontrado la ruta
            if actual == destino:
                # Calcular tramos
                tramos = []
                for i in range(len(camino)-1):
                    origen_tramo = camino[i]
                    destino_tramo = camino[i+1]
                    distancia_tramo = G[origen_tramo][destino_tramo]['weight']
                    tramos.append((origen_tramo, destino_tramo, distancia_tramo))
                
                return {
                    'ruta': camino,
                    'distancia_total': g_score,
                    'tramos': tramos,
                    'algoritmo': 'A* (A estrella)'
                }
            
            # No volver a expandir nodos ya visitados
            if actual in visitados:
                continue
            
            visitados.add(actual)
            
            # Explorar vecinos
            for vecino in G.neighbors(actual):
                # Costo para llegar al vecino
                tentative_g_score = g_score + G[actual][vecino]['weight']
                
                # Si ya conocemos un camino mejor a este vecino, ignoramos este
                if vecino in g_scores and tentative_g_score >= g_scores[vecino]:
                    continue
                
                # Este camino es mejor, lo guardamos
                g_scores[vecino] = tentative_g_score
                
                # Calcular la heurística (distancia geodésica directa al destino)
                h_score = geodesic(coords[vecino], dest_coords).kilometers
                
                # f_score es la suma del costo actual y la heurística
                f_score = tentative_g_score + h_score
                
                # Añadir a la frontera
                heapq.heappush(frontera, (f_score, vecino, camino + [vecino], tentative_g_score))
        
        return f"No existe una ruta entre {origen} y {destino}"
    
    @staticmethod
    def comparar_algoritmos(G, origen, destino, coords):
        """
        Compara los resultados de los tres algoritmos de búsqueda.
        
        Args:
            G: Grafo NetworkX
            origen: Nodo de origen
            destino: Nodo de destino
            coords: Diccionario con coordenadas de los nodos {nodo: (lat, lon)}
        
        Returns:
            Diccionario con los resultados de los tres algoritmos
        """
        print(f"Comparando algoritmos para la ruta {origen} → {destino}...")
        
        # Ejecutar cada algoritmo
        resultado_dijkstra = AlgoritmosBusqueda.dijkstra(G, origen, destino)
        resultado_voraz = AlgoritmosBusqueda.busqueda_voraz(G, origen, destino, coords)
        resultado_a_estrella = AlgoritmosBusqueda.a_estrella(G, origen, destino, coords)
        
        return {
            'Dijkstra': resultado_dijkstra,
            'Voraz': resultado_voraz,
            'A_estrella': resultado_a_estrella
        }