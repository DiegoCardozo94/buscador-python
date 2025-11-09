import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import platform
import subprocess
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor, as_completed

# Extensiones separadas para facilitar control por tipo
EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')
EXTENSIONES_VALIDAS = EXT_IMAGENES + EXT_VIDEOS

MAX_BYTES = 1024 * 1024  # 1 MB para hashing parcial
MAX_HILOS = 4
MAX_ARCHIVOS = 200000

duplicados_global = {}

def hash_parcial(path, max_bytes=MAX_BYTES):
    try:
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            hash_md5.update(f.read(max_bytes))
        return hash_md5.hexdigest(), path
    except Exception:
        return None, path

def encontrar_archivos(carpeta, extensiones, limite=None):
    archivos = []
    for raiz, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if nombre.lower().endswith(extensiones):
                ruta = os.path.join(raiz, nombre)
                try:
                    tamaño = os.path.getsize(ruta)
                except Exception:
                    continue

                ext = nombre.lower()
                if ext.endswith(EXT_VIDEOS):
                    if tamaño < 1 * 1024 * 1024:  # Ignorar videos < 10MB
                        continue
                elif ext.endswith(EXT_IMAGENES):
                    pass  # Aceptar imágenes de cualquier tamaño (desde 0 bytes)

                archivos.append(ruta)
                if limite and len(archivos) >= limite:
                    return archivos
    return archivos

def escanear_y_hash(carpeta, max_hilos=MAX_HILOS, max_archivos=MAX_ARCHIVOS):
    archivos = encontrar_archivos(carpeta, EXTENSIONES_VALIDAS, limite=max_archivos)
    hashes = {}
    errores = []

    progress_bar["maximum"] = len(archivos)
    progress_bar["value"] = 0
    ventana.update_idletasks()

    with ThreadPoolExecutor(max_workers=max_hilos) as executor:
        tareas = [executor.submit(hash_parcial, path) for path in archivos]
        for i, future in enumerate(as_completed(tareas), 1):
            hash_valor, path = future.result()
            if hash_valor:
                hashes.setdefault(hash_valor, []).append(path)
            else:
                errores.append(path)
            progress_bar["value"] = i
            ventana.update_idletasks()

    return hashes, errores

def seleccionar_carpeta():
    carpeta = filedialog.askdirectory()
    if carpeta:
        entrada_carpeta.delete(0, tk.END)
        entrada_carpeta.insert(0, carpeta)
        buscar_duplicados(carpeta)

def buscar_duplicados(carpeta):
    global duplicados_global
    tabla.delete(*tabla.get_children())
    hashes, errores = escanear_y_hash(carpeta)
    duplicados_global = {h: r for h, r in hashes.items() if len(r) > 1}
    for grupo, archivos in duplicados_global.items():
        tabla.insert("", tk.END, values=(f"Grupo ({len(archivos)} duplicados)", "", ""), tags=('grupo',))
        for archivo in archivos:
            try:
                tamaño = os.path.getsize(archivo)
            except Exception:
                tamaño = 0
            tipo = "Imagen" if archivo.lower().endswith(EXT_IMAGENES) else "Video"
            tabla.insert("", tk.END, values=(archivo, os.path.basename(archivo), f"{tamaño/1024:.1f} KB", tipo), tags=('archivo',))


def eliminar_duplicados_automatico():
    if not duplicados_global:
        messagebox.showinfo("Info", "No hay duplicados cargados.")
        return

    archivos_a_eliminar = []
    for grupo in duplicados_global.values():
        archivos_a_eliminar.extend(grupo[1:])  # deja el primero

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

    progress_bar["maximum"] = len(archivos_a_eliminar)
    progress_bar["value"] = 0
    ventana.update_idletasks()

    errores = []
    for i, ruta in enumerate(archivos_a_eliminar, 1):
        try:
            os.remove(ruta)
        except Exception:
            errores.append(ruta)
        progress_bar["value"] = i
        ventana.update_idletasks()

    if errores:
        messagebox.showwarning("Errores", f"No se pudieron eliminar {len(errores)} archivos.")
    else:
        messagebox.showinfo("Hecho", f"Se eliminaron {len(archivos_a_eliminar)} archivos duplicados.")

    seleccionar_carpeta()

def mover_duplicados_a_carpeta():
    if not duplicados_global:
        messagebox.showinfo("Info", "No hay duplicados cargados.")
        return

    carpeta_raiz = entrada_carpeta.get()
    carpeta_destino = os.path.join(carpeta_raiz, "archivos a borrar")
    os.makedirs(carpeta_destino, exist_ok=True)

    archivos_a_mover = []
    for grupo in duplicados_global.values():
        archivos_a_mover.extend(grupo[1:])  # deja el primero

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

    errores = []
    for i, ruta in enumerate(archivos_a_mover, 1):
        try:
            destino = os.path.join(carpeta_destino, os.path.basename(ruta))
            nombre_base, ext = os.path.splitext(os.path.basename(ruta))
            contador = 1
            while os.path.exists(destino):
                destino = os.path.join(carpeta_destino, f"{nombre_base} ({contador}){ext}")
                contador += 1
            os.rename(ruta, destino)
        except Exception:
            errores.append(ruta)

        progress_bar["value"] = i
        ventana.update_idletasks()

    if errores:
        messagebox.showwarning("Errores", f"No se pudieron mover {len(errores)} archivos.")
    else:
        messagebox.showinfo("Hecho", f"Se movieron {len(archivos_a_mover)} archivos a '{carpeta_destino}'.")

    seleccionar_carpeta()

def mover_imagenes_a_carpeta():
    carpeta_raiz = entrada_carpeta.get()
    if not carpeta_raiz or not os.path.isdir(carpeta_raiz):
        messagebox.showwarning("Error", "Selecciona una carpeta válida.")
        return

    carpeta_destino = os.path.join(carpeta_raiz, "imagenes extraidas")
    os.makedirs(carpeta_destino, exist_ok=True)

    imagenes = encontrar_archivos(carpeta_raiz, EXT_IMAGENES)

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

    progress_bar["maximum"] = len(imagenes)
    progress_bar["value"] = 0
    ventana.update_idletasks()

    errores = []
    for i, ruta in enumerate(imagenes, 1):
        try:
            nombre_archivo = os.path.basename(ruta)
            destino = os.path.join(carpeta_destino, nombre_archivo)

            # Evita sobrescritura
            contador = 1
            nombre_base, ext = os.path.splitext(nombre_archivo)
            while os.path.exists(destino):
                destino = os.path.join(carpeta_destino, f"{nombre_base} ({contador}){ext}")
                contador += 1

            os.rename(ruta, destino)
        except Exception:
            errores.append(ruta)
        progress_bar["value"] = i
        ventana.update_idletasks()

    if errores:
        messagebox.showwarning("Errores", f"No se pudieron mover {len(errores)} imágenes.")
    else:
        messagebox.showinfo("Hecho", f"Se movieron {len(imagenes)} imágenes a '{carpeta_destino}'.")

    seleccionar_carpeta()


def abrir_archivo(event):
    item = tabla.identify_row(event.y)
    if item:
        ruta = tabla.item(item)['values'][0]
        if os.path.isfile(ruta):
            try:
                if platform.system() == "Windows":
                    os.startfile(ruta)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", ruta])
                else:
                    subprocess.run(["xdg-open", ruta])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir {ruta}:\n{e}")

def obtener_thumbnail_video(ruta):
    """
    Intenta extraer un fotograma para el thumbnail del video.
    Necesita 'ffmpeg' instalado en el sistema.
    """
    import tempfile
    import subprocess

    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmpfile:
            # Extraer fotograma en el segundo 1
            comando = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "00:00:01",
                "-i", ruta,
                "-frames:v", "1",
                "-q:v", "2",
                tmpfile.name
            ]
            subprocess.run(comando, check=True)
            img = Image.open(tmpfile.name)
            img.thumbnail((300, 300))
            return img
    except Exception:
        return None

def mostrar_thumbnail(event):
    item = tabla.selection()
    if not item:
        return
    ruta = tabla.item(item[0])['values'][0]
    if not os.path.isfile(ruta):
        thumbnail_label.config(image='', text='No disponible')
        return

    try:
        tamaño_bytes = os.path.getsize(ruta)

        if ruta.lower().endswith(EXT_IMAGENES):
            if tamaño_bytes > 20 * 1024 * 1024:  # > 20MB
                thumbnail_label.config(image='', text='Imagen > 20MB')
                return
            img = Image.open(ruta)
            img.thumbnail((200, 200))
            img_tk = ImageTk.PhotoImage(img)
            thumbnail_label.image = img_tk
            thumbnail_label.config(image=img_tk, text='')

        elif ruta.lower().endswith(EXT_VIDEOS):
            if tamaño_bytes < 10 * 1024 * 1024:  # < 10MB
                thumbnail_label.config(image='', text='Video < 10MB')
                return
            img = obtener_thumbnail_video(ruta)
            if img:
                img_tk = ImageTk.PhotoImage(img)
                thumbnail_label.image = img_tk
                thumbnail_label.config(image=img_tk, text='')
            else:
                thumbnail_label.config(image='', text='No disponible')

        else:
            thumbnail_label.config(image='', text='No disponible')

    except Exception as e:
        thumbnail_label.config(image='', text='Error al cargar')
        print(f"Error al mostrar thumbnail: {e}")

def eliminar_imagenes_por_prefijo(prefijo):
    carpeta = entrada_carpeta.get()
    if not carpeta or not os.path.isdir(carpeta):
        messagebox.showwarning("Error", "Selecciona una carpeta válida.")
        return

    if not prefijo:
        messagebox.showwarning("Error", "Escribe un prefijo para buscar.")
        return

    imagenes = encontrar_archivos(carpeta, EXT_IMAGENES)
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

    errores = []
    for i, ruta in enumerate(candidatas, 1):
        try:
            os.remove(ruta)
        except Exception:
            errores.append(ruta)
        progress_bar["value"] = i
        ventana.update_idletasks()

    if errores:
        messagebox.showwarning("Errores", f"No se pudieron eliminar {len(errores)} archivos.")
    else:
        messagebox.showinfo("Hecho", f"Se eliminaron {len(candidatas)} imágenes que empezaban con '{prefijo}'.")

    seleccionar_carpeta()

# GUI
ventana = tk.Tk()
ventana.title("Buscador de duplicados (Automático)")
ventana.geometry("1000x660")

frame = ttk.Frame(ventana, padding=10)
frame.pack(fill='x')

entrada_carpeta = ttk.Entry(frame, width=70)
entrada_carpeta.grid(row=0, column=0, padx=5)

boton_explorar = ttk.Button(frame, text="Seleccionar carpeta", command=seleccionar_carpeta)
boton_explorar.grid(row=0, column=1, padx=5)

progress_bar = ttk.Progressbar(ventana, mode='determinate')
progress_bar.pack(fill='x', padx=10, pady=5)

contenedor = ttk.Frame(ventana)
contenedor.pack(fill='both', expand=True, padx=10, pady=10)

tabla = ttk.Treeview(contenedor, columns=("Ruta", "Nombre", "Tamaño", "Tipo"), show='headings', height=20)
tabla.heading("Ruta", text="Ruta del archivo")
tabla.heading("Nombre", text="Nombre")
tabla.heading("Tamaño", text="Tamaño")
tabla.heading("Tipo", text="Tipo")
tabla.column("Ruta", width=500)
tabla.column("Nombre", width=200)
tabla.column("Tamaño", width=100)
tabla.column("Tipo", width=80)

tabla.grid(row=0, column=0, sticky='nsew')

scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
tabla.configure(yscroll=scrollbar.set)
scrollbar.grid(row=0, column=1, sticky='ns')

preview_frame = ttk.Frame(contenedor, width=200)
preview_frame.grid(row=0, column=2, padx=(10,0), sticky='n')

thumbnail_label = ttk.Label(preview_frame, text='Previsualización', anchor='center')
thumbnail_label.pack()

contenedor.columnconfigure(0, weight=1)
contenedor.rowconfigure(0, weight=1)

tabla.tag_configure('grupo', background='#e0e0e0', font=('Arial', 10, 'bold'))
tabla.tag_configure('archivo', background='#ffffff', font=('Arial', 10))

tabla.bind("<Double-1>", abrir_archivo)
tabla.bind("<<TreeviewSelect>>", mostrar_thumbnail)

frame_botones = ttk.Frame(ventana)
frame_botones.pack(pady=5)

boton_eliminar_auto = ttk.Button(frame_botones, text="Eliminar duplicados automáticamente", command=eliminar_duplicados_automatico)
boton_eliminar_auto.grid(row=0, column=0, padx=10)

boton_mover = ttk.Button(frame_botones, text="Mover duplicados a carpeta 'archivos a borrar'", command=mover_duplicados_a_carpeta)
boton_mover.grid(row=0, column=1, padx=10)

boton_mover_imagenes = ttk.Button(frame_botones, text="Mover imágenes a 'imagenes extraidas'", command=mover_imagenes_a_carpeta)
boton_mover_imagenes.grid(row=0, column=2, padx=10)

boton_refrescar = ttk.Button(frame_botones, text="Refrescar resultados", command=lambda: buscar_duplicados(entrada_carpeta.get()))
boton_refrescar.grid(row=0, column=3, padx=10)

# Nuevo campo para prefijo + botón eliminar
frame_prefijo = ttk.Frame(ventana)
frame_prefijo.pack(pady=10)

ttk.Label(frame_prefijo, text="Prefijo de imagen a eliminar:").grid(row=0, column=0, padx=5)
entrada_prefijo = ttk.Entry(frame_prefijo, width=20)
entrada_prefijo.grid(row=0, column=1, padx=5)

boton_eliminar_prefijo = ttk.Button(
    frame_prefijo,
    text="Eliminar imágenes con prefijo",
    command=lambda: eliminar_imagenes_por_prefijo(entrada_prefijo.get())
)
boton_eliminar_prefijo.grid(row=0, column=2, padx=5)

ventana.mainloop()
