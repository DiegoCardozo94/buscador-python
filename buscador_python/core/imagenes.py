from PIL import Image
import os
import platform
import subprocess
import tempfile
import sys # Importado para DEVNULL, útil para subprocess

EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')

def verificar_ffmpeg():
    """Verifica si el ejecutable de ffmpeg está disponible en el PATH."""
    try:
        # Ejecuta un comando simple, check=True lanzará error si no se encuentra
        subprocess.run(["ffmpeg", "-version"], check=True, 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def obtener_thumbnail_video(ruta):
    """Genera un thumbnail de un video usando ffmpeg."""
    if not verificar_ffmpeg():
        # Retorna None si ffmpeg no está instalado
        return None
    
    try:
        # Usa tempfile.NamedTemporaryFile para gestionar la limpieza del archivo temporal
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmpfile:
            comando = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "00:00:01", # Posición de 1 segundo
                "-i", ruta,
                "-frames:v", "1",
                "-q:v", "2", # Calidad de la imagen
                tmpfile.name
            ]
            
            # check=True asegura que se lance un error si ffmpeg falla
            subprocess.run(comando, check=True, 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Abrir y redimensionar con PIL
            img = Image.open(tmpfile.name)
            img.thumbnail((300, 300))
            return img
    
    except subprocess.CalledProcessError:
        # Falla de ffmpeg (video corrupto o códec no soportado)
        return None
    except (FileNotFoundError, IOError):
        # Problema de acceso al archivo o al temporal
        return None
    except Exception:
        # Otros errores (ej: en PIL al abrir el tempfile)
        return None

def obtener_thumbnail(ruta):
    """
    Función unificada para obtener la vista previa:
    1. Si es video, llama a obtener_thumbnail_video.
    2. Si es imagen, la abre y redimensiona con PIL.
    """
    if es_video(ruta):
        return obtener_thumbnail_video(ruta)
    
    elif es_imagen(ruta):
        try:
            img = Image.open(ruta)
            img.thumbnail((300, 300))
            return img
        except Exception:
            return None
    
    return None

def es_imagen(ruta):
    """Verifica si la ruta apunta a una extensión de imagen."""
    return ruta.lower().endswith(EXT_IMAGENES)

def es_video(ruta):
    """Verifica si la ruta apunta a una extensión de video."""
    return ruta.lower().endswith(EXT_VIDEOS)

def abrir_archivo(ruta):
    """
    Abre un archivo utilizando el explorador de archivos predeterminado del sistema.
    (Función unificada para reemplazar 'abrir_archivo_sistema' y la duplicada)
    """
    if not os.path.isfile(ruta):
        return False
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(ruta)
        elif sistema == "Darwin": # macOS
            subprocess.run(["open", ruta], check=True)
        else: # Linux/Otros Unix
            subprocess.run(["xdg-open", ruta], check=True)
        return True
    except Exception:
        return False