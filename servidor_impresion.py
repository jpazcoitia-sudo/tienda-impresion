"""
Servidor de impresion local para Tienda POS - Fiambreria Yanina
================================================================

Version con comandos ESC/POS CRUDOS (bytes directos via _raw()).
Esto da control total del formato sin depender del perfil de python-escpos.

Requisitos (instalar una sola vez):
    pip install flask flask-cors python-escpos pyusb

Uso:
    python servidor_impresion.py

Queda escuchando en http://localhost:9100
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# -- Configuracion de la impresora --
VENDOR_ID = 0x04b8   # Epson
PRODUCT_ID = 0x0e27  # TM-T20III (confirmado en la Lenovo)
PUERTO = 9100

# -- App Flask --
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("servidor_impresion")

# -- Comandos ESC/POS --
ESC = b'\x1b'
GS = b'\x1d'

INIT         = ESC + b'@'
# Densidad de impresion maxima (GS ( K - ajuste de densidad)
DENSIDAD_MAX = GS + b'(' + b'K' + b'\x02\x00\x31\x08'
ALIGN_LEFT   = ESC + b'a' + b'\x00'
ALIGN_CENTER = ESC + b'a' + b'\x01'
BOLD_ON      = ESC + b'E' + b'\x01'
BOLD_OFF     = ESC + b'E' + b'\x00'
SIZE_NORMAL  = GS + b'!' + b'\x00'
CUT          = GS + b'V' + b'\x42' + b'\x00'
FEED         = b'\n'

ANCHO = 48


def obtener_impresora():
    from escpos.printer import Usb
    return Usb(VENDOR_ID, PRODUCT_ID, timeout=0)


def _col(izq, der, ancho=ANCHO):
    espacios = max(1, ancho - len(izq) - len(der))
    return (izq + (' ' * espacios) + der).encode('cp1252', errors='replace') + FEED


def _linea(texto=''):
    return texto.encode('cp1252', errors='replace') + FEED


def _truncar(texto, maximo):
    if len(texto) > maximo:
        return texto[:maximo - 1] + '.'
    return texto


def armar_ticket_raw(datos):
    out = bytearray()
    out += INIT
    out += DENSIDAD_MAX

    out += ALIGN_CENTER + BOLD_ON + SIZE_NORMAL
    out += _linea("PUNTO DE VENTA")
    out += BOLD_OFF
    out += _linea("Recibo no oficial")

    out += ALIGN_LEFT
    out += _linea("-" * ANCHO)
    out += _linea("Fecha: " + datos.get("fecha", ""))
    out += _linea("Ticket: " + datos.get("ticket", ""))
    out += _linea("-" * ANCHO)
    out += _col("Cant  Producto", "Total")
    out += _linea("-" * ANCHO)

    for item in datos.get("items", []):
        qty = item.get("qty", "")
        name = _truncar(item.get("name", ""), 32)
        total = item.get("total", "")
        price = item.get("price", "")
        out += _col(qty + "  " + name, total)
        out += _linea("  @ " + price + " c/u")

    out += _linea("-" * ANCHO)

    out += BOLD_ON
    out += _col("TOTAL:", datos.get("total", ""))
    out += BOLD_OFF
    out += _col("Recibido:", datos.get("recibido", ""))
    out += _col("Vuelto:", datos.get("vuelto", ""))
    out += _linea("-" * ANCHO)

    out += ALIGN_CENTER
    out += _linea("Gracias por su compra!")
    out += FEED + FEED + FEED
    out += CUT

    return bytes(out)


def imprimir_ticket(datos):
    p = obtener_impresora()
    datos_bytes = armar_ticket_raw(datos)
    p._raw(datos_bytes)
    p.close()


@app.route("/estado", methods=["GET"])
def estado():
    return jsonify({"estado": "ok", "servidor": "impresion", "puerto": PUERTO})


@app.route("/imprimir", methods=["POST"])
def imprimir():
    try:
        datos = request.get_json(force=True)
        logger.info("Ticket recibido: %s", datos.get("ticket", "sin-numero"))
        imprimir_ticket(datos)
        return jsonify({"estado": "ok", "mensaje": "Ticket impreso"})
    except Exception as e:
        logger.error("Error al imprimir: %s", e)
        return jsonify({"estado": "error", "mensaje": str(e)}), 500


if __name__ == "__main__":
    logger.info("Servidor de impresion iniciando en http://localhost:%s", PUERTO)
    logger.info("Endpoints: GET /estado  |  POST /imprimir")
    app.run(host="127.0.0.1", port=PUERTO, debug=False)