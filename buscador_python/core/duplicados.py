import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
# Se elimina la importación de Queue, ya no es necesaria
from core.hashing import hash_parcial, cargar_cache, guardar_cache
from core.archivos import EXT_IMAGENES, EXT_VIDEOS, EXTENSIONES_VALIDAS, encontrar_archivos

MAX_HILOS = 4
MAX_ARCHIVOS = 300000

def escanear_y_hash(carpeta, progress_callback=None, max_hilos=MAX_HILOS, max_archivos=MAX_ARCHIVOS):
    """
    Escanea la carpeta, agrupa por tamaño y calcula los hashes de forma concurrente, 
    utilizando caché y reportando el progreso en tiempo real.
    """
    
    # 1. ENCONTRAR ARCHIVOS (devuelve lista de diccionarios con 'ruta' y 'tamaño')
    archivos = encontrar_archivos(carpeta, EXTENSIONES_VALIDAS, limite=max_archivos)
    
    # 2. OPTIMIZACIÓN: AGRUPAR POR TAMAÑO
    # Solo los archivos que comparten tamaño necesitan ser hasheados.
    grupos_por_tamaño = {}
    for info_archivo in archivos:
        # Usamos el tamaño como clave
        grupos_por_tamaño.setdefault(info_archivo['tamaño'], []).append(info_archivo)
    
    # Filtrar solo grupos con MÁS DE UN archivo (candidatos a duplicados)
    archivos_a_hashear = []
    for tamaño, grupo in grupos_por_tamaño.items():
        if len(grupo) > 1:
            archivos_a_hashear.extend(grupo)

    total = len(archivos_a_hashear) # El nuevo total es la base de la barra de progreso
    hashes = {}
    errores = []

    # 3. CARGAR CACHÉ
    cache_path = os.path.join(carpeta, ".duplicados_cache.json")
    cache = cargar_cache(cache_path)
    nuevo_cache = {}
    contador = 0
    
    if total == 0:
        if progress_callback:
            progress_callback(0, 0) # Reportar fin si no hay nada que hashear
        return {}, []

    def trabajador(info_archivo):
        """Función ejecutada por cada hilo para calcular el hash."""
        path = info_archivo['ruta']
        
        try:
            stat = os.stat(path)
            size = stat.st_size
            mtime = stat.st_mtime

            hash_valor = None
            
            # Lógica de caché: verificar si el archivo no ha cambiado
            if path in cache:
                cache_entry = cache[path]
                if cache_entry["size"] == size and cache_entry["mtime"] == mtime:
                    hash_valor = cache_entry["hash"]
            
            # Si no está en caché o ha cambiado, calcular el hash
            if not hash_valor:
                # Nota: Asume que hash_parcial() calcula el hash COMPLETO
                # Si quieres usar un hashing de 2 etapas REAL, aquí llamarías a un hash 
                # parcial y luego, si coincide, el hash completo.
                hash_valor = hash_parcial(path) # Usar la lógica actual
            
            # Preparar la entrada para la nueva caché
            if hash_valor:
                nuevo_cache[path] = {"size": size, "mtime": mtime, "hash": hash_valor}
                
            return hash_valor, path # Devolver resultado
            
        except (FileNotFoundError, PermissionError) as e:
            # Captura de errores específicos del sistema de archivos
            # print(f"Error al procesar {path}: {e}")
            return None, path # Devolver error

        except Exception:
            # Captura de cualquier otro error (ej. error en hash_parcial)
            return None, path

    # 4. EJECUCIÓN CONCURRENTE
    with ThreadPoolExecutor(max_workers=max_hilos) as executor:
        # Enviar la info_archivo completa a cada trabajador
        futures = [executor.submit(trabajador, info) for info in archivos_a_hashear] 
        
        # Procesar resultados y actualizar progreso en tiempo real
        for future in as_completed(futures):
            contador += 1
            
            try:
                # Obtener el resultado del hilo de trabajo
                hash_valor, path = future.result() 
                
                if hash_valor:
                    hashes.setdefault(hash_valor, []).append(path)
                else:
                    errores.append(path)
            
            except Exception:
                # Error interno del future (raro, pero manejado)
                continue 

            # Reportar el progreso al callback inmediatamente
            if progress_callback:
                progress_callback(contador, total)

    # 5. GUARDAR CACHÉ
    # Limpiar caché de archivos que fueron movidos o borrados antes de guardar
    nuevo_cache_existentes = {k: v for k, v in nuevo_cache.items() if os.path.exists(k)}
    guardar_cache(cache_path, nuevo_cache_existentes)

    return hashes, errores

def filtrar_duplicados(hashes):
    """Filtra el diccionario de hashes para devolver solo aquellos con más de un archivo."""
    return {h: r for h, r in hashes.items() if len(r) > 1}