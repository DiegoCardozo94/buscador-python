import os
import tkinter as tk
from tkinter import ttk

# Importar los Mixins
from .estado import EstadoMixin
from .hilos import HilosMixin

# La clase principal hereda la lógica de Hilos (acciones) y Estado (UI control)
class VentanaDuplicados(HilosMixin, EstadoMixin):
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Buscador de duplicados (Automático)")
        self.ventana.geometry("1200x700")

        # --- Variables de estado ---
        # Estas variables son esenciales y utilizadas por los Mixins
        self.duplicados_global = {}
        self.current_thumbnail_tk = None

        # --- Inicialización de referencias a widgets ---
        # Inicializar todos los widgets principales para evitar AttributeError en los Mixins
        self.entrada_carpeta = None
        self.progress_bar = None
        self.contador_label = None
        self.tabla = None
        self.thumbnail_label = None
        self.entrada_prefijo = None

        # Referencias a Botones (Usadas por EstadoMixin para habilitar/deshabilitar)
        self.boton_explorar = None
        self.boton_eliminar_auto = None
        self.boton_mover = None
        self.boton_comparar = None
        self.boton_refrescar = None
        self.boton_mover_imagenes = None
        self.boton_eliminar_prefijo = None
        
        self._crear_widgets()
        self._configurar_eventos()
        
        # Inicializar el estado de los botones después de crearlos
        self._actualizar_estado_botones(escaneando=False) 

    def _crear_widgets(self):
        # --- 1. Frame Superior (Entrada/Explorar) ---
        frame = ttk.Frame(self.ventana, padding=10)
        frame.pack(fill='x')

        self.entrada_carpeta = ttk.Entry(frame, width=70)
        self.entrada_carpeta.grid(row=0, column=0, padx=5, sticky='ew')
        self.boton_explorar = ttk.Button(frame, text="Seleccionar carpeta", command=self.seleccionar_carpeta)
        self.boton_explorar.grid(row=0, column=1, padx=5)
        frame.columnconfigure(0, weight=1)

        # --- 2. Barra de progreso y Contador ---
        self.progress_bar = ttk.Progressbar(self.ventana, mode='determinate')
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        self.contador_label = ttk.Label(self.ventana, text="Archivos escaneados: 0")
        self.contador_label.pack()

        # --- 3. Contenedor Principal (Tabla y Preview) ---
        contenedor = ttk.Frame(self.ventana)
        contenedor.pack(fill='both', expand=True, padx=10, pady=10)

        # TABLA
        self.tabla = ttk.Treeview(contenedor, columns=("Ruta", "Nombre", "Tamaño", "Tipo"), show='headings', height=20)
        
        # Configuración de encabezados de la tabla
        self.tabla.heading("Ruta", text="Ruta Completa", anchor=tk.W)
        self.tabla.heading("Nombre", text="Nombre de Archivo", anchor=tk.W)
        self.tabla.heading("Tamaño", text="Tamaño", anchor=tk.W)
        self.tabla.heading("Tipo", text="Tipo", anchor=tk.W)

        # Configuración de columnas (Ancho)
        self.tabla.column("Ruta", width=400)
        self.tabla.column("Nombre", width=200)
        self.tabla.column("Tamaño", width=100)
        self.tabla.column("Tipo", width=100)
        
        self.tabla.grid(row=0, column=0, sticky='nsew')

        # SCROLLBAR
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        # FRAME DE PREVISUALIZACIÓN
        preview_frame = ttk.Frame(contenedor, width=350)
        preview_frame.grid(row=0, column=2, padx=(10,0), sticky='n')
        
        # ETIQUETA DE PREVISUALIZACIÓN
        self.thumbnail_label = tk.Label( 
            preview_frame, 
            text='Previsualización\n(Haga click en un archivo)',
            anchor='center', 
            background='#f0f0f0', 
            width=35, 
            height=5, 
            relief=tk.SUNKEN 
        )
        self.thumbnail_label.pack(pady=5, padx=5) 

        # Configuración de Expansión del Contenedor
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        # Tags para estilos
        self.tabla.tag_configure('grupo', background='#e0e0e0', font=('Arial', 10, 'bold'))
        self.tabla.tag_configure('archivo', background='#ffffff', font=('Arial', 10))


        # --- 4. Botones de acción principal ---
        frame_botones = ttk.Frame(self.ventana)
        frame_botones.pack(pady=5)

        self.boton_eliminar_auto = ttk.Button(frame_botones, text="🗑️ Eliminar duplicados autom.", command=self.eliminar_duplicados_automatico)
        self.boton_eliminar_auto.grid(row=0, column=0, padx=10)

        self.boton_mover = ttk.Button(frame_botones, text="📂 Mover duplicados a 'borrar'", command=self.mover_duplicados_a_carpeta)
        self.boton_mover.grid(row=0, column=1, padx=10)
        
        self.boton_mover_imagenes = ttk.Button(frame_botones, text="🖼️ Mover imágenes (todos) a 'extraidas'", command=self.mover_imagenes_a_carpeta)
        self.boton_mover_imagenes.grid(row=0, column=2, padx=10)
        
        self.boton_refrescar = ttk.Button(frame_botones, text="🔄 Refrescar resultados", command=self.refrescar_resultados)
        self.boton_refrescar.grid(row=0, column=3, padx=10)
        
        self.boton_comparar = ttk.Button(frame_botones, text="🆚 Comparar y eliminar entre carpetas", command=self.comparar_y_eliminar_entre_carpetas)
        self.boton_comparar.grid(row=0, column=4, padx=10)

        # --- 5. Botones de acción avanzada (Prefijo) ---
        frame_prefijo = ttk.Frame(self.ventana)
        frame_prefijo.pack(pady=10)

        ttk.Label(frame_prefijo, text="Prefijo de imagen a eliminar:").grid(row=0, column=0, padx=5)
        self.entrada_prefijo = ttk.Entry(frame_prefijo, width=20)
        self.entrada_prefijo.grid(row=0, column=1, padx=5)

        self.boton_eliminar_prefijo = ttk.Button(
            frame_prefijo,
            text="🗑️ Eliminar imágenes con prefijo",
            command=self.eliminar_imagenes_por_prefijo
        )
        self.boton_eliminar_prefijo.grid(row=0, column=2, padx=5)

    def _configurar_eventos(self):
        """Configura los eventos de doble click y selección de la tabla."""
        self.tabla.bind("<Double-1>", self.abrir_archivo)
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_thumbnail)