"""
Servidor de impresion local para Tienda POS - Fiambreria Yanina
================================================================

Recibe el ticket desde el POS (navegador) en http://localhost:9100/imprimir
y lo imprime con comandos ESC/POS crudos + QR de Instagram al pie.
Titulo: "Lo de Angelito"

CONFIGURACION POR PC (opcional): archivo config_impresion.json en esta carpeta.
Si NO existe, funciona como siempre: impresora Epson por USB.
La auto-actualizacion (actualizar.py) solo reemplaza ESTE archivo, nunca el
config_impresion.json, asi cada PC conserva su configuracion.

Ejemplo de config_impresion.json para imprimir via print server:
    {
        "modo": "red",
        "impresora": "epson",
        "print_server_ip": "192.168.180.35",
        "cola": "lp1"
    }

Valores posibles:
    modo:       "usb" (impresora enchufada a esta PC) | "red" (via print server, LPD)
    impresora:  "epson" (TM-T20III, 80mm) | "gadnic" (IT1050, 58mm)
    qr:         true | false   (opcional, por defecto segun la impresora)

Requisitos:
    pip install flask flask-cors python-escpos pyusb

Uso:
    python servidor_impresion.py

Endpoints:
    GET  /estado    -> estado y configuracion en uso
    POST /imprimir  -> imprime el ticket que manda el POS
    GET  /prueba    -> imprime un ticket de prueba
"""

import json
import logging
import os
import socket
import time
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

# -- Impresora USB (Epson TM-T20III) --
VENDOR_ID = 0x04b8
PRODUCT_ID = 0x0e27
PUERTO = 9100

# -- Datos del negocio --
INSTAGRAM_USUARIO = "@sabemosdepicadas"
INSTAGRAM_URL = "https://instagram.com/sabemosdepicadas"

# -- Perfiles de impresora --
PERFILES = {
    "epson":  {"ancho": 48, "densidad": True,  "corte": True,  "qr": True},   # 80mm
    "gadnic": {"ancho": 32, "densidad": False, "corte": False, "qr": True},   # 58mm
}

# -- Configuracion por defecto (= comportamiento original) --
CONFIG_DEFAULT = {
    "modo": "usb",
    "impresora": "epson",
    "print_server_ip": "",
    "print_server_puerto": 515,
    "cola": "lp1",
    "reintentos": 3,
    "qr": None,
}

DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CONFIG = os.path.join(DIR, "config_impresion.json")

# -- App Flask --
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("servidor_impresion")


def cargar_config():
    cfg = dict(CONFIG_DEFAULT)
    origen = "por defecto (USB + Epson)"
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, encoding="utf-8") as f:
                cfg.update(json.load(f))
            origen = ARCHIVO_CONFIG
        except Exception as e:
            logger.error("No se pudo leer %s (%s). Se usa la config por defecto.", ARCHIVO_CONFIG, e)
            cfg = dict(CONFIG_DEFAULT)
    if cfg["modo"] not in ("usb", "red"):
        logger.error("modo '%s' invalido. Se usa 'usb'.", cfg["modo"])
        cfg["modo"] = "usb"
    if cfg["impresora"] not in PERFILES:
        logger.error("impresora '%s' invalida. Se usa 'epson'.", cfg["impresora"])
        cfg["impresora"] = "epson"
    perfil = dict(PERFILES[cfg["impresora"]])
    if cfg.get("qr") is not None:
        perfil["qr"] = bool(cfg["qr"])
    return cfg, perfil, origen


CONFIG, PERFIL, ORIGEN_CONFIG = cargar_config()
ANCHO = PERFIL["ancho"]

# -- Comandos ESC/POS --
ESC = b'\x1b'
GS = b'\x1d'

INIT         = ESC + b'@'
DENSIDAD_MAX = GS + b'(' + b'K' + b'\x02\x00\x31\x08'
ALIGN_LEFT   = ESC + b'a' + b'\x00'
ALIGN_CENTER = ESC + b'a' + b'\x01'
BOLD_ON      = ESC + b'E' + b'\x01'
BOLD_OFF     = ESC + b'E' + b'\x00'
SIZE_NORMAL  = GS + b'!' + b'\x00'
DOBLE_ALTO   = GS + b'!' + b'\x01'
CUT          = GS + b'V' + b'\x42' + b'\x00'
FEED         = b'\n'


def _col(izq, der, ancho=None):
    ancho = ancho or ANCHO
    espacios = max(1, ancho - len(izq) - len(der))
    return (izq + (' ' * espacios) + der).encode('cp1252', errors='replace') + FEED


def _linea(texto=''):
    return texto.encode('cp1252', errors='replace') + FEED


def _truncar(texto, maximo):
    if len(texto) > maximo:
        return texto[:maximo - 1] + '.'
    return texto


def armar_cuerpo(datos):
    """Arma el cuerpo del ticket (sin QR ni corte) en bytes crudos."""
    out = bytearray()
    out += INIT
    if PERFIL["densidad"]:
        out += DENSIDAD_MAX

    # Titulo
    out += ALIGN_CENTER + BOLD_ON + SIZE_NORMAL
    out += _linea("Lo de Angelito")
    out += BOLD_OFF
    out += _linea("Recibo no oficial")

    # Cuerpo
    out += ALIGN_LEFT
    out += _linea("-" * ANCHO)

    # Cliente (solo si la venta tiene cliente) - destacado para el reparto
    cliente = (datos.get("cliente") or "").strip()
    if cliente:
        out += BOLD_ON + DOBLE_ALTO
        out += _linea("CLIENTE: " + cliente.upper())
        out += SIZE_NORMAL + BOLD_OFF
        out += _linea("-" * ANCHO)

    out += _linea("Fecha: " + datos.get("fecha", ""))
    out += _linea("Ticket: " + datos.get("ticket", ""))
    out += _linea("-" * ANCHO)
    out += _col("Cant  Producto", "Total")
    out += _linea("-" * ANCHO)

    largo_nombre = max(8, ANCHO - 16)
    for item in datos.get("items", []):
        qty = item.get("qty", "")
        name = _truncar(item.get("name", ""), largo_nombre)
        total = item.get("total", "")
        price = item.get("price", "")
        out += _col(qty + "  " + name, total)
        out += _linea("  @ " + price + " c/u")

    out += _linea("-" * ANCHO)

    # Totales
    out += BOLD_ON
    out += _col("TOTAL:", datos.get("total", ""))
    out += BOLD_OFF
    out += _col("Recibido:", datos.get("recibido", ""))
    out += _col("Vuelto:", datos.get("vuelto", ""))
    out += _linea("-" * ANCHO)

    # Pie con agradecimiento e Instagram
    out += ALIGN_CENTER
    out += _linea("Gracias por su compra!")
    out += FEED
    out += _linea("Seguinos en Instagram")
    out += _linea(INSTAGRAM_USUARIO)
    out += FEED

    return bytes(out)


def emitir(p, datos):
    """Manda el ticket completo a una 'impresora' de python-escpos (Usb o Dummy)."""
    # 1. Cuerpo del ticket (crudo)
    p._raw(armar_cuerpo(datos))
    # 2. QR de Instagram (metodo de la libreria, centrado)
    if PERFIL["qr"]:
        p.qr(INSTAGRAM_URL, size=6, center=True)
    # 3. Avance y corte (crudo)
    p._raw(FEED + FEED + FEED + (CUT if PERFIL["corte"] else b""))


# =====================================================================
# Salida por USB (igual que la version original)
# =====================================================================
def imprimir_usb(datos):
    from escpos.printer import Usb
    p = Usb(VENDOR_ID, PRODUCT_ID, timeout=0)
    emitir(p, datos)
    p.close()


# =====================================================================
# Salida por red: LPD (RFC 1179) al print server, en modo crudo
# =====================================================================
def _enviar_lpd_una_vez(datos_bytes):
    host = "pos"
    user = "tienda"
    jid = "%03d" % (int(time.time() * 1000) % 1000)
    df = "dfA%s%s" % (jid, host)
    cf = "cfA%s%s" % (jid, host)
    control = ("H%s\nP%s\nl%s\nU%s\nNticket\n" % (host, user, df, df)).encode()

    s = socket.create_connection((CONFIG["print_server_ip"], int(CONFIG["print_server_puerto"])), timeout=8)
    try:
        def ack(paso):
            r = s.recv(1)
            if r != b"\x00":
                raise RuntimeError("El print server rechazo el paso '%s' (respuesta %r)" % (paso, r))

        s.sendall(b"\x02" + CONFIG["cola"].encode() + b"\n")
        ack("cola")
        s.sendall(b"\x02" + str(len(control)).encode() + b" " + cf.encode() + b"\n")
        ack("control")
        s.sendall(control + b"\x00")
        ack("control-datos")
        s.sendall(b"\x03" + str(len(datos_bytes)).encode() + b" " + df.encode() + b"\n")
        ack("datos")
        s.sendall(datos_bytes + b"\x00")
        ack("datos-fin")
    finally:
        s.close()


def imprimir_red(datos):
    if not CONFIG["print_server_ip"]:
        raise RuntimeError("Modo red sin 'print_server_ip' en config_impresion.json")
    from escpos.printer import Dummy
    p = Dummy()
    emitir(p, datos)
    datos_bytes = p.output

    reintentos = int(CONFIG.get("reintentos", 3))
    ultimo_error = None
    for intento in range(1, reintentos + 1):
        try:
            _enviar_lpd_una_vez(datos_bytes)
            return
        except Exception as e:
            ultimo_error = e
            logger.warning("Intento %s/%s fallo: %s", intento, reintentos, e)
            time.sleep(1.5)
    raise RuntimeError("No se pudo imprimir en %s (cola %s): %s"
                       % (CONFIG["print_server_ip"], CONFIG["cola"], ultimo_error))


def imprimir_ticket(datos):
    if CONFIG["modo"] == "red":
        imprimir_red(datos)
    else:
        imprimir_usb(datos)


# =====================================================================
# Endpoints
# =====================================================================
@app.route("/estado", methods=["GET"])
def estado():
    return jsonify({
        "estado": "ok", "servidor": "impresion", "puerto": PUERTO,
        "modo": CONFIG["modo"], "impresora": CONFIG["impresora"], "qr": PERFIL["qr"],
        "print_server": CONFIG["print_server_ip"] if CONFIG["modo"] == "red" else None,
        "cola": CONFIG["cola"] if CONFIG["modo"] == "red" else None,
        "config": ORIGEN_CONFIG,
    })


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


@app.route("/prueba", methods=["GET"])
def prueba():
    datos = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "ticket": "PRUEBA",
        "cliente": "Cliente de Prueba",
        "items": [
            {"qty": "1", "name": "Queso cremoso", "price": "$1500", "total": "$1500"},
            {"qty": "2", "name": "Salame milan", "price": "$500", "total": "$1000"},
        ],
        "total": "$2500",
        "recibido": "$3000",
        "vuelto": "$500",
    }
    try:
        imprimir_ticket(datos)
        return jsonify({"estado": "ok", "mensaje": "Ticket de prueba enviado (%s, %s)"
                        % (CONFIG["modo"], CONFIG["impresora"])})
    except Exception as e:
        logger.error("Error en prueba: %s", e)
        return jsonify({"estado": "error", "mensaje": str(e)}), 500


if __name__ == "__main__":
    logger.info("Servidor de impresion iniciando en http://localhost:%s", PUERTO)
    logger.info("Config: %s", ORIGEN_CONFIG)
    logger.info("Modo: %s | Impresora: %s | QR: %s%s", CONFIG["modo"], CONFIG["impresora"], PERFIL["qr"],
                (" | Print server: %s cola %s" % (CONFIG["print_server_ip"], CONFIG["cola"]))
                if CONFIG["modo"] == "red" else "")
    logger.info("Endpoints: GET /estado  |  POST /imprimir  |  GET /prueba")
    app.run(host="127.0.0.1", port=PUERTO, debug=False)
