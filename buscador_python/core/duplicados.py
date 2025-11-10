import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from core.hashing import hash_parcial, cargar_cache, guardar_cache
from core.archivos import EXT_IMAGENES, EXT_VIDEOS, EXTENSIONES_VALIDAS, encontrar_archivos

MAX_HILOS = 4
MAX_ARCHIVOS = 300000

def escanear_y_hash(carpeta, progress_callback=None, max_hilos=MAX_HILOS, max_archivos=MAX_ARCHIVOS):
    archivos = encontrar_archivos(carpeta, EXTENSIONES_VALIDAS, limite=max_archivos)
    hashes = {}
    errores = []

    cache_path = os.path.join(carpeta, ".duplicados_cache.json")
    cache = cargar_cache(cache_path)

    resultado_queue = Queue()
    nuevo_cache = {}
    contador = 0
    total = len(archivos)

    def trabajador(path):
        try:
            stat = os.stat(path)
            size = stat.st_size
            mtime = stat.st_mtime

            if path in cache:
                cache_entry = cache[path]
                if cache_entry["size"] == size and cache_entry["mtime"] == mtime:
                    hash_valor = cache_entry["hash"]
                else:
                    hash_valor = hash_parcial(path)
            else:
                hash_valor = hash_parcial(path)

            if hash_valor:
                nuevo_cache[path] = {"size": size, "mtime": mtime, "hash": hash_valor}
            resultado_queue.put((hash_valor, path))
        except Exception:
            resultado_queue.put((None, path))

    with ThreadPoolExecutor(max_workers=max_hilos) as executor:
        futures = [executor.submit(trabajador, path) for path in archivos]
        for future in as_completed(futures):
            pass

    # Procesar resultados
    while not resultado_queue.empty():
        hash_valor, path = resultado_queue.get()
        if hash_valor:
            hashes.setdefault(hash_valor, []).append(path)
        else:
            errores.append(path)
        contador += 1
        if progress_callback:
            progress_callback(contador, total)

    # Guardar cache solo para archivos existentes
    nuevo_cache_existentes = {k: v for k, v in nuevo_cache.items() if os.path.exists(k)}
    guardar_cache(cache_path, nuevo_cache_existentes)

    return hashes, errores

def filtrar_duplicados(hashes):
    return {h: r for h, r in hashes.items() if len(r) > 1}
