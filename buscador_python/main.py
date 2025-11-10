import tkinter as tk
# Importar la clase principal refactorizada
from gui import base

def iniciar_ventana():
    app = base.VentanaDuplicados()
    app.ventana.mainloop()

if __name__ == "__main__":
    # Asegúrate de que los módulos 'core' y 'utils' estén en el path si es necesario
    # sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    iniciar_ventana()