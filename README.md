# buscador-python

Buscador Automático de Duplicados de Archivos Multimedia (Imágenes y Videos)

Es una herramienta de escritorio rápida y eficiente, desarrollada en Python y Tkinter, diseñada para escanear grandes colecciones de archivos multimedia. Utiliza algoritmos de hashing con caché para identificar y gestionar copias exactas de imágenes (.jpg, .png, etc.) y videos (.mp4, .mkv, etc.).

✨ Características Principales

Alto Rendimiento: Implementa hashing de dos etapas (agrupación por tamaño y hash parcial) para descartar archivos únicos rápidamente, y concurrencia (ThreadPoolExecutor) para aprovechar múltiples núcleos de la CPU.

Sistema de Caché Inteligente: Almacena los hashes en un archivo de caché, recalculándolos solo si el archivo ha cambiado (verificando el tamaño y el tiempo de modificación mtime).

Previsualización Multimedia: Genera miniaturas en tiempo real para imágenes (usando PIL) y videos (usando ffmpeg).

Gestión de Archivos:

Eliminación automática y segura de duplicados (dejando solo una copia por grupo).

Movimiento de duplicados a una carpeta de "Archivos a Borrar".

Comparación y eliminación de duplicados entre dos carpetas diferentes.

Interfaz Gráfica (GUI): Interfaz intuitiva construida con tkinter.

💻 Instalación y Dependencias

Requiere Python 3.8+ y tiene dos dependencias principales:

1. Dependencias de Python

Instala las bibliotecas necesarias usando pip:

pip install pillow

2. Dependencia Externa (Multimedia)
Para generar las vistas previas (miniaturas) de los archivos de video (.mp4, .mkv, etc.), el sistema requiere tener instalado FFmpeg:

- Windows / macOS / Linux: Visita el sitio web oficial de FFmpeg y asegúrate de que el ejecutable (ffmpeg) esté disponible en el PATH del sistema.

🚀 Uso
1. Iniciar la Aplicación

Ejecuta el script principal desde tu terminal:

python main.py

2. Escaneo

Haz clic en "Seleccionar carpeta" y elige el directorio que deseas escanear.

La aplicación comenzará automáticamente el proceso de escaneo en segundo plano, actualizando la barra de progreso a medida que calcula los hashes.

Los grupos de archivos duplicados aparecerán en la tabla, agrupados por hash.

Funcionalidad,Descripción

- Doble Clic en la tabla, abre el archivo seleccionado con el programa predeterminado del sistema.
- Clic Simple en la tabla, muestra la previsualización (thumbnail) del archivo en el panel derecho.
- Eliminar duplicados autom., elimina todos los archivos duplicados, dejando intacta solo la primera instancia encontrada de cada grupo.
- Mover duplicados a 'borrar', mueve todos los duplicados (excepto la primera instancia) a una subcarpeta llamada archivos a borrar dentro de la carpeta escaneada.
- Comparar y eliminar entre carpetas, compara el contenido de la carpeta escaneada (A) con una segunda carpeta (B) seleccionada y elimina los duplicados solo en la carpeta B.

📂 Estructura del Proyecto

El código está organizado en módulos siguiendo buenas prácticas de separación de responsabilidades:


|-- main.py             # Punto de entrada de la aplicación
|
|-- core/               # Lógica central del buscador
|   |-- archivos.py     # Detección y listado de archivos multimedia
|   |-- hashing.py      # Cálculo de hash parcial y completo, gestión de caché
|   |-- duplicados.py   # Lógica concurrente de escaneo y filtrado (el 'motor')
|   |-- imagenes.py     # Generación de thumbnails (PIL y ffmpeg)
|
|-- gui/                # Lógica de la interfaz gráfica
|   |-- ventana.py      # La clase VentanaDuplicados (interfaz Tkinter)
|
|-- utils/              # Utilidades de bajo nivel
    |-- sistema.py      # Operaciones de archivo (eliminar, mover, renombrar)

🤝 Contribuciones y Soporte
Las contribuciones son bienvenidas. Si encuentra un error o tiene sugerencias para nuevas características, por favor, abra un issue en este repositorio.