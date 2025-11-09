import os
import hashlib
import json

MAX_BYTES = 1024 * 1024  # 1 MB para hashing parcial

def hash_parcial(path, max_bytes=MAX_BYTES):
    try:
        hash_md5 = hashlib.md5()
        tamaño = os.path.getsize(path)
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()
    except Exception:
        return None

def cargar_cache(cache_path):
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_cache(cache_path, cache_data):
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error al guardar caché: {e}")
