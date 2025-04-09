import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import networkx as nx
from PIL import Image, ImageTk
import threading

# Importar nuestros módulos
from ciudades_crud import CiudadesCRUD
from generador_grafo import GeneradorGrafo
from algoritmos_busqueda import AlgoritmosBusqueda
from nueva_ciudad_conexiones import DialogoSeleccionConexiones


class RutasCiudadesApp:
    """Aplicación para encontrar rutas entre ciudades ecuatorianas"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Rutas - Ciudades de Ecuador")
        self.root.geometry("1200x800")
        
        # Variables para el grafo
        self.G = None
        self.coords = None
        self.nombre_a_id = None
        self.ciudades = []
        
        # Variables para la interfaz
        self.ciudad_origen_var = tk.StringVar()
        self.ciudad_destino_var = tk.StringVar()
        self.algoritmo_var = tk.StringVar(value="Dijkstra")  # Valor por defecto
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Cargar datos iniciales (en un hilo separado para no bloquear la interfaz)
        self.mostrar_mensaje_estado("Cargando datos...")
        threading.Thread(target=self.cargar_datos_iniciales).start()
    
    def crear_interfaz(self):
        """Crear la interfaz gráfica"""
        # Panel principal
        panel_principal = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        panel_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo (controles)
        self.panel_izquierdo = ttk.Frame(panel_principal, width=300)
        panel_principal.add(self.panel_izquierdo, weight=1)
        
        # Panel derecho (visualización)
        self.panel_derecho = ttk.Frame(panel_principal)
        panel_principal.add(self.panel_derecho, weight=3)
        
        # Sección de búsqueda de rutas
        self.crear_seccion_busqueda()
        
        # Sección de gestión de ciudades
        self.crear_seccion_gestion_ciudades()

        # Sección para gestionar conexiones entre ciudades
        self.crear_botones_conexiones()
        
        # Área de resultados en el panel izquierdo
        self.crear_area_resultados()
        
        # Área de visualización en panel derecho
        self.crear_area_visualizacion()
        
        # Barra de estado
        self.barra_estado = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.barra_estado.pack(side=tk.BOTTOM, fill=tk.X)
    
    def crear_seccion_busqueda(self):
        """Crear sección para búsqueda de rutas"""
        # Marco para la búsqueda de rutas
        marco_busqueda = ttk.LabelFrame(self.panel_izquierdo, text="Buscar Ruta")
        marco_busqueda.pack(fill=tk.X, padx=5, pady=5)
        
        # Origen
        ttk.Label(marco_busqueda, text="Ciudad de Origen:").pack(anchor=tk.W, padx=5, pady=2)
        self.combo_origen = ttk.Combobox(marco_busqueda, textvariable=self.ciudad_origen_var, state="readonly")
        self.combo_origen.pack(fill=tk.X, padx=5, pady=2)
        
        # Destino
        ttk.Label(marco_busqueda, text="Ciudad de Destino:").pack(anchor=tk.W, padx=5, pady=2)
        self.combo_destino = ttk.Combobox(marco_busqueda, textvariable=self.ciudad_destino_var, state="readonly")
        self.combo_destino.pack(fill=tk.X, padx=5, pady=2)
        
        # Algoritmo
        ttk.Label(marco_busqueda, text="Algoritmo:").pack(anchor=tk.W, padx=5, pady=2)
        algoritmos = ["Dijkstra", "Búsqueda Voraz", "A* (A estrella)", "Comparar todos"]
        self.combo_algoritmo = ttk.Combobox(marco_busqueda, textvariable=self.algoritmo_var, values=algoritmos, state="readonly")
        self.combo_algoritmo.pack(fill=tk.X, padx=5, pady=2)
        self.combo_algoritmo.current(0)  # Seleccionar primer elemento
        
        # Botón de búsqueda
        ttk.Button(marco_busqueda, text="Buscar Ruta", command=self.buscar_ruta).pack(fill=tk.X, padx=5, pady=5)
    
    def crear_seccion_gestion_ciudades(self):
        """Crear sección para gestión de ciudades"""
        # Marco para gestión de ciudades
        marco_gestion = ttk.LabelFrame(self.panel_izquierdo, text="Gestión de Ciudades")
        marco_gestion.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones para gestión
        ttk.Button(marco_gestion, text="Nueva Ciudad", command=self.nueva_ciudad).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(marco_gestion, text="Editar Ciudad", command=self.editar_ciudad).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(marco_gestion, text="Eliminar Ciudad", command=self.eliminar_ciudad).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(marco_gestion, text="Ver Todas las Ciudades", command=self.ver_ciudades).pack(fill=tk.X, padx=5, pady=2)
    
    def crear_botones_conexiones(self):
        """Crear botones para gestionar conexiones entre ciudades"""
        frame_conexiones = ttk.LabelFrame(self.panel_izquierdo, text="Gestión de Conexiones")
        frame_conexiones.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(frame_conexiones, text="Agregar Conexión", 
                command=self.agregar_conexion).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(frame_conexiones, text="Ver Todas las Conexiones", 
                command=self.ver_conexiones).pack(fill=tk.X, padx=5, pady=2)

    def agregar_conexion(self):
        """Agregar una nueva conexión entre ciudades"""
        # Pedir al usuario que seleccione las dos ciudades
        ciudad1 = self._seleccionar_ciudad("Seleccionar Ciudad 1")
        if not ciudad1:
            return
        
        ciudad2 = self._seleccionar_ciudad("Seleccionar Ciudad 2")
        if not ciudad2:
            return
        
        if ciudad1 == ciudad2:
            messagebox.showwarning("Advertencia", "Debe seleccionar dos ciudades diferentes")
            return
        
        # Pedir la distancia
        distancia = simpledialog.askfloat(
            "Distancia", 
            f"Ingrese la distancia entre {ciudad1} y {ciudad2} (km):",
            minvalue=0.1
        )
        
        if distancia is None:
            return
        
        # Ejecutar en un hilo
        self.mostrar_mensaje_estado(f"Agregando conexión entre {ciudad1} y {ciudad2}...")
        threading.Thread(target=self._ejecutar_agregar_conexion, 
                    args=(ciudad1, ciudad2, distancia)).start()

    def _ejecutar_agregar_conexion(self, ciudad1, ciudad2, distancia):
        """Agregar una conexión en la base de datos"""
        try:
            ciudad1_id = self.nombre_a_id[ciudad1]
            ciudad2_id = self.nombre_a_id[ciudad2]
            
            resultado = CiudadesCRUD.crear_conexion(ciudad1_id, ciudad2_id, distancia)
            
            if "error" in resultado:
                self.mostrar_mensaje_estado(f"Error: {resultado['error']}")
                self.root.after(0, lambda: messagebox.showerror("Error", resultado["error"]))
                return
            
            # Recargar el grafo
            self.G, self.coords, self.nombre_a_id = GeneradorGrafo.crear_grafo()
            
            # Actualizar visualización
            imagen_grafo = GeneradorGrafo.visualizar_grafo(self.G, self.coords, "grafo_actualizado.png")
            self.root.after(0, lambda: self.mostrar_imagen(imagen_grafo))
            
            self.mostrar_mensaje_estado(f"Conexión entre {ciudad1} y {ciudad2} agregada correctamente")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"Conexión entre {ciudad1} y {ciudad2} agregada correctamente"))
            
        except Exception as e:
            error_msg = f"Error al agregar conexión: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    def ver_conexiones(self):
        """Ver todas las conexiones entre ciudades"""
        # Obtener todas las conexiones
        self.mostrar_mensaje_estado("Cargando conexiones...")
        threading.Thread(target=self._cargar_conexiones).start()

    def _cargar_conexiones(self):
        """Cargar y mostrar las conexiones en un hilo separado"""
        try:
            # Obtener todas las ciudades para mapear IDs a nombres
            ciudades = CiudadesCRUD.listar_ciudades()
            id_a_nombre = {ciudad['id']: ciudad['nombre'] for ciudad in ciudades}
            
            # Obtener todas las distancias
            distancias = []
            
            # Acumular las distancias de cada ciudad
            for ciudad in ciudades:
                ciudad_distancias = CiudadesCRUD.listar_distancias(ciudad['id'])
                for d in ciudad_distancias:
                    # Solo agregar una dirección para evitar duplicados
                    if ciudad['id'] < d['destino_id']:
                        distancias.append({
                            'ciudad1': ciudad['nombre'],
                            'ciudad2': d['nombre'],
                            'distancia': d['distancia']
                        })
            
            # Mostrar en la interfaz
            self.root.after(0, lambda: self._mostrar_conexiones(distancias))
            
        except Exception as e:
            error_msg = f"Error al cargar conexiones: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    def _mostrar_conexiones(self, conexiones):
        """Mostrar las conexiones en una ventana"""
        if not conexiones:
            messagebox.showinfo("Información", "No hay conexiones para mostrar")
            return
        
        # Crear ventana
        ventana = tk.Toplevel(self.root)
        ventana.title("Conexiones entre Ciudades")
        ventana.geometry("600x400")
        
        # Frame para la tabla
        frame_tabla = ttk.Frame(ventana)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabla para mostrar las conexiones
        tabla = ttk.Treeview(frame_tabla, columns=("ciudad1", "ciudad2", "distancia"), show="headings")
        tabla.heading("ciudad1", text="Ciudad 1")
        tabla.heading("ciudad2", text="Ciudad 2")
        tabla.heading("distancia", text="Distancia (km)")
        
        tabla.column("ciudad1", width=200)
        tabla.column("ciudad2", width=200)
        tabla.column("distancia", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tabla.yview)
        tabla.configure(yscrollcommand=scrollbar.set)
        
        tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar la tabla
        for conexion in conexiones:
            tabla.insert("", tk.END, values=(
                conexion['ciudad1'],
                conexion['ciudad2'],
                f"{conexion['distancia']:.1f}"
            ))
        
        # Botones
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Mostrar mensaje de estado
        self.mostrar_mensaje_estado(f"Se muestran {len(conexiones)} conexiones")


    def crear_area_resultados(self):
        """Crear área para mostrar resultados de búsqueda"""
        # Marco para resultados
        marco_resultados = ttk.LabelFrame(self.panel_izquierdo, text="Resultados")
        marco_resultados.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Área de texto para resultados
        self.texto_resultados = tk.Text(marco_resultados, height=10, wrap=tk.WORD)
        self.texto_resultados.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar para el área de texto
        scrollbar = ttk.Scrollbar(self.texto_resultados, command=self.texto_resultados.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.texto_resultados.config(yscrollcommand=scrollbar.set)
        
        # Solo lectura
        self.texto_resultados.configure(state='disabled')
    
    def crear_area_visualizacion(self):
        """Crear área para visualizar el grafo y las rutas"""
        # Marco para visualización
        self.marco_visualizacion = ttk.LabelFrame(self.panel_derecho, text="Visualización")
        self.marco_visualizacion.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para mostrar la imagen
        self.canvas = tk.Canvas(self.marco_visualizacion, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
    
    def cargar_datos_iniciales(self):
        """Cargar los datos iniciales del grafo y las ciudades"""
        try:
            # Generar el grafo
            self.G, self.coords, self.nombre_a_id = GeneradorGrafo.crear_grafo()
            
            if not self.G:
                self.mostrar_mensaje_estado("Error al cargar el grafo")
                messagebox.showerror("Error", "No se pudo cargar el grafo de ciudades")
                return
            
            # Obtener lista de ciudades para los combos
            self.ciudades = sorted(list(self.G.nodes()))
            
            # Actualizar combos
            self.root.after(0, self.actualizar_combos_ciudades)
            
            # Visualizar grafo inicial
            self.mostrar_mensaje_estado("Generando visualización inicial...")
            imagen_grafo = GeneradorGrafo.visualizar_grafo(self.G, self.coords, "grafo_inicial.png")
            
            # Mostrar la imagen en la interfaz
            self.root.after(0, lambda: self.mostrar_imagen(imagen_grafo))
            
            self.mostrar_mensaje_estado("Datos cargados correctamente")
        except Exception as e:
            self.mostrar_mensaje_estado(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")
    
    def actualizar_combos_ciudades(self):
        """Actualizar los combos de selección de ciudades"""
        self.combo_origen['values'] = self.ciudades
        self.combo_destino['values'] = self.ciudades
        
        # Seleccionar valores por defecto
        if self.ciudades:
            self.combo_origen.current(0)
            if len(self.ciudades) > 1:
                self.combo_destino.current(1)
            else:
                self.combo_destino.current(0)
    
    def mostrar_imagen(self, ruta_imagen):
        """Mostrar una imagen en el canvas"""
        try:
            # Limpiar canvas
            self.canvas.delete("all")
            
            # Cargar imagen
            imagen = Image.open(ruta_imagen)
            
            # Redimensionar para ajustar al canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Asegurar que el canvas tiene un tamaño válido
            if canvas_width <= 1 or canvas_height <= 1:
                # El canvas aún no ha sido configurado, usar tamaños predeterminados
                canvas_width = 800
                canvas_height = 600
            
            # Calcular proporciones para el redimensionamiento
            img_width, img_height = imagen.size
            ratio = min(canvas_width/img_width, canvas_height/img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionar imagen
            imagen_redimensionada = imagen.resize((new_width, new_height), Image.LANCZOS)
            
            # Convertir a formato compatible con tkinter
            self.tk_imagen = ImageTk.PhotoImage(imagen_redimensionada)
            
            # Mostrar en el canvas
            self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.tk_imagen, anchor=tk.CENTER)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar la imagen: {str(e)}")
    
    def buscar_ruta(self):
        """Buscar ruta entre las ciudades seleccionadas"""
        origen = self.ciudad_origen_var.get()
        destino = self.ciudad_destino_var.get()
        algoritmo = self.algoritmo_var.get()
        
        if not origen or not destino:
            messagebox.showwarning("Advertencia", "Debe seleccionar ciudad de origen y destino")
            return
        
        if origen == destino:
            messagebox.showwarning("Advertencia", "Origen y destino deben ser diferentes")
            return
        
        self.mostrar_mensaje_estado(f"Buscando ruta de {origen} a {destino} usando {algoritmo}...")
        
        # Ejecutar en un hilo para no bloquear la interfaz
        threading.Thread(target=self._ejecutar_busqueda, args=(origen, destino, algoritmo)).start()
    
    def _ejecutar_busqueda(self, origen, destino, algoritmo):
        """Ejecutar la búsqueda de ruta en un hilo separado"""
        try:
            resultado = None
            
            # Ejecutar el algoritmo seleccionado
            if algoritmo == "Dijkstra":
                resultado = AlgoritmosBusqueda.dijkstra(self.G, origen, destino)
                nombre_archivo = f"ruta_dijkstra_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png"
                
            elif algoritmo == "Búsqueda Voraz":
                if not self.coords or origen not in self.coords or destino not in self.coords:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", 
                        "El algoritmo Voraz requiere coordenadas para todas las ciudades en la ruta"
                    ))
                    self.mostrar_mensaje_estado("Error: Faltan coordenadas para las ciudades")
                    return
                
                resultado = AlgoritmosBusqueda.busqueda_voraz(self.G, origen, destino, self.coords)
                nombre_archivo = f"ruta_voraz_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png"
                
            elif algoritmo == "A* (A estrella)":
                if not self.coords or origen not in self.coords or destino not in self.coords:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", 
                        "El algoritmo A* requiere coordenadas para todas las ciudades en la ruta"
                    ))
                    self.mostrar_mensaje_estado("Error: Faltan coordenadas para las ciudades")
                    return
                
                resultado = AlgoritmosBusqueda.a_estrella(self.G, origen, destino, self.coords)
                nombre_archivo = f"ruta_a_estrella_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png"
                
            elif algoritmo == "Comparar todos":
                if not self.coords or origen not in self.coords or destino not in self.coords:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", 
                        "La comparación requiere coordenadas para todas las ciudades en la ruta"
                    ))
                    self.mostrar_mensaje_estado("Error: Faltan coordenadas para las ciudades")
                    return
                
                resultados = AlgoritmosBusqueda.comparar_algoritmos(self.G, origen, destino, self.coords)
                
                # Mostrar resultados de la comparación
                self._mostrar_comparacion_resultados(resultados)
                
                # Visualizar la ruta de Dijkstra (como referencia)
                resultado = resultados['Dijkstra']
                nombre_archivo = f"ruta_comparacion_{origen.replace(' ','_')}_a_{destino.replace(' ','_')}.png"
            
            # Verificar si se encontró una ruta
            if isinstance(resultado, str):
                # Es un mensaje de error
                self.root.after(0, lambda: messagebox.showinfo("Resultado", resultado))
                self.mostrar_mensaje_estado(resultado)
                return
            
            # Visualizar la ruta
            imagen_ruta = GeneradorGrafo.visualizar_ruta(self.G, resultado, self.coords, nombre_archivo)
            
            # Mostrar resultados en el área de texto
            self._mostrar_resultado_ruta(resultado)
            
            # Mostrar la imagen en la interfaz
            self.root.after(0, lambda: self.mostrar_imagen(imagen_ruta))
            
            self.mostrar_mensaje_estado("Ruta encontrada")
            
        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def _mostrar_resultado_ruta(self, resultado):
        """Mostrar el resultado de la ruta en el área de texto"""
        if isinstance(resultado, str):
            texto = resultado
        else:
            texto = f"Ruta encontrada ({resultado['algoritmo']}):\n\n"
            texto += f"Origen: {resultado['ruta'][0]}\n"
            texto += f"Destino: {resultado['ruta'][-1]}\n"
            texto += f"Distancia total: {resultado['distancia_total']:.2f} km\n"
            texto += f"Ciudades: {len(resultado['ruta'])}\n\n"
            
            texto += "Tramos:\n"
            for origen, destino, distancia in resultado['tramos']:
                texto += f"  • {origen} → {destino}: {distancia:.2f} km\n"
        
        # Actualizar texto en la interfaz
        self.root.after(0, lambda: self._actualizar_texto_resultados(texto))
    
    def _mostrar_comparacion_resultados(self, resultados):
        """Mostrar la comparación de los diferentes algoritmos"""
        texto = "COMPARACIÓN DE ALGORITMOS\n"
        texto += "========================\n\n"
        
        for nombre, resultado in resultados.items():
            if isinstance(resultado, str):
                texto += f"{nombre}: {resultado}\n\n"
            else:
                texto += f"{nombre}:\n"
                texto += f"  • Distancia: {resultado['distancia_total']:.2f} km\n"
                texto += f"  • Ciudades: {len(resultado['ruta'])}\n"
                texto += f"  • Ruta: {' → '.join(resultado['ruta'])}\n\n"
        
        # Actualizar texto en la interfaz
        self.root.after(0, lambda: self._actualizar_texto_resultados(texto))
    
    def _actualizar_texto_resultados(self, texto):
        """Actualizar el contenido del área de resultados"""
        self.texto_resultados.configure(state='normal')
        self.texto_resultados.delete(1.0, tk.END)
        self.texto_resultados.insert(tk.END, texto)
        self.texto_resultados.configure(state='disabled')
    
    def nueva_ciudad(self):
        """Abrir ventana para añadir una nueva ciudad"""
        dialogo = DialogoCiudad(self.root, "Nueva Ciudad")
        if dialogo.resultado:
            nombre, latitud, longitud = dialogo.resultado
            
            self.mostrar_mensaje_estado(f"Añadiendo nueva ciudad: {nombre}...")
            
            # Ejecutar en un hilo
            threading.Thread(target=self._ejecutar_nueva_ciudad, 
                            args=(nombre, latitud, longitud)).start()
    
    def _ejecutar_nueva_ciudad(self, nombre, latitud, longitud):
        """Añadir una nueva ciudad a la base de datos"""
        try:
            # Solicitar conexiones para la nueva ciudad
            dialogo_conexiones = DialogoSeleccionConexiones(self.root, "Conexiones para la nueva ciudad", self.ciudades, nombre)
            conexiones = dialogo_conexiones.resultado
            
            # Si hay conexiones, prepararlas para el formato esperado
            conexiones_para_bd = []
            if conexiones:
                for ciudad_nombre, distancia in conexiones:
                    ciudad_id = self.nombre_a_id[ciudad_nombre]
                    conexiones_para_bd.append({
                        'ciudad_id': ciudad_id,
                        'distancia': distancia
                    })
            
            # Crear la ciudad
            resultado = CiudadesCRUD.crear_ciudad(nombre, latitud, longitud, conexiones_para_bd)
            
            if "error" in resultado:
                self.mostrar_mensaje_estado(f"Error: {resultado['error']}")
                self.root.after(0, lambda: messagebox.showerror("Error", resultado["error"]))
                return
            
            # Recargar el grafo
            self.G, self.coords, self.nombre_a_id = GeneradorGrafo.crear_grafo()
            
            # Actualizar la lista de ciudades
            self.ciudades = sorted(list(self.G.nodes()))
            self.root.after(0, self.actualizar_combos_ciudades)
            
            # Actualizar visualización
            imagen_grafo = GeneradorGrafo.visualizar_grafo(self.G, self.coords, "grafo_actualizado.png")
            self.root.after(0, lambda: self.mostrar_imagen(imagen_grafo))
            
            self.mostrar_mensaje_estado(f"Ciudad {nombre} añadida correctamente")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"Ciudad {nombre} añadida correctamente"))
            
        except Exception as e:
            error_msg = f"Error al añadir ciudad: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
    def editar_ciudad(self):
        """Editar una ciudad existente"""
        if not self.ciudades:
            messagebox.showwarning("Advertencia", "No hay ciudades para editar")
            return
        
        # Seleccionar ciudad a editar
        ciudad = self._seleccionar_ciudad("Seleccionar Ciudad a Editar")
        if not ciudad:
            return
        
        # Obtener datos actuales de la ciudad
        ciudad_id = self.nombre_a_id[ciudad]
        datos_ciudad = CiudadesCRUD.obtener_ciudad(ciudad_id)
        
        if not datos_ciudad:
            messagebox.showerror("Error", f"No se pudieron obtener los datos de {ciudad}")
            return
        
        # Abrir diálogo de edición
        dialogo = DialogoCiudad(
            self.root, 
            f"Editar Ciudad: {ciudad}",
            nombre=datos_ciudad['nombre'],
            latitud=datos_ciudad['latitud'],
            longitud=datos_ciudad['longitud']
        )
        
        if dialogo.resultado:
            nombre, latitud, longitud = dialogo.resultado
            
            self.mostrar_mensaje_estado(f"Actualizando ciudad: {nombre}...")
            
            # Ejecutar en un hilo
            threading.Thread(target=self._ejecutar_editar_ciudad, 
                            args=(ciudad_id, nombre, latitud, longitud)).start()
    
    def _ejecutar_editar_ciudad(self, ciudad_id, nombre, latitud, longitud):
        """Actualizar una ciudad en la base de datos"""
        try:
            resultado = CiudadesCRUD.actualizar_ciudad(ciudad_id, nombre, latitud, longitud)
            
            if "error" in resultado:
                self.mostrar_mensaje_estado(f"Error: {resultado['error']}")
                self.root.after(0, lambda: messagebox.showerror("Error", resultado["error"]))
                return
            
            # Recargar el grafo
            self.G, self.coords, self.nombre_a_id = GeneradorGrafo.crear_grafo()
            
            # Actualizar la lista de ciudades
            self.ciudades = sorted(list(self.G.nodes()))
            self.root.after(0, self.actualizar_combos_ciudades)
            
            # Actualizar visualización
            imagen_grafo = GeneradorGrafo.visualizar_grafo(self.G, self.coords, "grafo_actualizado.png")
            self.root.after(0, lambda: self.mostrar_imagen(imagen_grafo))
            
            self.mostrar_mensaje_estado(f"Ciudad {nombre} actualizada correctamente")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"Ciudad {nombre} actualizada correctamente"))
            
        except Exception as e:
            error_msg = f"Error al actualizar ciudad: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def eliminar_ciudad(self):
        """Eliminar una ciudad existente"""
        if not self.ciudades:
            messagebox.showwarning("Advertencia", "No hay ciudades para eliminar")
            return
        
        # Seleccionar ciudad a eliminar
        ciudad = self._seleccionar_ciudad("Seleccionar Ciudad a Eliminar")
        if not ciudad:
            return
        
        # Confirmar eliminación
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Está seguro de eliminar la ciudad {ciudad}?\n\n"
            "Esta acción eliminará también todas las distancias asociadas a esta ciudad."
        )
        
        if not confirmar:
            return
        
        ciudad_id = self.nombre_a_id[ciudad]
        self.mostrar_mensaje_estado(f"Eliminando ciudad: {ciudad}...")
        
        # Ejecutar en un hilo
        threading.Thread(target=self._ejecutar_eliminar_ciudad, args=(ciudad_id, ciudad)).start()
    
    def _ejecutar_eliminar_ciudad(self, ciudad_id, nombre_ciudad):
        """Eliminar una ciudad de la base de datos"""
        try:
            resultado = CiudadesCRUD.eliminar_ciudad(ciudad_id)
            
            if "error" in resultado:
                self.mostrar_mensaje_estado(f"Error: {resultado['error']}")
                self.root.after(0, lambda: messagebox.showerror("Error", resultado["error"]))
                return
            
            # Recargar el grafo
            self.G, self.coords, self.nombre_a_id = GeneradorGrafo.crear_grafo()
            
            # Actualizar la lista de ciudades
            self.ciudades = sorted(list(self.G.nodes()))
            self.root.after(0, self.actualizar_combos_ciudades)
            
            # Actualizar visualización
            imagen_grafo = GeneradorGrafo.visualizar_grafo(self.G, self.coords, "grafo_actualizado.png")
            self.root.after(0, lambda: self.mostrar_imagen(imagen_grafo))
            
            self.mostrar_mensaje_estado(f"Ciudad {nombre_ciudad} eliminada correctamente")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", resultado["mensaje"]))
            
        except Exception as e:
            error_msg = f"Error al eliminar ciudad: {str(e)}"
            self.mostrar_mensaje_estado(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def ver_ciudades(self):
        """Mostrar lista de todas las ciudades"""
        if not self.ciudades:
            messagebox.showwarning("Advertencia", "No hay ciudades para mostrar")
            return
        
        # Crear ventana de lista de ciudades
        ventana = tk.Toplevel(self.root)
        ventana.title("Lista de Ciudades")
        ventana.geometry("500x600")
        
        # Crear tabla para mostrar las ciudades
        tabla = ttk.Treeview(ventana, columns=("ID", "Nombre", "Latitud", "Longitud"))
        tabla.heading("#0", text="")
        tabla.heading("ID", text="ID")
        tabla.heading("Nombre", text="Nombre")
        tabla.heading("Latitud", text="Latitud")
        tabla.heading("Longitud", text="Longitud")
        
        tabla.column("#0", width=0, stretch=tk.NO)
        tabla.column("ID", width=50, anchor=tk.CENTER)
        tabla.column("Nombre", width=200)
        tabla.column("Latitud", width=100, anchor=tk.CENTER)
        tabla.column("Longitud", width=100, anchor=tk.CENTER)
        
        # Añadir scrollbar
        scrollbar = ttk.Scrollbar(ventana, orient=tk.VERTICAL, command=tabla.yview)
        tabla.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar elementos
        tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar datos
        self._cargar_datos_tabla_ciudades(tabla)
    
    def _cargar_datos_tabla_ciudades(self, tabla):
        """Cargar datos de ciudades en la tabla"""
        # Limpiar tabla
        for item in tabla.get_children():
            tabla.delete(item)
        
        # Obtener datos actualizados
        ciudades = CiudadesCRUD.listar_ciudades()
        
        # Insertar datos en la tabla
        for ciudad in ciudades:
            tabla.insert(
                "", 
                tk.END, 
                values=(
                    ciudad['id'],
                    ciudad['nombre'],
                    f"{ciudad['latitud']:.6f}" if ciudad['latitud'] is not None else "N/A",
                    f"{ciudad['longitud']:.6f}" if ciudad['longitud'] is not None else "N/A"
                )
            )
    
    def _seleccionar_ciudad(self, titulo):
        """Mostrar un cuadro de diálogo para seleccionar una ciudad"""
        # Diálogo para seleccionar ciudad
        dialogo = DialogoSeleccionCiudad(self.root, titulo, self.ciudades)
        return dialogo.resultado
    
    def mostrar_mensaje_estado(self, mensaje):
        """Mostrar mensaje en la barra de estado"""
        self.root.after(0, lambda: self.barra_estado.config(text=mensaje))


class DialogoCiudad:
    """Diálogo para añadir o editar una ciudad"""
    
    def __init__(self, parent, titulo, nombre="", latitud=None, longitud=None):
        self.resultado = None
        
        # Crear ventana de diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width() // 2 - 200,
            parent.winfo_rooty() + parent.winfo_height() // 2 - 125
        ))
        
        # Variables
        self.nombre_var = tk.StringVar(value=nombre)
        
        if latitud is not None:
            self.latitud_var = tk.DoubleVar(value=latitud)
        else:
            self.latitud_var = tk.DoubleVar()
        
        if longitud is not None:
            self.longitud_var = tk.DoubleVar(value=longitud)
        else:
            self.longitud_var = tk.DoubleVar()
        
        # Crear campos
        self.crear_campos()
        
        # Esperar a que se cierre el diálogo
        parent.wait_window(self.dialog)
    
    def crear_campos(self):
        """Crear campos del formulario"""
        # Marco para el formulario
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo de nombre
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.nombre_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        
        # Campo de latitud
        ttk.Label(frame, text="Latitud:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.latitud_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(frame, text="(decimal, -90 a 90)").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # Campo de longitud
        ttk.Label(frame, text="Longitud:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.longitud_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(frame, text="(decimal, -180 a 180)").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # Información de Ecuador
        ttk.Label(frame, text="En Ecuador: Latitud entre -5 y 2, Longitud entre -81 y -75").grid(row=3, column=0, columnspan=3, pady=10)
        
        # Botones
        botones_frame = ttk.Frame(frame)
        botones_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(botones_frame, text="Cancelar", command=self.cancelar).pack(side=tk.LEFT, padx=10)
        ttk.Button(botones_frame, text="Guardar", command=self.guardar).pack(side=tk.LEFT, padx=10)
    
    def guardar(self):
        """Guardar los datos y cerrar el diálogo"""
        nombre = self.nombre_var.get().strip()
        
        try:
            latitud = self.latitud_var.get()
            longitud = self.longitud_var.get()
            
            # Validar datos
            if not nombre:
                messagebox.showerror("Error", "El nombre de la ciudad es obligatorio")
                return
            
            if latitud < -90 or latitud > 90:
                messagebox.showerror("Error", "La latitud debe estar entre -90 y 90 grados")
                return
            
            if longitud < -180 or longitud > 180:
                messagebox.showerror("Error", "La longitud debe estar entre -180 y 180 grados")
                return
            
            # Guardar resultado y cerrar
            self.resultado = (nombre, latitud, longitud)
            self.dialog.destroy()
            
        except tk.TclError:
            messagebox.showerror("Error", "Los valores de latitud y longitud deben ser números decimales")
    
    def cancelar(self):
        """Cancelar y cerrar el diálogo"""
        self.dialog.destroy()


class DialogoSeleccionCiudad:
    """Diálogo para seleccionar una ciudad de la lista"""
    
    def __init__(self, parent, titulo, ciudades):
        self.resultado = None
        self.ciudades = ciudades
        
        # Crear ventana de diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width() // 2 - 150,
            parent.winfo_rooty() + parent.winfo_height() // 2 - 200
        ))
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Esperar a que se cierre el diálogo
        parent.wait_window(self.dialog)
    
    def crear_interfaz(self):
        """Crear interfaz del diálogo"""
        # Marco principal
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Etiqueta
        ttk.Label(frame, text="Seleccione una ciudad:").pack(pady=5)
        
        # Campo de búsqueda
        self.busqueda_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.busqueda_var).pack(fill=tk.X, pady=5)
        self.busqueda_var.trace_add("write", self.filtrar_ciudades)
        
        # Lista de ciudades
        frame_lista = ttk.Frame(frame)
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.listbox = tk.Listbox(frame_lista)
        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar la lista
        self.llenar_lista()
        
        # Botones
        frame_botones = ttk.Frame(frame)
        frame_botones.pack(fill=tk.X, pady=10)
        
        ttk.Button(frame_botones, text="Cancelar", command=self.cancelar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Seleccionar", command=self.seleccionar).pack(side=tk.RIGHT, padx=5)
        
        # Doble clic para seleccionar
        self.listbox.bind("<Double-1>", lambda e: self.seleccionar())
    
    def llenar_lista(self, filtro=""):
        """Llenar la lista de ciudades"""
        self.listbox.delete(0, tk.END)
        
        for ciudad in self.ciudades:
            if filtro.lower() in ciudad.lower():
                self.listbox.insert(tk.END, ciudad)
    
    def filtrar_ciudades(self, *args):
        """Filtrar la lista de ciudades según el texto de búsqueda"""
        self.llenar_lista(self.busqueda_var.get())
    
    def seleccionar(self):
        """Seleccionar la ciudad y cerrar el diálogo"""
        seleccion = self.listbox.curselection()
        
        if not seleccion:
            messagebox.showwarning("Advertencia", "Debe seleccionar una ciudad")
            return
        
        self.resultado = self.listbox.get(seleccion[0])
        self.dialog.destroy()
    
    def cancelar(self):
        """Cancelar y cerrar el diálogo"""
        self.dialog.destroy()

# Función principal
def main():
    root = tk.Tk()
    app = RutasCiudadesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()