import tkinter as tk
from tkinter import ttk

class EstadoMixin:
    """
    Contiene métodos para gestionar el estado de los widgets (botones, progreso)
    y utilidades de formato.
    """

    def format_bytes(self, size):
        """Convierte bytes a una cadena legible (B, KB, MB, GB, TB)."""
        if size == 0:
            return "0 B"
        units = ("B", "KB", "MB", "GB", "TB")
        i = 0
        # Permite hasta Petabytes (PB) si el archivo fuera enorme
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"

    def _actualizar_estado_botones(self, escaneando=False):
        """
        Controla el estado de los botones de acción principales basado
        en si hay duplicados encontrados.
        """
        
        # Accede a la variable de la clase base
        hay_duplicados = bool(getattr(self, 'duplicados_global', {}))

        # 1. Determinar el estado general
        if escaneando:
            estado_accion = tk.DISABLED
            estado_general = tk.DISABLED
        else:
            # Habilitar acción solo si hay duplicados
            estado_accion = tk.NORMAL if hay_duplicados else tk.DISABLED
            estado_general = tk.NORMAL

        # 2. Aplicar estado a los botones:
        
        # Botones de gestión de duplicados (requieren duplicados)
        if self.boton_eliminar_auto:
            self.boton_eliminar_auto.config(state=estado_accion)
        if self.boton_mover:
            self.boton_mover.config(state=estado_accion)
        
        # Botones de utilidad/comparación/refresco (no requieren duplicados)
        if self.boton_comparar:
            self.boton_comparar.config(state=estado_general)
        if self.boton_refrescar:
            self.boton_refrescar.config(state=estado_general)
        if self.boton_mover_imagenes:
            self.boton_mover_imagenes.config(state=estado_general)
        if self.boton_eliminar_prefijo:
            self.boton_eliminar_prefijo.config(state=estado_general)
        
        # Botón de exploración
        if self.boton_explorar:
            self.boton_explorar.config(state=estado_general)

    def actualizar_progreso(self, contador, total):
        """Actualiza la barra de progreso y la etiqueta del contador (Escaneo)."""
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = contador
        self.contador_label.config(text=f"Archivos escaneados: {contador}/{total}")
        self.ventana.update_idletasks()

    def _actualizar_progreso_eliminacion(self, contador, total):
        """Actualiza la barra de progreso para tareas de eliminación/movimiento."""
        self.progress_bar["value"] = contador
        self.ventana.update_idletasks()