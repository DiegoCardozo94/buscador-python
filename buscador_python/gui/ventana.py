import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from core import duplicados, archivos, imagenes
from utils import sistema

class VentanaDuplicados:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Buscador de duplicados (Automático)")
        self.ventana.geometry("1000x660")

        self.duplicados_global = {}

        self._crear_widgets()
        self._configurar_eventos()

    def _crear_widgets(self):
        frame = ttk.Frame(self.ventana, padding=10)
        frame.pack(fill='x')

        self.entrada_carpeta = ttk.Entry(frame, width=70)
        self.entrada_carpeta.grid(row=0, column=0, padx=5)

        self.boton_explorar = ttk.Button(frame, text="Seleccionar carpeta", command=self.seleccionar_carpeta)
        self.boton_explorar.grid(row=0, column=1, padx=5)

        self.progress_bar = ttk.Progressbar(self.ventana, mode='determinate')
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        contenedor = ttk.Frame(self.ventana)
        contenedor.pack(fill='both', expand=True, padx=10, pady=10)

        self.tabla = ttk.Treeview(contenedor, columns=("Ruta", "Nombre", "Tamaño", "Tipo"), show='headings', height=20)
        self.tabla.heading("Ruta", text="Ruta del archivo")
        self.tabla.heading("Nombre", text="Nombre")
        self.tabla.heading("Tamaño", text="Tamaño")
        self.tabla.heading("Tipo", text="Tipo")
        self.tabla.column("Ruta", width=500)
        self.tabla.column("Nombre", width=200)
        self.tabla.column("Tamaño", width=100)
        self.tabla.column("Tipo", width=80)
        self.tabla.grid(row=0, column=0, sticky='nsew')

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        preview_frame = ttk.Frame(contenedor, width=200)
        preview_frame.grid(row=0, column=2, padx=(10,0), sticky='n')

        self.thumbnail_label = ttk.Label(preview_frame, text='Previsualización', anchor='center')
        self.thumbnail_label.pack()

        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        self.tabla.tag_configure('grupo', background='#e0e0e0', font=('Arial', 10, 'bold'))
        self.tabla.tag_configure('archivo', background='#ffffff', font=('Arial', 10))

        frame_botones = ttk.Frame(self.ventana)
        frame_botones.pack(pady=5)

        self.contador_label = ttk.Label(self.ventana, text="Archivos escaneados: 0")
        self.contador_label.pack()

        self.boton_eliminar_auto = ttk.Button(frame_botones, text="Eliminar duplicados automáticamente", command=self.eliminar_duplicados_automatico)
        self.boton_eliminar_auto.grid(row=0, column=0, padx=10)

        self.boton_comparar = ttk.Button(frame_botones, text="Eliminar duplicados entre carpetas", command=self.comparar_y_eliminar_entre_carpetas)
        self.boton_comparar.grid(row=0, column=4, padx=10)

        self.boton_mover = ttk.Button(frame_botones, text="Mover duplicados a carpeta 'archivos a borrar'", command=self.mover_duplicados_a_carpeta)
        self.boton_mover.grid(row=0, column=1, padx=10)

        self.boton_mover_imagenes = ttk.Button(frame_botones, text="Mover imágenes a 'imagenes extraidas'", command=self.mover_imagenes_a_carpeta)
        self.boton_mover_imagenes.grid(row=0, column=2, padx=10)

        self.boton_refrescar = ttk.Button(frame_botones, text="Refrescar resultados", command=self.refrescar_resultados)
        self.boton_refrescar.grid(row=0, column=3, padx=10)

        frame_prefijo = ttk.Frame(self.ventana)
        frame_prefijo.pack(pady=10)

        ttk.Label(frame_prefijo, text="Prefijo de imagen a eliminar:").grid(row=0, column=0, padx=5)
        self.entrada_prefijo = ttk.Entry(frame_prefijo, width=20)
        self.entrada_prefijo.grid(row=0, column=1, padx=5)

        self.boton_eliminar_prefijo = ttk.Button(
            frame_prefijo,
            text="Eliminar imágenes con prefijo",
            command=self.eliminar_imagenes_por_prefijo
        )
        self.boton_eliminar_prefijo.grid(row=0, column=2, padx=5)

    def comparar_y_eliminar_entre_carpetas(self):
        carpeta_a = self.entrada_carpeta.get()
        if not carpeta_a or not os.path.isdir(carpeta_a):
            messagebox.showwarning("Error", "Selecciona una carpeta A válida.")
            return

        carpeta_b = filedialog.askdirectory(title="Selecciona la carpeta B para comparar")
        if not carpeta_b or not os.path.isdir(carpeta_b):
            return

        confirmar = messagebox.askyesno("Comparar y eliminar duplicados",
            f"¿Deseas comparar los archivos de:\n\nA: {carpeta_a}\nB: {carpeta_b}\n\nY eliminar duplicados encontrados en B?\n\nLos archivos duplicados en A y B serán eliminados SOLO en B.")

        if not confirmar:
            return

        threading.Thread(target=self._comparar_y_eliminar_tarea, args=(carpeta_a, carpeta_b), daemon=True).start()
    
    def _comparar_y_eliminar_tarea(self, carpeta_a, carpeta_b):
        self.progress_bar["value"] = 0
        self.contador_label.config(text="Comparando hashes entre carpetas...")
        self.ventana.update_idletasks()

        from core import duplicados

        hashes_a, _ = duplicados.escanear_y_hash(carpeta_a)
        hashes_b, _ = duplicados.escanear_y_hash(carpeta_b)

        # Crear sets para comparación rápida
        hash_set_a = set(hashes_a.keys())
        duplicados_en_b = [archivo for h, archivo in hashes_b.items() if h in hash_set_a]

        # Filtrar duplicados válidos
        duplicados_validos = [d for d in duplicados_en_b if isinstance(d, list) and len(d) > 1]

        if not duplicados_validos:
            messagebox.showinfo("Resultado", "No se encontraron duplicados entre las carpetas.")
            return

        # Si hay duplicados válidos, armar el resumen
        resumen = "\n".join([
            os.path.basename(r[0]) for r in duplicados_validos[:10] if r and isinstance(r, list) and isinstance(r[0], str)
        ])

        if len(duplicados_validos) > 10:
            resumen += f"\n...y {len(duplicados_validos) - 10} más"

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"Se eliminarán {len(duplicados_validos)} archivos duplicados de la carpeta B:\n\n{resumen}\n\n¿Continuar?"
        )
        if not confirmar:
            return

        errores = []
        self.progress_bar["maximum"] = len(duplicados_en_b)
        self.ventana.update_idletasks()

        for i, ruta in enumerate(duplicados_en_b, 1):
            error = sistema.eliminar_archivo(ruta)
            if error:
                errores.append(error)
            self.progress_bar["value"] = i
            self.ventana.update_idletasks()

        if errores:
            messagebox.showwarning("Errores", f"No se pudieron eliminar {len(errores)} archivos.")
        else:
            messagebox.showinfo("Hecho", f"Se eliminaron {len(duplicados_en_b)} archivos duplicados de la carpeta B.")

        self.seleccionar_carpeta()


    def _configurar_eventos(self):
        self.tabla.bind("<Double-1>", self.abrir_archivo)
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_thumbnail)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.entrada_carpeta.delete(0, tk.END)
            self.entrada_carpeta.insert(0, carpeta)
            threading.Thread(target=self.buscar_duplicados, args=(carpeta,), daemon=True).start()

    def actualizar_progreso(self, contador, total):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = contador
        self.contador_label.config(text=f"Archivos escaneados: {contador}/{total}")
        self.ventana.update_idletasks()

    def buscar_duplicados(self, carpeta):
        self.tabla.delete(*self.tabla.get_children())
        hashes, errores = duplicados.escanear_y_hash(carpeta, progress_callback=self.actualizar_progreso)
        self.duplicados_global = duplicados.filtrar_duplicados(hashes)

        for grupo_hash, lista_archivos in self.duplicados_global.items():
            self.tabla.insert("", tk.END, values=(f"Grupo ({len(lista_archivos)} duplicados)", "", "", ""), tags=('grupo',))
            for archivo in lista_archivos:
                try:
                    tamaño = os.path.getsize(archivo)
                except Exception:
                    tamaño = 0
                tipo = "Imagen" if archivo.lower().endswith(archivos.EXT_IMAGENES) else "Video"
                self.tabla.insert("", tk.END, values=(archivo, os.path.basename(archivo), f"{tamaño/1024:.1f} KB", tipo), tags=('archivo',))

    def abrir_archivo(self, event):
        item = self.tabla.identify_row(event.y)
        if item:
            ruta = self.tabla.item(item)['values'][0]
            if os.path.isfile(ruta):
                abierto = imagenes.abrir_archivo_sistema(ruta)
                if not abierto:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{ruta}")

    def mostrar_thumbnail(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            self.thumbnail_label.config(image='', text='Previsualización')
            return
        ruta = self.tabla.item(seleccion[0])['values'][0]
        if not os.path.isfile(ruta):
            self.thumbnail_label.config(image='', text='No disponible')
            return

        try:
            tamaño_bytes = os.path.getsize(ruta)

            if ruta.lower().endswith(archivos.EXT_IMAGENES):
                if tamaño_bytes > 20 * 1024 * 1024:
                    self.thumbnail_label.config(image='', text='Imagen > 20MB')
                    return
                img = Image.open(ruta)
                img.thumbnail((200, 200))
                img_tk = ImageTk.PhotoImage(img)
                self.thumbnail_label.image = img_tk
                self.thumbnail_label.config(image=img_tk, text='')

            elif ruta.lower().endswith(archivos.EXT_VIDEOS):
                if tamaño_bytes < 10 * 1024 * 1024:
                    self.thumbnail_label.config(image='', text='Video < 10MB')
                    return
                img = imagenes.obtener_thumbnail_video(ruta)
                if img:
                    img_tk = ImageTk.PhotoImage(img)
                    self.thumbnail_label.image = img_tk
                    self.thumbnail_label.config(image=img_tk, text='')
                else:
                    self.thumbnail_label.config(image='', text='No disponible')

            else:
                self.thumbnail_label.config(image='', text='No disponible')

        except Exception as e:
            self.thumbnail_label.config(image='', text='Error al cargar')
            print(f"Error al mostrar thumbnail: {e}")

    def eliminar_duplicados_automatico(self):
        if not self.duplicados_global:
            messagebox.showinfo("Info", "No hay duplicados cargados.")
            return

        archivos_a_eliminar = []
        for grupo in self.duplicados_global.values():
            archivos_a_eliminar.extend(grupo[1:])  # dejar el primero

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

        errores = []

        def eliminar_tarea():
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(sistema.eliminar_archivo, ruta): ruta for ruta in archivos_a_eliminar}
                for i, future in enumerate(as_completed(futures), 1):
                    error = future.result()
                    if error:
                        errores.append(error)
                    self.progress_bar["value"] = i
                    self.ventana.update_idletasks()

            if errores:
                messagebox.showwarning("Errores", f"No se pudieron eliminar {len(errores)} archivos:\n" + "\n".join(errores[:10]))
            else:
                messagebox.showinfo("Hecho", f"Se eliminaron {len(archivos_a_eliminar)} archivos duplicados.")

            self.seleccionar_carpeta()

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
            archivos_a_mover.extend(grupo[1:])  # dejar el primero

        if not archivos_a_mover:
            messagebox.showinfo("Nada que mover", "No hay duplicados para mover.")
            return

        resumen = "\n".join([os.path.basename(r) for r in archivos_a_mover[:10]])
        if len(archivos_a_mover) > 10:
            resumen += f"\n...y {len(archivos_a_mover) - 10} más"

        confirmar = messagebox.askyesno(
            "Mover duplicados",
            f"Se moverán {len(archivos_a_mover)} archivos a:\n{carpeta_destino}\n\nEjemplos:\n{resumen}\n\n¿Continuar?"
        )
        if not confirmar:
            return

        self.progress_bar["maximum"] = len(archivos_a_mover)
        self.progress_bar["value"] = 0
        self.ventana.update_idletasks()

        errores = []

        def mover_tarea():
            for i, ruta in enumerate(archivos_a_mover, 1):
                destino = os.path.join(carpeta_destino, os.path.basename(ruta))
                error = sistema.mover_archivo(ruta, destino)
                if error:
                    errores.append(error)
                self.progress_bar["value"] = i
                self.ventana.update_idletasks()

            if errores:
                messagebox.showwarning("Errores", f"No se pudieron mover {len(errores)} archivos.")
            else:
                messagebox.showinfo("Hecho", f"Se movieron {len(archivos_a_mover)} archivos a '{carpeta_destino}'.")

            self.seleccionar_carpeta()

        threading.Thread(target=mover_tarea, daemon=True).start()

    def mover_imagenes_a_carpeta(self):
        carpeta_raiz = self.entrada_carpeta.get()
        if not carpeta_raiz or not os.path.isdir(carpeta_raiz):
            messagebox.showwarning("Error", "Selecciona una carpeta válida.")
            return

        carpeta_destino = os.path.join(carpeta_raiz, "imagenes extraidas")
        os.makedirs(carpeta_destino, exist_ok=True)

        imagenes = archivos.encontrar_archivos(carpeta_raiz, archivos.EXT_IMAGENES)

        if not imagenes:
            messagebox.showinfo("Sin imágenes", "No se encontraron imágenes para mover.")
            return

        resumen = "\n".join([os.path.basename(r) for r in imagenes[:10]])
        if len(imagenes) > 10:
            resumen += f"\n...y {len(imagenes) - 10} más"

        confirmar = messagebox.askyesno(
            "Mover imágenes",
            f"Se moverán {len(imagenes)} imágenes a:\n{carpeta_destino}\n\nEjemplos:\n{resumen}\n\n¿Continuar?"
        )
        if not confirmar:
            return

        self.progress_bar["maximum"] = len(imagenes)
        self.progress_bar["value"] = 0
        self.ventana.update_idletasks()

        errores = []

        def mover_imagenes_tarea():
            for i, ruta in enumerate(imagenes, 1):
                destino = os.path.join(carpeta_destino, os.path.basename(ruta))
                error = sistema.mover_archivo(ruta, destino)
                if error:
                    errores.append(error)
                self.progress_bar["value"] = i
                self.ventana.update_idletasks()

            if errores:
                messagebox.showwarning("Errores", f"No se pudieron mover {len(errores)} imágenes.")
            else:
                messagebox.showinfo("Hecho", f"Se movieron {len(imagenes)} imágenes a '{carpeta_destino}'.")

            self.seleccionar_carpeta()

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

        imagenes = archivos.encontrar_archivos(carpeta, archivos.EXT_IMAGENES)
        candidatas = [ruta for ruta in imagenes if os.path.basename(ruta).startswith(prefijo)]

        if not candidatas:
            messagebox.showinfo("Sin coincidencias", f"No se encontraron imágenes que empiecen con '{prefijo}'.")
            return

        resumen = "\n".join([os.path.basename(r) for r in candidatas[:10]])
        if len(candidatas) > 10:
            resumen += f"\n...y {len(candidatas) - 10} más"

        confirmar = messagebox.askyesno(
            "Eliminar imágenes por prefijo",
            f"Se eliminarán {len(candidatas)} imágenes que empiezan con '{prefijo}':\n\n{resumen}\n\n¿Continuar?"
        )
        if not confirmar:
            return

        self.progress_bar["maximum"] = len(candidatas)
        self.progress_bar["value"] = 0
        self.ventana.update_idletasks()

        errores = []

        def eliminar_tarea():
            for i, ruta in enumerate(candidatas, 1):
                error = sistema.eliminar_archivo(ruta)
                if error:
                    errores.append(error)
                self.progress_bar["value"] = i
                self.ventana.update_idletasks()

            if errores:
                messagebox.showwarning("Errores", f"No se pudieron eliminar {len(errores)} archivos.")
            else:
                messagebox.showinfo("Hecho", f"Se eliminaron {len(candidatas)} imágenes que empezaban con '{prefijo}'.")

            self.seleccionar_carpeta()

        threading.Thread(target=eliminar_tarea, daemon=True).start()

    def refrescar_resultados(self):
        carpeta = self.entrada_carpeta.get()
        if carpeta and os.path.isdir(carpeta):
            threading.Thread(target=self.buscar_duplicados, args=(carpeta,), daemon=True).start()

def iniciar_ventana():
    app = VentanaDuplicados()
    app.ventana.mainloop()
