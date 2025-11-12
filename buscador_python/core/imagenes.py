from PIL import Image
import os
import platform
import subprocess
import tempfile
# El sistema moderno de Python maneja DEVNULL, pero para compatibilidad
# se recomienda importarlo si se usa:
from subprocess import DEVNULL # Reemplaza el 'sys' original si se usa DEVNULL

# --- DEFINICIONES DE EXTENSIONES Y TAMAÑO ---
EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')
TAMANO_THUMBNAIL = (350, 350) 
TAMANO_THUMBNAIL_VIDEO = (300, 300) # Usado internamente por obtener_thumbnail_video

# --- FUNCIONES DE VERIFICACIÓN Y ACCIÓN ---

def verificar_ffmpeg():
    """Verifica si el ejecutable de ffmpeg está disponible en el PATH."""
    try:
        # Usa DEVNULL de subprocess.
        subprocess.run(["ffmpeg", "-version"], check=True, 
                        stdout=DEVNULL, stderr=DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def obtener_thumbnail_video(ruta):
    """Genera un thumbnail de un video usando ffmpeg."""
    if not verificar_ffmpeg():
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
            
            subprocess.run(comando, check=True, 
                            stdout=DEVNULL, stderr=DEVNULL)
            
            # Abrir y redimensionar con PIL
            img = Image.open(tmpfile.name)
            img.thumbnail(TAMANO_THUMBNAIL_VIDEO)
            return img
    
    except subprocess.CalledProcessError:
        return None
    except (FileNotFoundError, IOError):
        return None
    except Exception:
        return None

def es_imagen(ruta):
    """Verifica si la ruta apunta a una extensión de imagen."""
    # os.path.splitext devuelve la extensión con el punto (ej: '.mp4')
    _, ext = os.path.splitext(ruta) 
    return ext.lower() in EXT_IMAGENES

def es_video(ruta):
    """Verifica si la ruta apunta a una extensión de video."""
    _, ext = os.path.splitext(ruta)
    return ext.lower() in EXT_VIDEOS

def obtener_thumbnail(ruta_archivo):
    """
    Intenta obtener la miniatura, decidiendo si es imagen (PIL) o video (ffmpeg).
    """
    if not os.path.exists(ruta_archivo):
        return None
        
    # 1. Verificar si es un video
    if es_video(ruta_archivo):
        # Si es video, usa FFmpeg
        return obtener_thumbnail_video(ruta_archivo)

    # 2. Verificar si es una imagen (usando 'elif')
    elif es_imagen(ruta_archivo):
        try:
            # Lógica de procesamiento de imagen (PIL)
            img = Image.open(ruta_archivo)
            
            # Conversión de modo de color
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            # --- LÓGICA DE CENTRADO Y LIENZO ---
            
            # 1. Reducir la imagen si es necesario, manteniendo la proporción (thumbnail)
            img.thumbnail(TAMANO_THUMBNAIL)
            
            # 2. Crear el nuevo lienzo (marco) del tamaño del widget (350x350)
            ancho_final, alto_final = TAMANO_THUMBNAIL
            
            # Creamos el lienzo (la clave para que no se vea estirada)
            lienzo = Image.new('RGBA', (ancho_final, alto_final), (255, 255, 255, 0))
            
            # 3. Calcular la posición para centrar la imagen en el lienzo
            ancho_img, alto_img = img.size
            x_offset = (ancho_final - ancho_img) // 2
            y_offset = (alto_final - alto_img) // 2
            
            # 4. Pegar la imagen (ya redimensionada) en el centro del lienzo
            lienzo.paste(img, (x_offset, y_offset))
            
            # --- FIN LÓGICA DE CENTRADO Y LIENZO ---
            
            # 5. Devolver el lienzo (que ahora es el objeto de 350x350 con la imagen centrada)
            return lienzo 
            
        except Exception as e:
            print(f"Error al procesar la miniatura de imagen {ruta_archivo}: {e}")
            return None
            
    # Si no es ni imagen ni video soportado, devuelve None
    return None
    
# --- OTRAS FUNCIONES ---
# (abrir_archivo, etc.)
def abrir_archivo(ruta):
    """
    Abre un archivo utilizando el explorador de archivos predeterminado del sistema.
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