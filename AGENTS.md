# AGENTS.md — tienda-impresion

Servidor de impresion ESC/POS (Flask, puerto 9100) que corre en las PC Windows del negocio.
Recibe los tickets del POS (repo tienda) en /imprimir. Ver README.md para contrato, config y modos.
El contrato completo con Tienda esta en ../tienda/docs/impresion.md.

## Reglas
- CRITICO: todo push a main se instala solo en las PC del negocio al reiniciar. Es un deploy a produccion.
  Nunca hacer commit ni push sin que Juan lo apruebe y lo haya probado en la Lenovo (C:\PruebaImpresion).
- No cambiar el formato del JSON de /imprimir (fecha, ticket, cliente, items, total, recibido, vuelto)
  sin seguir el orden de ../tienda/docs/impresion.md: primero el agente acepta lo viejo y lo nuevo, despues Tienda.
- Mantener compatibilidad con Windows, con las dos impresoras (epson 80mm, gadnic 58mm) y ambos modos (usb, red).
- config_impresion.json es propio de cada PC: nunca va al repo ni se pisa.
- La impresion real no se puede probar en la Mac: revisar el codigo y avisar que hay que probar en Windows.

## Archivos
- servidor_impresion.py: el activo. servidor_impresion_con_qr.py y Servidor_impresion_bk.py son versiones viejas: no editarlos.
- actualizar.py y los .bat: auto-actualizacion desde GitHub. No se actualizan solos en las PC; tocarlos con mucho cuidado.
