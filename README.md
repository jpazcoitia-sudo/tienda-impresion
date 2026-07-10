# Tienda Impresion

Servidor de impresion ESC/POS para el sistema Tienda POS (Fiambreria Yanina).

Corre localmente en la PC del negocio, recibe los datos del ticket desde el
navegador y los imprime en la Epson TM-T20III via USB con calidad ESC/POS.

## Archivos

- `servidor_impresion.py` - Servidor activo (version en produccion)
- `servidor_impresion_con_qr.py` - Version con QR de Instagram (en prueba)
- `actualizar.py` - Descarga la ultima version desde este repo
- `iniciar_servidor.bat` - Actualiza y arranca el servidor (arranque de Windows)
- `actualizar_urgente.bat` - Fuerza actualizacion y reinicio (uso manual)

## Instalacion en PC nueva

Ver la guia en el repositorio principal.

## Como actualizar el servidor

1. Editar `servidor_impresion.py`
2. `git commit` y `git push`
3. La PC del negocio toma la nueva version al reiniciar (o con actualizar_urgente.bat)
