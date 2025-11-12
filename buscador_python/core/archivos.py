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

def encontrar_archivos(carpeta_raiz, extensiones_validas, limite=None):
    archivos_encontrados = []
    
    for dirpath, dirnames, filenames in os.walk(carpeta_raiz):
        for nombre_archivo in filenames:
            ruta_completa = os.path.join(dirpath, nombre_archivo)
            
            _, ext = os.path.splitext(nombre_archivo)
            ext = ext.lower()
            
            if ext in extensiones_validas:
                
                # --- CORRECCIÓN CLAVE AQUÍ ---
                try:
                    # 1. Obtener el tamaño del archivo
                    tamano_bytes = os.path.getsize(ruta_completa)
                except Exception:
                    # Manejar archivos inaccesibles o rotos
                    tamano_bytes = 0 
                # ------------------------------
                
                archivos_encontrados.append({
                    'ruta': ruta_completa,
                    'nombre': nombre_archivo,
                    # 2. Asignar la clave 'tamaño' (en minúsculas)
                    'tamaño': tamano_bytes,
                    # Nota: El KeyError original usa 'tamaño' con ñ. Si tu código usa 'tamano'
                    # (sin ñ), ajusta la clave en escanear_y_hash o aquí.
                })
                
                # Opcional: Implementar el límite de archivos si limite no es None
                if limite is not None and len(archivos_encontrados) >= limite:
                    return archivos_encontrados
    
    return archivos_encontrados