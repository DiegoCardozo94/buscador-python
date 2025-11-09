from PIL import Image
import os
import platform
import subprocess
import tempfile

EXT_IMAGENES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.heic')
EXT_VIDEOS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg')

def obtener_thumbnail_video(ruta):
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmpfile:
            comando = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "00:00:01",
                "-i", ruta,
                "-frames:v", "1",
                "-q:v", "2",
                tmpfile.name
            ]
            subprocess.run(comando, check=True)
            img = Image.open(tmpfile.name)
            img.thumbnail((300, 300))
            return img
    except Exception:
        return None

def es_imagen(ruta):
    return ruta.lower().endswith(EXT_IMAGENES)

def es_video(ruta):
    return ruta.lower().endswith(EXT_VIDEOS)

def abrir_archivo_sistema(ruta):
    if not os.path.isfile(ruta):
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(ruta)
        elif platform.system() == "Darwin":
            subprocess.run(["open", ruta])
        else:
            subprocess.run(["xdg-open", ruta])
        return True
    except Exception:
        return False
