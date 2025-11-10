import os
import hashlib
import json

MAX_BYTES_PARCIAL = 1024 * 1024 # 1 MB para hashing parcial (Renombrado para claridad)
CHUNK_SIZE = 8192 # Tamaño de bloque para lectura

def hash_completo(path):
    """Calcula el hash MD5 leyendo todo el archivo. Usado para verificación final."""
    try:
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (FileNotFoundError, PermissionError, IOError):
        # Captura errores de I/O específicos
        return None
    except Exception:
        # Otros errores inesperados
        return None


def hash_parcial(path, max_bytes=MAX_BYTES_PARCIAL):
    """
    Calcula el hash MD5 leyendo solo los primeros `max_bytes` del archivo.
    Usado para filtrar rápidamente no-duplicados.
    """
    try:
        hash_md5 = hashlib.md5()
        bytes_leidos = 0
        
        with open(path, "rb") as f:
            while bytes_leidos < max_bytes:
                # Leer un bloque, asegurando no exceder max_bytes
                bytes_a_leer = min(CHUNK_SIZE, max_bytes - bytes_leidos)
                chunk = f.read(bytes_a_leer)
                
                # Si no se leyó nada, es el final del archivo
                if not chunk:
                    break
                    
                hash_md5.update(chunk)
                bytes_leidos += len(chunk)

        return hash_md5.hexdigest()
    except (FileNotFoundError, PermissionError, IOError):
        return None
    except Exception:
        return None

def cargar_cache(cache_path):
    """Carga los datos de caché desde un archivo JSON."""
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            # Captura errores de I/O o si el JSON está corrupto
            return {}
    return {}

def guardar_cache(cache_path, cache_data):
    """Guarda los datos de caché a un archivo JSON."""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        # Se mantiene la impresión del error para notificar al desarrollador o usuario
        print(f"Error al guardar caché: {e}")