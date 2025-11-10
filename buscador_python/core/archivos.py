import os

EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')
EXTENSIONES_VALIDAS = EXT_IMAGENES + EXT_VIDEOS

def crear_info_archivo(ruta, tamaño):
    """Crea un diccionario de información básica del archivo."""
    return {
        'ruta': ruta,
        'tamaño': tamaño,
    }

def encontrar_archivos(carpeta, extensiones=EXTENSIONES_VALIDAS, limite=None):
    """
    Escanea la carpeta recursivamente y devuelve una lista de diccionarios 
    con la ruta y el tamaño de los archivos multimedia válidos.
    """
    archivos_info = []
    
    # Manejo de casos en que la carpeta no existe o no es accesible
    if not os.path.isdir(carpeta):
        # Podrías agregar un log o lanzar una excepción más específica aquí
        return archivos_info

    for raiz, _, nombres in os.walk(carpeta):
        for nombre in nombres:
            if nombre.lower().endswith(extensiones):
                ruta = os.path.join(raiz, nombre)
                
                try:
                    # Intenta obtener el tamaño y manejar errores de acceso/permisos
                    tamaño = os.path.getsize(ruta)
                except (FileNotFoundError, PermissionError):
                    # Ignorar archivos que no se pueden acceder
                    continue

                ext = nombre.lower()
                # Aplicar filtro de tamaño para videos (< 1MB se ignoran)
                if ext.endswith(EXT_VIDEOS):
                    if tamaño < 1 * 1024 * 1024:
                        continue

                # Almacenar la información estructurada
                archivos_info.append(crear_info_archivo(ruta, tamaño))
                
                if limite and len(archivos_info) >= limite:
                    return archivos_info
    return archivos_info