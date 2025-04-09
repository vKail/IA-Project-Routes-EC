import tkinter as tk
from tkinter import ttk, messagebox

class DialogoSeleccionConexiones:
    """Diálogo para seleccionar conexiones al crear una nueva ciudad"""
    
    def __init__(self, parent, titulo, ciudades, ciudad_nueva):
        self.resultado = []
        self.ciudades = ciudades
        self.ciudad_nueva = ciudad_nueva
        
        # Crear ventana de diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar en la pantalla
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width() // 2 - 250,
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
        
        # Cabecera
        ttk.Label(frame, text=f"Seleccione las conexiones para {self.ciudad_nueva}", 
                font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        ttk.Label(frame, text="Agregue las ciudades que están directamente conectadas por carretera").pack(pady=5)
        
        # Panel de selección de ciudad y distancia
        panel_seleccion = ttk.Frame(frame)
        panel_seleccion.pack(fill=tk.X, pady=10)
        
        ttk.Label(panel_seleccion, text="Ciudad vecina:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.combo_ciudad = ttk.Combobox(panel_seleccion, values=self.ciudades, state="readonly", width=25)
        self.combo_ciudad.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(panel_seleccion, text="Distancia (km):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.distancia_var = tk.StringVar()
        ttk.Entry(panel_seleccion, textvariable=self.distancia_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(panel_seleccion, text="Agregar", command=self.agregar_conexion).grid(row=1, column=2, padx=5, pady=5)
        
        # Lista de conexiones agregadas
        ttk.Label(frame, text="Conexiones agregadas:").pack(anchor=tk.W, pady=5)
        
        # Frame para la lista
        lista_frame = ttk.Frame(frame)
        lista_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview para la lista
        self.lista = ttk.Treeview(lista_frame, columns=("ciudad", "distancia"), show="headings", height=8)
        self.lista.heading("ciudad", text="Ciudad")
        self.lista.heading("distancia", text="Distancia (km)")
        
        self.lista.column("ciudad", width=300)
        self.lista.column("distancia", width=100)
        
        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.lista.yview)
        self.lista.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón para eliminar selección
        ttk.Button(frame, text="Eliminar seleccionado", command=self.eliminar_seleccion).pack(anchor=tk.W, pady=5)
        
        # Botones de acción
        panel_botones = ttk.Frame(frame)
        panel_botones.pack(fill=tk.X, pady=10)
        
        ttk.Button(panel_botones, text="Cancelar", command=self.cancelar).pack(side=tk.RIGHT, padx=5)
        ttk.Button(panel_botones, text="Aceptar", command=self.aceptar).pack(side=tk.RIGHT, padx=5)
    
    def agregar_conexion(self):
        """Agregar una conexión a la lista"""
        ciudad = self.combo_ciudad.get()
        
        try:
            distancia = float(self.distancia_var.get())
        except ValueError:
            messagebox.showerror("Error", "La distancia debe ser un número válido", parent=self.dialog)
            return
        
        if not ciudad:
            messagebox.showwarning("Advertencia", "Debe seleccionar una ciudad", parent=self.dialog)
            return
        
        if distancia <= 0:
            messagebox.showwarning("Advertencia", "La distancia debe ser mayor que cero", parent=self.dialog)
            return
        
        # Verificar que no exista ya una conexión con esta ciudad
        for item_id in self.lista.get_children():
            if self.lista.item(item_id, "values")[0] == ciudad:
                messagebox.showwarning("Advertencia", f"Ya existe una conexión con {ciudad}", parent=self.dialog)
                return
        
        # Agregar a la lista
        self.lista.insert("", tk.END, values=(ciudad, f"{distancia:.1f}"))
        
        # Limpiar campos
        self.combo_ciudad.set("")
        self.distancia_var.set("")
    
    def eliminar_seleccion(self):
        """Eliminar la selección actual de la lista"""
        seleccion = self.lista.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "No hay ninguna conexión seleccionada", parent=self.dialog)
            return
        
        self.lista.delete(seleccion)
    
    def aceptar(self):
        """Aceptar y guardar las conexiones"""
        # Recopilar todas las conexiones
        for item_id in self.lista.get_children():
            ciudad, distancia = self.lista.item(item_id, "values")
            self.resultado.append((ciudad, float(distancia)))
        
        self.dialog.destroy()
    
    def cancelar(self):
        """Cancelar y cerrar el diálogo"""
        self.resultado = []
        self.dialog.destroy()