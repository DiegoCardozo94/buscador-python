import os

EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')
EXTENSIONES_VALIDAS = EXT_IMAGENES + EXT_VIDEOS

def encontrar_archivos(carpeta, extensiones=EXTENSIONES_VALIDAS, limite=None):
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
                    if tamaño < 1 * 1024 * 1024:  # Ignorar videos < 1MB
                        continue
                # Para imágenes no hacemos filtro de tamaño

                archivos.append(ruta)
                if limite and len(archivos) >= limite:
                    return archivos
    return archivos
