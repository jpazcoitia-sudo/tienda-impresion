# Tienda Impresion

Servidor de impresion ESC/POS para el sistema Tienda POS (Fiambreria Yanina — "Lo de Angelito").

Corre en cada PC que imprime tickets. El POS (navegador) le manda el ticket a
`http://localhost:9100/imprimir` y este servidor lo imprime con calidad ESC/POS:
titulo, cliente (si la venta tiene), items, totales y QR de Instagram.

## Archivos

| Archivo | Para que sirve |
|---|---|
| `servidor_impresion.py` | Servidor activo. **Se auto-actualiza** desde este repo. |
| `actualizar.py` | Descarga la ultima version de `servidor_impresion.py` desde `main`. |
| `iniciar_servidor.bat` | Actualiza y arranca el servidor (arranque de Windows). |
| `actualizar_urgente.bat` | Fuerza actualizacion y reinicio (uso manual). |
| `config_impresion.json` | **Opcional, NO va en el repo.** Configuracion propia de cada PC. |
| `servidor_impresion_con_qr.py`, `Servidor_impresion_bk.py` | Versiones anteriores (historial). |

## Configuracion por PC (`config_impresion.json`)

Va en la misma carpeta que `servidor_impresion.py` (en el negocio: `C:\TiendaPOS`).
La auto-actualizacion **nunca** lo pisa.

- **Sin archivo** → Epson por USB (el comportamiento de siempre).
- **Impresora compartida por print server:**

```json
{
    "modo": "red",
    "impresora": "epson",
    "print_server_ip": "192.168.180.35",
    "cola": "lp1"
}
```

| Campo | Valores | Por defecto |
|---|---|---|
| `modo` | `"usb"` (impresora enchufada a esta PC) / `"red"` (via print server) | `"usb"` |
| `impresora` | `"epson"` (TM-T20III, 80mm) / `"gadnic"` (IT1050, 58mm) | `"epson"` |
| `print_server_ip` | IP del print server (solo modo red) | — |
| `cola` | Cola LPD del print server | `"lp1"` |
| `qr` | `true` / `false` para forzar el QR | segun impresora |
| `reintentos` | Reintentos si el print server esta ocupado | `3` |

### Modo red (print server)
- Print server: NU62P11-A (generico "Networking USB LPR Print Server"), protocolo **LPD puerto 515**, cola **`lp1`**. El puerto 9100 esta cerrado.
- Varias PC comparten la impresora: cada PC corre su propio servidor y todos mandan al print server. Si dos imprimen a la vez, los trabajos se encolan (y hay reintentos).
- El print server toma IP por DHCP: si cambia, hay que actualizar `print_server_ip` (ideal: reserva DHCP en el router).

## Probar

- `http://localhost:9100/estado` → muestra modo, impresora y de donde salio la config.
- `http://localhost:9100/prueba` → imprime un ticket de prueba (con cliente de ejemplo).

## Instalacion en PC nueva (Windows)

1. Instalar Python 3 (tildar "Add Python to PATH").
2. `pip install flask flask-cors python-escpos pyusb`
3. Crear `C:\TiendaPOS` y copiar: `servidor_impresion.py`, `actualizar.py`, `iniciar_servidor.bat`, `actualizar_urgente.bat`.
4. Si usa print server: crear `config_impresion.json` (ver arriba).
5. Modo USB: la Epson necesita un driver compatible con libusb para `pyusb`. _(A confirmar: documentar como se hizo en la PC del negocio.)_
6. Arranque automatico: acceso directo a `C:\TiendaPOS\iniciar_servidor.bat` en la carpeta de inicio (`Windows+R` → `shell:startup`). _(A confirmar: como esta hecho en la PC del negocio.)_
7. Probar con `http://localhost:9100/prueba`.

## Como actualizar el servidor

> ⚠️ **Todo push a `main` se instala solo en las PC del negocio en el proximo reinicio.**
> Es un deploy a produccion: no pushear nada sin probarlo antes.

1. Editar `servidor_impresion.py`.
2. Probarlo en otra PC (ej. copia en `C:\PruebaImpresion` con su propio `config_impresion.json`).
3. `git commit` y `git push` a `main`.
4. La PC del negocio toma la nueva version al reiniciar (o con `actualizar_urgente.bat`).

Para volver atras: revertir el commit y pushear; al reiniciar vuelve la version anterior.

## Relacion con la app (repo `tienda`)

`store/pos/templates/pos/receipt.html` arma el JSON que se manda a `/imprimir`:
`fecha`, `ticket`, `cliente` (vacio si la venta no tiene cliente), `items` (`qty`, `name`, `price`, `total`), `total`, `recibido`, `vuelto`.
El boton **"Imprimir"** del recibo usa este servidor; "Imprimir (Chrome)" usa el navegador (respaldo).
