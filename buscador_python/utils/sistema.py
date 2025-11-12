import os
import shutil # Necesario para mover si os.rename falla por cruce de dispositivos

def eliminar_archivo(ruta):
    """
    Elimina un archivo, retornando None si tiene éxito o un mensaje de error.
    """
    try:
        if os.path.exists(ruta):
            # Usar os.remove para eliminar el archivo
            os.remove(ruta)
            return None
        else:
            # Archivo ya no existe, reportar para el log, pero no es un error de eliminación
            return f"Archivo no existe: {ruta}" 
    except (FileNotFoundError, PermissionError, IOError) as e:
        # Captura errores de I/O, como permisos insuficientes o archivos abiertos
        return f"Error eliminando {ruta}: {e}"
    except Exception as e:
        # Otros errores inesperados
        return f"Error inesperado al eliminar {ruta}: {e}"

def mover_archivo(origen, destino):
    """
    Mueve un archivo a una nueva ubicación, asegurando que el nombre 
    de destino sea único para evitar sobrescribir.
    
    Devuelve None si tiene éxito, o un string con el mensaje de error si falla.
    """
    try:
        # 1. Crear el directorio destino si no existe
        # Esto es crucial para que la función no falle si la carpeta 'videos extraidos' no existe
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        
        # 2. Lógica para manejar la colisión de nombres
        nombre_base, ext = os.path.splitext(os.path.basename(destino))
        contador = 1
        nuevo_destino = destino
        
        while os.path.exists(nuevo_destino):
            # Si el archivo ya existe en el destino, añadir (1), (2), etc.
            nuevo_destino = os.path.join(os.path.dirname(destino), f"{nombre_base} ({contador}){ext}")
            contador += 1
            
        # 3. Intentar mover. os.rename es más rápido pero falla entre dispositivos/particiones.
        try:
            # Intenta mover usando os.rename (rápido, dentro del mismo disco)
            os.rename(origen, nuevo_destino)
        except OSError:
            # Si os.rename falla (ej. moviendo a otra partición o unidad), usar shutil.move
            # shutil.move maneja la copia y posterior eliminación
            shutil.move(origen, nuevo_destino)

        # Si todo es exitoso
        return None
        
    except (FileNotFoundError, PermissionError, IOError) as e:
        # Captura errores comunes como "archivo en uso" o "permiso denegado"
        return f"Error de I/O moviendo {os.path.basename(origen)}: {e}"
    except Exception as e:
        # Captura cualquier otro error inesperado
        return f"Error inesperado al mover {os.path.basename(origen)}: {e}"