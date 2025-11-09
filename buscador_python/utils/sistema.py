import os

def eliminar_archivo(ruta):
    try:
        if os.path.exists(ruta):
            os.remove(ruta)
            return None
        else:
            return f"Archivo no existe: {ruta}"
    except Exception as e:
        return f"Error eliminando {ruta}: {e}"

def mover_archivo(origen, destino):
    import os
    try:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        nombre_base, ext = os.path.splitext(os.path.basename(destino))
        contador = 1
        nuevo_destino = destino
        while os.path.exists(nuevo_destino):
            nuevo_destino = os.path.join(os.path.dirname(destino), f"{nombre_base} ({contador}){ext}")
            contador += 1
        os.rename(origen, nuevo_destino)
        return None
    except Exception as e:
        return f"Error moviendo {origen} a {destino}: {e}"
