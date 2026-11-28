# Verificacion de VeredalApp

Fecha: 2026-11-27

## Resultados

- La aplicacion actualizada esta disponible en `http://127.0.0.1:5050/`; inicio y `/registro` responden 200.
- El inicio de sesion administrativo de Milena redirige al panel y el panel carga correctamente despues de reiniciar el servidor.
- `app.py` usa 5050 por defecto y permite configurar otro puerto mediante `PORT`.
- `app.py` compila y `git diff --check` no reporta errores.
- Pasaron 30 comprobaciones aisladas de rutas, permisos, registro, inicio de sesion, alta de asociados, publicaciones y radicacion de PQR. Los datos temporales se restauraron; no se escribieron datos de prueba en MySQL.
- MySQL responde. Existen las tablas `usuarios`, `asociados`, `pqrs` y `publicaciones`; `usuarios.clave` admite 255 caracteres.
- Las variables de administrador y `SECRET_KEY` estan configuradas en el entorno de usuario de Windows; los secretos no se incluyen en este informe.

## Instancia anterior

El proceso anterior que estaba en `http://127.0.0.1:5000/` tiene codigo desactualizado: una solicitud GET a `/registro` devolvia 405 y ese proceso no cargaba la configuracion de administrador. Usa el servidor actualizado en el puerto 5050.

## Datos pendientes

La tabla `publicaciones` esta creada, pero contiene 0 comunicados. Milena puede publicar el primer aviso desde la herramienta de administracion.

## Alcance

Las pruebas funcionales de formularios se ejecutaron con almacenamiento de demostracion y sin escrituras a MySQL. La comprobacion del esquema MySQL fue de solo lectura. No se encontro una suite de pruebas automatizadas en el proyecto.
