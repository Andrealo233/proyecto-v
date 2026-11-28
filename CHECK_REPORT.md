# Verificacion de VeredalApp

Fecha: 2026-11-27

## Resultados

- La aplicacion actualizada esta disponible en `http://127.0.0.1:5050/`; inicio y `/registro` responden 200.
- El inicio de sesion administrativo de Milena redirige al panel y el panel carga correctamente despues de reiniciar el servidor.
- `app.py` usa 5050 por defecto y permite configurar otro puerto mediante `PORT`.
- `app.py` compila y `git diff --check` no reporta errores.
- Pasaron 30 comprobaciones aisladas de rutas, permisos, registro, inicio de sesion, alta de asociados, publicaciones y radicacion de PQR. Los datos temporales se restauraron; no se escribieron datos de prueba en MySQL.
- MySQL responde. Existen las tablas `usuarios`, `asociados`, `pqrs`, `publicaciones`, `viviendas`, `configuracion_facturacion` y `cargos_recurrentes`; `usuarios.clave` admite 255 caracteres.
- Las variables de administrador y `SECRET_KEY` estan configuradas en el entorno de usuario de Windows; los secretos no se incluyen en este informe.

## Instancia anterior

El proceso anterior que estaba en `http://127.0.0.1:5000/` tiene codigo desactualizado: una solicitud GET a `/registro` devolvia 405 y ese proceso no cargaba la configuracion de administrador. Usa el servidor actualizado en el puerto 5050.

## Datos pendientes

La tabla `publicaciones` esta creada, pero contiene 0 comunicados. Milena puede publicar el primer aviso desde la herramienta de administracion.

## Alcance

Las pruebas funcionales anteriores de formularios se ejecutaron con almacenamiento de demostracion y sin escrituras a MySQL. La comprobacion del esquema MySQL fue de solo lectura. La nueva suite de facturacion cubre calculos mensuales/quincenales, validacion de viviendas y presentacion del estado de cuenta.

## Facturacion por vivienda

- La tarifa base mensual es de $15.000 COP por vivienda; la modalidad quincenal calcula la mitad por periodo.
- El registro y la edicion de asociados permiten relacionar varias viviendas y seleccionar la frecuencia de pago.
- `Mi cuenta` muestra el detalle de viviendas, los aportes recurrentes activos y el total correspondiente al periodo.
- La migracion `migracion_facturacion_viviendas.sql` es necesaria en bases existentes. Los asociados existentes quedan sin viviendas asignadas, y el historial de facturas se conserva.
- La migracion se aplico a `veredal_db`: se conservo el asociado existente sin asignarle viviendas y la tarifa inicial quedo en $15.000 COP.
- Pasaron 8 pruebas de facturacion con `python -m unittest discover -s tests -v`.
- Tras la migracion, las rutas `/facturacion`, `/productos`, `/nuevo-asociado` y `/mi-cuenta` respondieron 200 en pruebas Flask conectadas a MySQL.
