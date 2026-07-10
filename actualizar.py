"""
Actualizador del servidor de impresion.
=======================================

Descarga la ultima version de servidor_impresion.py desde el repo publico
de GitHub y la reemplaza localmente si cambio.

Se ejecuta ANTES de arrancar el servidor (desde el .bat).
No requiere token porque el repo es publico.
"""

import urllib.request
import hashlib
import os
import sys

# URL raw del archivo en GitHub (repo publico)
URL_RAW = "https://raw.githubusercontent.com/jpazcoitia-sudo/tienda-impresion/main/servidor_impresion.py"

# Archivo local a actualizar (mismo directorio que este script)
DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_LOCAL = os.path.join(DIR, "servidor_impresion.py")


def hash_contenido(contenido):
    return hashlib.md5(contenido).hexdigest()


def actualizar():
    print("Verificando actualizaciones del servidor de impresion...")

    try:
        # Descargar la version remota
        with urllib.request.urlopen(URL_RAW, timeout=10) as resp:
            contenido_remoto = resp.read()
    except Exception as e:
        print("No se pudo verificar actualizaciones (sin internet?):", e)
        print("Se usara la version local actual.")
        return

    # Leer la version local si existe
    contenido_local = b""
    if os.path.exists(ARCHIVO_LOCAL):
        with open(ARCHIVO_LOCAL, "rb") as f:
            contenido_local = f.read()

    # Comparar
    if hash_contenido(contenido_remoto) == hash_contenido(contenido_local):
        print("El servidor ya esta actualizado.")
        return

    # Hay version nueva: reemplazar
    try:
        with open(ARCHIVO_LOCAL, "wb") as f:
            f.write(contenido_remoto)
        print("Servidor actualizado a la ultima version.")
    except Exception as e:
        print("Error al guardar la actualizacion:", e)


if __name__ == "__main__":
    actualizar()
