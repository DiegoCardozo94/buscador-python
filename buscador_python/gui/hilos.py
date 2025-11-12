import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageTk

# Asegúrate de que estos módulos estén disponibles en el entorno
from core import duplicados, archivos, imagenes
from utils import sistema

class HilosMixin:
    """
    Contiene la lógica para el escaneo, manejo de hilos, y las acciones
    de gestión de archivos (eliminar, mover, etc.).
    
    NOTA: Se asume que los métodos format_bytes, _actualizar_progreso_eliminacion, 
    _actualizar_estado_botones, y las referencias a widgets (self.tabla, etc.)
    están disponibles a través de la clase base y EstadoMixin.
    """
    
    # --- Lógica de Escaneo ---

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.entrada_carpeta.delete(0, tk.END)
            self.entrada_carpeta.insert(0, carpeta)
            
            # Limpiar la tabla de resultados antiguos
            self.ventana.after(0, self.tabla.delete, *self.tabla.get_children())
            
            # Deshabilitar botones al inicio (definido en EstadoMixin)
            self._actualizar_estado_botones(escaneando=True)
            
            # Iniciar la búsqueda en un hilo separado
            threading.Thread(target=self.buscar_duplicados, args=(carpeta,), daemon=True).start()

    def buscar_duplicados(self, carpeta):
        # Preparar la GUI en el hilo principal
        self.ventana.after(0, self.contador_label.config, {'text': "Buscando duplicados..."})
        
        # Ejecutar la tarea pesada
        hashes, errores = duplicados.escanear_y_hash(carpeta, progress_callback=self.actualizar_progreso)
        self.duplicados_global = duplicados.filtrar_duplicados(hashes)

        # Llamar al callback de actualización final de la tabla y botones
        self.ventana.after(0, self._finalizar_escaneo, errores)
        
    def _finalizar_escaneo(self, errores):
        """Callback ejecutado en el hilo principal después de la búsqueda."""
        self._actualizar_tabla(errores)
        
        # Habilitar/Deshabilitar botones
        self._actualizar_estado_botones(escaneando=False) 
        
    def _actualizar_tabla(self, errores):
        """Inserta los resultados de duplicados_global en el Treeview."""
        
        for grupo_hash, lista_archivos in self.duplicados_global.items():
            # Insertar la fila de grupo (padre)
            self.tabla.insert("", tk.END, values=(f"Grupo ({len(lista_archivos)} duplicados)", "", "", ""), tags=('grupo',))
            
            for archivo in lista_archivos:
                try:
                    tamaño = os.path.getsize(archivo)
                except Exception:
                    tamaño = 0

                ext_archivo = os.path.splitext(archivo)[1].lower()
                
                # Lógica para determinar el tipo
                if ext_archivo in archivos.EXT_IMAGENES:
                    tipo = "Imagen"
                elif ext_archivo in archivos.EXT_VIDEOS:
                    tipo = "Video"
                else:
                    tipo = "Otro"
                
                # Formato de tamaño (método del EstadoMixin)
                tamaño_formateado = self.format_bytes(tamaño)
                
                # Insertar la fila del archivo (hijo)
                self.tabla.insert("", tk.END, values=(archivo, os.path.basename(archivo), tamaño_formateado, tipo), tags=('archivo',))
        
        if errores:
            messagebox.showwarning("Errores de escaneo", f"No se pudieron leer {len(errores)} archivos (permisos/inexistentes).")

    # --- Lógica de Thumbnail y Eventos Simples ---
    
    def abrir_archivo(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            ruta = self.tabla.item(item)['values'][0]
            if os.path.isfile(ruta):
                abierto = imagenes.abrir_archivo(ruta)
                if not abierto:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{ruta}")

    def mostrar_thumbnail(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            self.thumbnail_label.config(image='', text='Previsualización\n(Haga click en un archivo)')
            return
            
        ruta = self.tabla.item(seleccion[0])['values'][0]
        if not os.path.isfile(ruta):
            self.thumbnail_label.config(image='', text='No disponible')
            return

        self.thumbnail_label.config(image='', text='Cargando...')
        self.ventana.update_idletasks()
        
        threading.Thread(target=self._cargar_thumbnail_tarea, args=(ruta,), daemon=True).start()

    def _cargar_thumbnail_tarea(self, ruta):
            """Genera el thumbnail en un hilo y lo actualiza en la GUI."""
            try:
                # 1. Tarea pesada (obtener y redimensionar la imagen) en el hilo de trabajo
                img = imagenes.obtener_thumbnail(ruta)
                
                if img:
                    # 2. Convertir la imagen a formato Tkinter (aún en el hilo de trabajo)
                    img_tk = ImageTk.PhotoImage(img)
                    
                    # 3. Función de callback para el hilo principal (ejecuta la configuración y la asignación)
                    def actualizar_label():
                        self.current_thumbnail_tk = img_tk 
                        self.thumbnail_label.config(image=self.current_thumbnail_tk, text='')
                        
                    # 4. Enviar el callback al hilo principal
                    self.ventana.after(0, actualizar_label)
                else:
                    # Caso de error simple (se ejecuta en el hilo principal)
                    self.ventana.after(0, self.thumbnail_label.config, {'image': '', 'text': 'No disponible\n(Error o video muy grande)'})
                    
            except Exception as e:
                # Manejo de excepciones (se ejecuta en el hilo principal)
                self.ventana.after(0, self.thumbnail_label.config, {'image': '', 'text': 'Error al cargar'})
                print(f"Error al mostrar thumbnail: {e}")

    # --- Lógica de Acción (Eliminar / Mover / Comparar, etc.) ---
    
    def eliminar_duplicados_automatico(self):
        if not self.duplicados_global:
            messagebox.showinfo("Info", "No hay duplicados cargados.")
            return

        archivos_a_eliminar = []
        for grupo in self.duplicados_global.values():
            archivos_a_eliminar.extend(grupo[1:])
            
        if not archivos_a_eliminar:
            messagebox.showinfo("Nada que eliminar", "No hay duplicados para eliminar.")
            return
            
        resumen = "\n".join([os.path.basename(r) for r in archivos_a_eliminar[:10]])
        if len(archivos_a_eliminar) > 10:
            resumen += f"\n...y {len(archivos_a_eliminar) - 10} más"
            
        confirmar = messagebox.askyesno("Eliminar duplicados",
            f"Se eliminarán {len(archivos_a_eliminar)} archivos, dejando solo uno por grupo.\n\nEjemplos:\n{resumen}\n\n¿Continuar?")

        if not confirmar:
            return

        self.progress_bar["maximum"] = len(archivos_a_eliminar)
        self.progress_bar["value"] = 0
        self.ventana.update_idletasks()
        
        def eliminar_tarea():
            errores = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(sistema.eliminar_archivo, ruta): ruta for ruta in archivos_a_eliminar}
                for i, future in enumerate(as_completed(futures), 1):
                    error = future.result()
                    if error:
                        errores.append(error)
                    self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(archivos_a_eliminar)) 

            self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se eliminaron {len(archivos_a_eliminar) - len(errores)} archivos duplicados."))
            self.ventana.after(0, self.seleccionar_carpeta) # Refrescar la vista
        
        threading.Thread(target=eliminar_tarea, daemon=True).start()

    def mover_duplicados_a_carpeta(self):
        if not self.duplicados_global:
            messagebox.showinfo("Info", "No hay duplicados cargados.")
            return

        carpeta_raiz = self.entrada_carpeta.get()
        carpeta_destino = os.path.join(carpeta_raiz, "archivos a borrar")
        os.makedirs(carpeta_destino, exist_ok=True)

        archivos_a_mover = []
        for grupo in self.duplicados_global.values():
            archivos_a_mover.extend(grupo[1:])
            
        if not archivos_a_mover:
            messagebox.showinfo("Nada que mover", "No hay duplicados para mover.")
            return

        def mover_tarea():
            errores = []
            for i, ruta in enumerate(archivos_a_mover, 1):
                destino = os.path.join(carpeta_destino, os.path.basename(ruta))
                error = sistema.mover_archivo(ruta, destino)
                if error:
                    errores.append(error)
                self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(archivos_a_mover))

            self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se movieron {len(archivos_a_mover) - len(errores)} archivos a '{carpeta_destino}'."))
            self.ventana.after(0, self.seleccionar_carpeta)

        threading.Thread(target=mover_tarea, daemon=True).start()
    
    def mover_videos_a_carpeta(self):
        carpeta_raiz = self.entrada_carpeta.get()
        if not carpeta_raiz or not os.path.isdir(carpeta_raiz):
            messagebox.showwarning("Error", "Selecciona una carpeta válida.")
            return

        carpeta_destino = os.path.join(carpeta_raiz, "videos extraidos")
        os.makedirs(carpeta_destino, exist_ok=True)

        # Usar archivos.EXT_VIDEOS para encontrar los archivos
        videos_info = archivos.encontrar_archivos(carpeta_raiz, archivos.EXT_VIDEOS)
        videos_a_mover = [info['ruta'] for info in videos_info]
        
        if not videos_a_mover:
            messagebox.showinfo("Sin videos", "No se encontraron videos para mover.")
            return
            
        confirmar = messagebox.askyesno("Mover Videos",
            f"Se moverán {len(videos_a_mover)} videos de la carpeta principal a la subcarpeta '{os.path.basename(carpeta_destino)}'.\n\n¿Continuar?")
        
        if not confirmar:
            return

        # Preparar la barra de progreso
        self.progress_bar["maximum"] = len(videos_a_mover)
        self.progress_bar["value"] = 0
        self.ventana.update_idletasks()

        def mover_videos_tarea():
            errores = []
            for i, ruta in enumerate(videos_a_mover, 1):
                # Usar sistema.mover_archivo, asegurando que el nombre de archivo sea único si ya existe
                destino = os.path.join(carpeta_destino, os.path.basename(ruta))
                error = sistema.mover_archivo(ruta, destino)
                if error:
                    errores.append(error)
                self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(videos_a_mover))

            self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se movieron {len(videos_a_mover) - len(errores)} videos a '{carpeta_destino}'."))
            self.ventana.after(0, self.seleccionar_carpeta)

        threading.Thread(target=mover_videos_tarea, daemon=True).start()

    def mover_imagenes_a_carpeta(self):
        carpeta_raiz = self.entrada_carpeta.get()
        if not carpeta_raiz or not os.path.isdir(carpeta_raiz):
            messagebox.showwarning("Error", "Selecciona una carpeta válida.")
            return

        carpeta_destino = os.path.join(carpeta_raiz, "imagenes extraidas")
        os.makedirs(carpeta_destino, exist_ok=True)

        imagenes_info = archivos.encontrar_archivos(carpeta_raiz, archivos.EXT_IMAGENES)
        imagenes_a_mover = [info['ruta'] for info in imagenes_info]
        
        if not imagenes_a_mover:
            messagebox.showinfo("Sin imágenes", "No se encontraron imágenes para mover.")
            return

        def mover_imagenes_tarea():
            errores = []
            for i, ruta in enumerate(imagenes_a_mover, 1):
                destino = os.path.join(carpeta_destino, os.path.basename(ruta))
                error = sistema.mover_archivo(ruta, destino)
                if error:
                    errores.append(error)
                self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(imagenes_a_mover))

            self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se movieron {len(imagenes_a_mover) - len(errores)} imágenes a '{carpeta_destino}'."))
            self.ventana.after(0, self.seleccionar_carpeta)

        threading.Thread(target=mover_imagenes_tarea, daemon=True).start()
        
    def eliminar_imagenes_por_prefijo(self):
        prefijo = self.entrada_prefijo.get().strip()
        carpeta = self.entrada_carpeta.get()

        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning("Error", "Selecciona una carpeta válida.")
            return
        if not prefijo:
            messagebox.showwarning("Error", "Escribe un prefijo para buscar.")
            return

        imagenes_info = archivos.encontrar_archivos(carpeta, archivos.EXT_IMAGENES)
        candidatas_a_eliminar = [info['ruta'] for info in imagenes_info if os.path.basename(info['ruta']).startswith(prefijo)]

        if not candidatas_a_eliminar:
            messagebox.showinfo("Sin coincidencias", f"No se encontraron imágenes que empiecen con '{prefijo}'.")
            return

        def eliminar_tarea():
            errores = []
            for i, ruta in enumerate(candidatas_a_eliminar, 1):
                error = sistema.eliminar_archivo(ruta)
                if error:
                    errores.append(error)
                self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(candidatas_a_eliminar))

            self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se eliminaron {len(candidatas_a_eliminar) - len(errores)} imágenes que empezaban con '{prefijo}'."))
            self.ventana.after(0, self.seleccionar_carpeta)

        threading.Thread(target=eliminar_tarea, daemon=True).start()

    def comparar_y_eliminar_entre_carpetas(self):
        carpeta_a = self.entrada_carpeta.get()
        if not carpeta_a or not os.path.isdir(carpeta_a):
            messagebox.showwarning("Error", "Selecciona una carpeta A válida.")
            return

        carpeta_b = filedialog.askdirectory(title="Selecciona la carpeta B para comparar")
        if not carpeta_b or not os.path.isdir(carpeta_b):
            return

        confirmar = messagebox.askyesno("Comparar y eliminar duplicados",
            f"¿Deseas comparar los archivos de:\n\nA: {os.path.basename(carpeta_a)}\nB: {os.path.basename(carpeta_b)}\n\nY eliminar duplicados encontrados en B?\n\nLos archivos duplicados en A y B serán eliminados SOLO en B.")

        if not confirmar:
            return

        threading.Thread(target=self._comparar_y_eliminar_tarea, args=(carpeta_a, carpeta_b), daemon=True).start()
        
    def _comparar_y_eliminar_tarea(self, carpeta_a, carpeta_b):
        self.ventana.after(0, self.progress_bar.config, {'value': 0})
        self.ventana.after(0, self.contador_label.config, {'text': "Comparando hashes entre carpetas..."})
        self.ventana.update_idletasks()

        # 1. Escanear ambas carpetas
        hashes_a, _ = duplicados.escanear_y_hash(carpeta_a)
        hashes_b, _ = duplicados.escanear_y_hash(carpeta_b)

        hash_set_a = set(hashes_a.keys())
        
        # 2. Identificar duplicados en B
        duplicados_en_b_rutas = []
        for h, rutas_b in hashes_b.items():
            if h in hash_set_a:
                duplicados_en_b_rutas.extend(rutas_b) 

        if not duplicados_en_b_rutas:
            self.ventana.after(0, messagebox.showinfo, "Resultado", "No se encontraron duplicados entre las carpetas.")
            return

        # ... (Validación y confirmación en el hilo principal - Ya manejada por messagebox.askyesno arriba) ...
        # NOTA: La confirmación *DEBE* hacerse en el hilo principal. Como `askyesno` bloquea,
        # si se llamó dentro de `_comparar_y_eliminar_tarea` (que está en un hilo), 
        # funcionará, pero no es la práctica ideal. Para simplificar, asumiremos que
        # la confirmación ya fue hecha en `comparar_y_eliminar_entre_carpetas`.
        
        errores = []
        self.ventana.after(0, self.progress_bar.config, {'maximum': len(duplicados_en_b_rutas)})
        self.ventana.update_idletasks()

        # 3. Eliminación
        for i, ruta in enumerate(duplicados_en_b_rutas, 1):
            error = sistema.eliminar_archivo(ruta)
            if error:
                errores.append(error)
            self.ventana.after(0, self._actualizar_progreso_eliminacion, i, len(duplicados_en_b_rutas))

        self.ventana.after(0, lambda: messagebox.showinfo("Hecho", f"Se eliminaron {len(duplicados_en_b_rutas) - len(errores)} archivos duplicados de la carpeta B."))
        
        # Refrescar la vista principal (de la carpeta A)
        self.ventana.after(0, self.seleccionar_carpeta)

    def refrescar_resultados(self):
        carpeta = self.entrada_carpeta.get()
        if carpeta and os.path.isdir(carpeta):
            # Llama a la lógica de escaneo principal
            threading.Thread(target=self.buscar_duplicados, args=(carpeta,), daemon=True).start()