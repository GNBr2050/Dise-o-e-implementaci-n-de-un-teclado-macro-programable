import tkinter as tk
from tkinter import messagebox
import traceback
import sys

# Importación principal
try:
    from ui_interface import MacroPadUI
except ImportError as e:
    print("Error crítico en importaciones:")
    traceback.print_exc()
    input("Presiona ENTER para salir...") # Pausa para leer el error
    sys.exit()

def main():
    try:
        root = tk.Tk()
        # root.iconbitmap('icon.ico') # Descomenta solo si tienes el archivo .ico
        
        app = MacroPadUI(root)
        
        print("Aplicación iniciada correctamente...")
        root.mainloop()
        
    except Exception as e:
        # Esto capturará errores lógicos (ej: falta un archivo o librería)
        error_msg = traceback.format_exc()
        print("ERROR EN TIEMPO DE EJECUCIÓN:")
        print(error_msg)
        try:
            messagebox.showerror("Error Fatal", f"Ocurrió un error:\n{e}\n\nRevisa la consola para más detalles.")
        except:
            pass
        input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()