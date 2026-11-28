from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import os
import hmac
import secrets
from functools import wraps
from datetime import datetime, timedelta
import random
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

DB_AVAILABLE = False

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '1234'),
    'database': os.environ.get('DB_NAME', 'veredal_db'),
    'connection_timeout': 5,
    'autocommit': True,
    'raise_on_warnings': True,
}


def get_db():
    global DB_AVAILABLE
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        DB_AVAILABLE = True
        return conn
    except mysql.connector.Error as e:
        DB_AVAILABLE = False
        error_msg = str(e)
        if "Access denied" in error_msg:
            print(f"❌ MySQL Access Denied: Check user/password. Using fallback mode.")
        elif "Can't connect" in error_msg or "Connection refused" in error_msg:
            print(f"❌ MySQL Server not running: {e}. Using fallback mode.")
        elif "Unknown database" in error_msg:
            print(f"❌ Database 'veredal_db' doesn't exist. Using fallback mode.")
        else:
            print(f"❌ Database connection failed: {e}. Using fallback mode.")
        return None
    except Exception as e:
        DB_AVAILABLE = False
        print(f"❌ Unexpected DB error: {e}. Using fallback mode.")
        return None


def get_db_or_fallback():
    db = get_db()
    if db is None:
        flash('Base de datos no disponible. Funcionando en modo demostración.', 'warning')
    return db


def close_db(db, cursor=None):
    """Safely close database connection and cursor."""
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if db and db.is_connected():
            db.close()
    except Exception:
        pass


def missing_fields(*names):
    """Return a list of required form fields that were not submitted."""
    return [name for name in names if not request.form.get(name, '').strip()]


def verify_password(stored_password, submitted_password):
    if stored_password.startswith(('scrypt:', 'pbkdf2:')):
        try:
            return check_password_hash(stored_password, submitted_password)
        except ValueError:
            return False
    return hmac.compare_digest(stored_password, submitted_password)


def demo_login_is_valid(usuario, clave):
    if not usuario or not clave:
        return None
    for account in DEMO_CUENTAS.values():
        if usuario in (account['nombre'], account['documento']) and verify_password(account['clave'], clave):
            return account
    return None


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get('usuario'):
                flash('Inicia sesión para continuar.', 'warning')
                return redirect(url_for('login'))
            if session.get('rol') not in roles:
                flash('No tienes permiso para acceder a esa página.', 'error')
                return redirect(url_for('inicio'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ============================================================
# FALLBACK DEMO DATA - Colombian Rural Aqueduct Community
# ============================================================

DEMO_USUARIOS = [
    {'id': 1, 'nombre': 'Carlos Méndez', 'documento': '1.023.456.789', 'telefono': '310 234 5678', 'vereda': 'El Roble', 'estrato': 2, 'medidor': 'M-101', 'tarifa': 'Residencial', 'estado': 'Activo', 'ultimo_pago': '2025-07-10'},
    {'id': 2, 'nombre': 'Ana Torres', 'documento': '1.098.765.432', 'telefono': '320 111 2233', 'vereda': 'La Loma', 'estrato': 1, 'medidor': 'M-102', 'tarifa': 'Residencial', 'estado': 'Activo', 'ultimo_pago': '2025-07-12'},
    {'id': 3, 'nombre': 'Jorge Herrera', 'documento': '1.145.678.901', 'telefono': '315 789 0123', 'vereda': 'San José', 'estrato': 2, 'medidor': 'M-103', 'tarifa': 'Agrícola', 'estado': 'Activo', 'ultimo_pago': '2025-07-08'},
    {'id': 4, 'nombre': 'María Rojas', 'documento': '1.202.345.678', 'telefono': '300 456 7890', 'vereda': 'El Mirador', 'estrato': 1, 'medidor': 'M-104', 'tarifa': 'Residencial', 'estado': 'Activo', 'ultimo_pago': '2025-07-14'},
    {'id': 5, 'nombre': 'Luis Gómez', 'documento': '1.334.567.890', 'telefono': '312 345 6789', 'vereda': 'El Roble', 'estrato': 2, 'medidor': 'M-105', 'tarifa': 'Comercial', 'estado': 'Activo', 'ultimo_pago': '2025-07-05'},
    {'id': 6, 'nombre': 'Patricia Vélez', 'documento': '1.456.789.012', 'telefono': '318 901 2345', 'vereda': 'La Loma', 'estrato': 1, 'medidor': 'M-106', 'tarifa': 'Residencial', 'estado': 'Suspendido', 'ultimo_pago': '2025-06-20'},
    {'id': 7, 'nombre': 'Roberto Díaz', 'documento': '1.567.890.123', 'telefono': '314 567 8901', 'vereda': 'San José', 'estrato': 2, 'medidor': 'M-107', 'tarifa': 'Agrícola', 'estado': 'Activo', 'ultimo_pago': '2025-07-11'},
    {'id': 8, 'nombre': 'Carmen López', 'documento': '1.678.901.234', 'telefono': '311 678 9012', 'vereda': 'El Mirador', 'estrato': 1, 'medidor': 'M-108', 'tarifa': 'Residencial', 'estado': 'Activo', 'ultimo_pago': '2025-07-13'},
    {'id': 9, 'nombre': 'Fernando Castro', 'documento': '1.789.012.345', 'telefono': '319 789 0123', 'vereda': 'El Roble', 'estrato': 3, 'medidor': 'M-109', 'tarifa': 'Residencial', 'estado': 'Activo', 'ultimo_pago': '2025-07-09'},
    {'id': 10, 'nombre': 'Gloria Muñoz', 'documento': '1.890.123.456', 'telefono': '316 890 1234', 'vereda': 'La Loma', 'estrato': 2, 'medidor': 'M-110', 'tarifa': 'Ultrasónico', 'estado': 'Activo', 'ultimo_pago': '2025-07-15'},
]

DEMO_SERVICIOS = [
    {'nombre': 'Derecho de Matrícula Residencial', 'tipo': 'Conexión', 'valor': 150000, 'descripcion': 'Instalación nueva vivienda'},
    {'nombre': 'Acueducto Agrícola / Riego', 'tipo': 'Servicio', 'valor': 85000, 'descripcion': 'Riego por goteo y aspersión'},
    {'nombre': 'Medidor Ultrasónico Inteligente', 'tipo': 'Equipo', 'valor': 220000, 'descripcion': 'Lectura remota sin contacto'},
    {'nombre': 'Reconexión de Servicio', 'tipo': 'Mantenimiento', 'valor': 45000, 'descripcion': 'Restablecimiento tras suspensión'},
    {'nombre': 'Cambio de Medidor Mecánico', 'tipo': 'Mantenimiento', 'valor': 95000, 'descripcion': 'Actualización a digital'},
    {'nombre': 'Toma Domiciliaria Estándar', 'tipo': 'Conexión', 'valor': 120000, 'descripcion': 'Conexión 1/2 pulgada'},
]

DEMO_LECTURAS = [
    {'servicio': 'AV-001 · Carlos Méndez (M-101)', 'lectura_anterior': 1250, 'lectura_actual': 1278, 'consumo': 28, 'fecha': '2025-07-15 08:30:00', 'vereda': 'El Roble'},
    {'servicio': 'AV-002 · Ana Torres (M-102)', 'lectura_anterior': 980, 'lectura_actual': 1012, 'consumo': 32, 'fecha': '2025-07-15 09:15:00', 'vereda': 'La Loma'},
    {'servicio': 'AV-003 · Jorge Herrera (M-103)', 'lectura_anterior': 2100, 'lectura_actual': 2145, 'consumo': 45, 'fecha': '2025-07-14 14:20:00', 'vereda': 'San José'},
    {'servicio': 'AV-004 · María Rojas (M-104)', 'lectura_anterior': 750, 'lectura_actual': 772, 'consumo': 22, 'fecha': '2025-07-14 10:45:00', 'vereda': 'El Mirador'},
    {'servicio': 'AV-005 · Luis Gómez (M-105)', 'lectura_anterior': 3200, 'lectura_actual': 3265, 'consumo': 65, 'fecha': '2025-07-13 16:00:00', 'vereda': 'El Roble'},
    {'servicio': 'AV-006 · Patricia Vélez (M-106)', 'lectura_anterior': 580, 'lectura_actual': 595, 'consumo': 15, 'fecha': '2025-07-13 11:30:00', 'vereda': 'La Loma'},
]

DEMO_FACTURAS = [
    {'id': 1, 'numero': 'FV-2025-001', 'asociado': 'Carlos Méndez', 'documento': '1.023.456.789', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 28, 'valor': 58500, 'estado': 'Pagada', 'fecha_pago': '2025-07-10', 'metodo': 'Efectivo'},
    {'id': 2, 'numero': 'FV-2025-002', 'asociado': 'Ana Torres', 'documento': '1.098.765.432', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 32, 'valor': 62000, 'estado': 'Pagada', 'fecha_pago': '2025-07-12', 'metodo': 'Transferencia'},
    {'id': 3, 'numero': 'FV-2025-003', 'asociado': 'Jorge Herrera', 'documento': '1.145.678.901', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 45, 'valor': 85500, 'estado': 'Pendiente', 'fecha_pago': None, 'metodo': None},
    {'id': 4, 'numero': 'FV-2025-004', 'asociado': 'María Rojas', 'documento': '1.202.345.678', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 22, 'valor': 52000, 'estado': 'Pagada', 'fecha_pago': '2025-07-14', 'metodo': 'Efectivo'},
    {'id': 5, 'numero': 'FV-2025-005', 'asociado': 'Luis Gómez', 'documento': '1.334.567.890', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 65, 'valor': 125000, 'estado': 'En Mora', 'fecha_pago': None, 'metodo': None},
    {'id': 6, 'numero': 'FV-2025-006', 'asociado': 'Patricia Vélez', 'documento': '1.456.789.012', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 15, 'valor': 42000, 'estado': 'Pendiente', 'fecha_pago': None, 'metodo': None},
    {'id': 7, 'numero': 'FV-2025-007', 'asociado': 'Roberto Díaz', 'documento': '1.567.890.123', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 38, 'valor': 72000, 'estado': 'Pagada', 'fecha_pago': '2025-07-11', 'metodo': 'Nequi'},
    {'id': 8, 'numero': 'FV-2025-008', 'asociado': 'Carmen López', 'documento': '1.678.901.234', 'periodo': 'Julio 2025', 'meses': 1, 'm3': 26, 'valor': 56000, 'estado': 'Pagada', 'fecha_pago': '2025-07-13', 'metodo': 'Daviplata'},
    {'id': 9, 'numero': 'FV-2025-009', 'asociado': 'Fernando Castro', 'documento': '1.789.012.345', 'periodo': 'Junio 2025', 'meses': 1, 'm3': 31, 'valor': 61000, 'estado': 'En Mora', 'fecha_pago': None, 'metodo': None},
    {'id': 10, 'numero': 'FV-2025-010', 'asociado': 'Gloria Muñoz', 'documento': '1.890.123.456', 'periodo': 'Junio 2025', 'meses': 1, 'm3': 29, 'valor': 59000, 'estado': 'Pagada', 'fecha_pago': '2025-06-28', 'metodo': 'Efectivo'},
]

DEMO_PQRS = [
    {'codigo': 'P-001', 'tipo': 'Petición', 'asunto': 'Solicitud de nueva conexión domiciliaria', 'sector': 'El Roble', 'descripcion': 'Nueva vivienda requiere conexión a red matriz', 'prioridad': 'Media', 'fecha': '2025-07-10', 'estado': 'En proceso', 'responsable': 'Técnico Carlos'},
    {'codigo': 'P-002', 'tipo': 'Queja', 'asunto': 'Agua con mal olor y color amarillento', 'sector': 'La Loma', 'descripcion': 'Varios usuarios reportan olor a azufre desde hace 3 días', 'prioridad': 'Alta', 'fecha': '2025-07-12', 'estado': 'En proceso', 'responsable': 'Químico María'},
    {'codigo': 'P-003', 'tipo': 'Reclamo', 'asunto': 'Factura incorrecta - consumo inflado', 'sector': 'San José', 'descripcion': 'Medidor marca 45 m³ pero consumo real estimado en 28 m³', 'prioridad': 'Alta', 'fecha': '2025-07-08', 'estado': 'Resuelto', 'responsable': 'Facturación'},
    {'codigo': 'P-004', 'tipo': 'Solicitud de Reparación', 'asunto': 'Fuga en tubería madre sector El Roble', 'sector': 'El Roble', 'descripcion': 'Fuga visible a 50m de la bocatoma, pérdida estimada 15 L/min', 'prioridad': 'Crítica', 'fecha': '2025-07-14', 'estado': 'En proceso', 'responsable': 'Cuadrilla A'},
    {'codigo': 'P-005', 'tipo': 'Petición', 'asunto': 'Cambio de medidor a ultrasónico', 'sector': 'El Mirador', 'descripcion': 'Usuario solicita actualización a medidor inteligente', 'prioridad': 'Baja', 'fecha': '2025-07-05', 'estado': 'Pendiente', 'responsable': 'Técnico Luis'},
    {'codigo': 'P-006', 'tipo': 'Queja', 'asunto': 'Baja presión en horas pico (6-8 AM)', 'sector': 'La Loma', 'descripcion': 'Presión insuficiente para tanque elevado', 'prioridad': 'Media', 'fecha': '2025-07-11', 'estado': 'En proceso', 'responsable': 'Ing. Hidráulica'},
    {'codigo': 'P-007', 'tipo': 'Reclamo', 'asunto': 'Corte de servicio sin previo aviso', 'sector': 'San José', 'descripcion': 'Suspendieron servicio el 12/07 sin notificar a la comunidad', 'prioridad': 'Alta', 'fecha': '2025-07-13', 'estado': 'Resuelto', 'responsable': 'Administración'},
    {'codigo': 'P-008', 'tipo': 'Petición', 'asunto': 'Extensión de red hacia vereda Nueva Esperanza', 'sector': 'Nueva Esperanza', 'descripcion': '15 familias solicitan conexión a acueducto veredal', 'prioridad': 'Media', 'fecha': '2025-07-01', 'estado': 'Pendiente', 'responsable': 'Planeación'},
]

DEMO_TELEMETRIA = {
    'bocatoma_caudal_ls': 42.5,
    'tanque_principal_nivel': 78,
    'tanque_alto_nivel': 65,
    'ph': 7.2,
    'cloro_residual': 0.8,
    'turbidez': 1.2,
    'presion_red': 3.8,
    'ultima_actualizacion': '2025-07-15 14:30:00',
}

DEMO_CONSUMO_DIARIO = [
    {'fecha': '2025-07-09', 'consumo_m3': 1250, 'caudal_ls': 41.2},
    {'fecha': '2025-07-10', 'consumo_m3': 1320, 'caudal_ls': 43.1},
    {'fecha': '2025-07-11', 'consumo_m3': 1180, 'caudal_ls': 39.8},
    {'fecha': '2025-07-12', 'consumo_m3': 1410, 'caudal_ls': 45.3},
    {'fecha': '2025-07-13', 'consumo_m3': 1290, 'caudal_ls': 42.7},
    {'fecha': '2025-07-14', 'consumo_m3': 1350, 'caudal_ls': 44.0},
    {'fecha': '2025-07-15', 'consumo_m3': 1380, 'caudal_ls': 45.8},
]

DEMO_RECAUDO_MENSUAL = [
    {'mes': 'Ene', 'facturado': 8500000, 'recaudado': 7800000, 'mora': 700000},
    {'mes': 'Feb', 'facturado': 8800000, 'recaudado': 8200000, 'mora': 600000},
    {'mes': 'Mar', 'facturado': 9100000, 'recaudado': 8500000, 'mora': 600000},
    {'mes': 'Abr', 'facturado': 9500000, 'recaudado': 9100000, 'mora': 400000},
    {'mes': 'May', 'facturado': 9800000, 'recaudado': 9200000, 'mora': 600000},
    {'mes': 'Jun', 'facturado': 10200000, 'recaudado': 9800000, 'mora': 400000},
    {'mes': 'Jul', 'facturado': 10500000, 'recaudado': 10100000, 'mora': 400000},
]

DEMO_CARTERA_ESTADO = {
    'al_dia': 72,
    'pendiente': 18,
    'mora': 10,
}

DEMO_ASOCIADOS_VEREDA = {
    'El Roble': 32,
    'La Loma': 28,
    'San José': 22,
    'El Mirador': 18,
    'Nueva Esperanza': 12,
}

DEMO_SERVICIOS_TIPO = {
    'Residencial': 68,
    'Agrícola': 22,
    'Comercial': 8,
    'Ultrasónico': 12,
}

DEMO_ACTIVIDAD_RECIENTE = [
    {'icono': '💰', 'tipo': 'success', 'titulo': 'Pago recibido', 'detalle': 'Carlos Méndez - $58.500 - Hace 15 min', 'estado': 'Completado'},
    {'icono': '💧', 'tipo': 'info', 'titulo': 'Nueva lectura registrada', 'detalle': 'Jorge Herrera - 45 m³ - Sector San José', 'estado': 'Registrado'},
    {'icono': '⚡', 'tipo': 'warning', 'titulo': 'Corte programado', 'detalle': 'Sector La Loma - Mañana 8:00 AM - Mantenimiento', 'estado': 'Programado'},
    {'icono': '🚨', 'tipo': 'danger', 'titulo': 'PQRS Urgente', 'detalle': 'Fuga en tubería madre El Roble - Sin resolver', 'estado': 'En proceso'},
    {'icono': '📋', 'tipo': 'info', 'titulo': 'Nueva solicitud', 'detalle': 'Gloria Muñoz - Cambio a medidor ultrasónico', 'estado': 'Pendiente'},
    {'icono': '💰', 'tipo': 'success', 'titulo': 'Pago recibido', 'detalle': 'Ana Torres - $62.000 - Hace 1 hora', 'estado': 'Completado'},
    {'icono': '🔧', 'tipo': 'warning', 'titulo': 'Mantenimiento preventivo', 'detalle': 'Tanque Principal - Limpieza programada sábado', 'estado': 'Programado'},
]

DEMO_PUBLICACIONES = [
    {
        'id': 1,
        'titulo': 'Comunicados de la Junta de Acción Comunal',
        'contenido': 'En este espacio se publicarán los avisos oficiales sobre el servicio de agua y las actividades comunitarias.',
        'activo': 1,
        'actualizado_en': 'Información general',
    },
]

DEMO_CUENTAS = {}


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def inicio():
    db = get_db()
    publicaciones = [post for post in DEMO_PUBLICACIONES if post['activo']]
    modo_demo = db is None
    if db is not None:
        cursor = None
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """SELECT id, titulo, contenido, activo, actualizado_en
                   FROM publicaciones WHERE activo=1 ORDER BY actualizado_en DESC"""
            )
            publicaciones = cursor.fetchall()
        except Exception as e:
            print(f"Publicaciones no disponibles: {e}")
            flash('No se pudieron cargar los comunicados guardados. Revisa la migración de publicaciones.', 'warning')
            publicaciones = [post for post in DEMO_PUBLICACIONES if post['activo']]
            modo_demo = True
        finally:
            close_db(db, cursor)
    return render_template('inicio.html', publicaciones=publicaciones, modo_demo=modo_demo)


@app.route('/admin/publicaciones', methods=['GET', 'POST'])
@roles_required('administrador')
def administrar_publicaciones():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        contenido = request.form.get('contenido', '').strip()
        publicacion_id = request.form.get('publicacion_id', '').strip()
        activo = 1 if request.form.get('activo') == '1' else 0
        if not titulo or not contenido:
            flash('El título y el contenido son obligatorios.', 'warning')
            return redirect(url_for('administrar_publicaciones'))
        if len(titulo) > 160 or len(contenido) > 5000:
            flash('El título admite hasta 160 caracteres y el comunicado hasta 5000.', 'warning')
            return redirect(url_for('administrar_publicaciones'))

        if publicacion_id:
            try:
                publicacion_id = int(publicacion_id)
            except ValueError:
                flash('La publicación seleccionada no es válida.', 'warning')
                return redirect(url_for('administrar_publicaciones'))

        db = get_db()
        if db is None:
            if publicacion_id:
                post = next((p for p in DEMO_PUBLICACIONES if p['id'] == publicacion_id), None)
                if post is None:
                    flash('No se encontró la publicación que intentas editar.', 'warning')
                    return redirect(url_for('administrar_publicaciones'))
                post.update(titulo=titulo, contenido=contenido, activo=activo,
                            actualizado_en=datetime.now().strftime('%Y-%m-%d %H:%M'))
                flash('Comunicado actualizado en modo demostración.', 'success')
            else:
                DEMO_PUBLICACIONES.append({
                    'id': max((p['id'] for p in DEMO_PUBLICACIONES), default=0) + 1,
                    'titulo': titulo,
                    'contenido': contenido,
                    'activo': activo,
                    'actualizado_en': datetime.now().strftime('%Y-%m-%d %H:%M'),
                })
                flash('Comunicado publicado en modo demostración.', 'success')
            return redirect(url_for('administrar_publicaciones'))

        cursor = None
        try:
            cursor = db.cursor()
            if publicacion_id:
                cursor.execute("SELECT id FROM publicaciones WHERE id=%s", (publicacion_id,))
                if cursor.fetchone() is None:
                    flash('No se encontró la publicación que intentas editar.', 'warning')
                    return redirect(url_for('administrar_publicaciones'))
                cursor.execute(
                    """UPDATE publicaciones
                       SET titulo=%s, contenido=%s, activo=%s
                       WHERE id=%s""",
                    (titulo, contenido, activo, publicacion_id)
                )
                flash('Comunicado actualizado correctamente.', 'success')
            else:
                cursor.execute(
                    """INSERT INTO publicaciones (titulo, contenido, activo, creado_por)
                       VALUES (%s, %s, %s, %s)""",
                    (titulo, contenido, activo, session['usuario'])
                )
                flash('Comunicado publicado correctamente.', 'success')
            db.commit()
        except Exception as e:
            print(f"Guardar publicación: {e}")
            flash('No se pudo guardar. Verifica que migracion_publicaciones.sql esté aplicada.', 'error')
        finally:
            close_db(db, cursor)
        return redirect(url_for('administrar_publicaciones'))

    db = get_db()
    publicaciones = [dict(p) for p in DEMO_PUBLICACIONES]
    publicacion = None
    modo_demo = db is None
    migration_error = False
    if db is not None:
        cursor = None
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """SELECT id, titulo, contenido, activo, creado_por, actualizado_en
                   FROM publicaciones ORDER BY actualizado_en DESC"""
            )
            publicaciones = cursor.fetchall()
            editar = request.args.get('editar', '').strip()
            if editar:
                try:
                    editar_id = int(editar)
                except ValueError:
                    flash('La publicación seleccionada no es válida.', 'warning')
                else:
                    publicacion = next((p for p in publicaciones if p['id'] == editar_id), None)
                    if publicacion is None:
                        flash('No se encontró la publicación que intentas editar.', 'warning')
        except Exception as e:
            print(f"Cargar publicaciones: {e}")
            flash('No se pudo abrir la tabla de publicaciones. Aplica migracion_publicaciones.sql.', 'error')
            publicaciones = []
            migration_error = True
        finally:
            close_db(db, cursor)
    elif request.args.get('editar', '').strip():
        try:
            editar_id = int(request.args['editar'])
            publicacion = next((p for p in publicaciones if p['id'] == editar_id), None)
        except ValueError:
            flash('La publicación seleccionada no es válida.', 'warning')
        if publicacion is None:
            flash('No se encontró la publicación que intentas editar.', 'warning')

    return render_template(
        'admin_publicaciones.html',
        publicaciones=publicaciones,
        publicacion=publicacion,
        modo_demo=modo_demo,
        migration_error=migration_error
    )


@app.route('/dashboard')
@roles_required('administrador')
def dashboard():
    """Dashboard principal con KPIs, gráfico radial y actividad reciente"""
    db = get_db_or_fallback()
    if db is None:
        return render_template('dashboard.html',
            kpis={'usuarios': 1254, 'servicios': 412, 'recaudo': 12500000, 'pqrs': 18},
            instalados=310, en_proceso=74, cancelados=28,
            actividad=DEMO_ACTIVIDAD_RECIENTE[:5]
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        # KPIs
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        usuarios = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM asociados WHERE estado='Activo'")
        servicios = cursor.fetchone()['total']
        cursor.execute("SELECT SUM(valor) as total FROM facturas WHERE MONTH(fecha)=7 AND YEAR(fecha)=2025")
        recaudo = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT COUNT(*) as total FROM pqrs WHERE estado='En proceso'")
        pqrs = cursor.fetchone()['total']

        # Instalaciones
        cursor.execute("SELECT COUNT(*) as total FROM instalaciones WHERE estado='Instalado'")
        instalados = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM instalaciones WHERE estado='En proceso'")
        en_proceso = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as total FROM instalaciones WHERE estado='Cancelado'")
        cancelados = cursor.fetchone()['total']

        # Actividad reciente
        cursor.execute("""SELECT * FROM actividad_reciente ORDER BY fecha DESC LIMIT 5""")
        actividad = cursor.fetchall()

        close_db(db, cursor)
        return render_template('dashboard.html',
            kpis={'usuarios': usuarios, 'servicios': servicios, 'recaudo': recaudo, 'pqrs': pqrs},
            instalados=instalados, en_proceso=en_proceso, cancelados=cancelados,
            actividad=actividad
        )
    except Exception as e:
        print(f"Dashboard fallback: {e}")
        close_db(db, cursor)
        return render_template('dashboard.html',
            kpis={'usuarios': 1254, 'servicios': 412, 'recaudo': 12500000, 'pqrs': 18},
            instalados=310, en_proceso=74, cancelados=28,
            actividad=DEMO_ACTIVIDAD_RECIENTE[:5]
        )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('rol') == 'administrador':
            return redirect(url_for('dashboard'))
        if session.get('rol') == 'usuario':
            return redirect(url_for('radicar_pqr'))
        return render_template('acceso.html')

    usuario = request.form.get('usuario', '').strip()
    clave = request.form.get('clave', '').strip()
    rol = request.form.get('rol', '').strip()
    session.clear()
    if not usuario or not clave or rol not in ('administrador', 'usuario'):
        flash('Completa tus datos y selecciona un tipo de acceso.', 'warning')
        return redirect(url_for('login'))

    if rol == 'administrador':
        admin_username = os.environ.get('ADMIN_USERNAME', 'Milena').strip()
        admin_password = os.environ.get('ADMIN_PASSWORD', '')
        if not admin_username or not admin_password:
            flash('El acceso de Administrador no está configurado en el servidor.', 'error')
            return redirect(url_for('login'))
        if hmac.compare_digest(usuario, admin_username) and hmac.compare_digest(clave, admin_password):
            session['usuario'] = admin_username
            session['rol'] = 'administrador'
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos.', 'error')
        return redirect(url_for('login'))

    db = get_db()
    cursor = None
    if db is None:
        flash('Base de datos no disponible. Solo están disponibles las cuentas registradas durante esta sesión de demostración.', 'warning')
        account = demo_login_is_valid(usuario, clave)
        if account:
            session['usuario'] = account['nombre']
            session['rol'] = 'usuario'
            flash('Ingreso como usuario en modo demostración.', 'success')
            return redirect(url_for('radicar_pqr'))
        flash('Usuario o contraseña incorrectos.', 'error')
        return redirect(url_for('login'))

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT nombre, documento, clave FROM usuarios WHERE nombre=%s OR documento=%s LIMIT 1",
            (usuario, usuario)
        )
        user = cursor.fetchone()
        if not user or not verify_password(user['clave'], clave):
            flash('Usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('login'))
        session['usuario'] = user['nombre']
        session['rol'] = 'usuario'
        return redirect(url_for('radicar_pqr'))
    except Exception as e:
        print(f"Login failed: {e}")
        flash('No se pudo validar el acceso. Intenta de nuevo.', 'error')
        return redirect(url_for('login'))
    finally:
        close_db(db, cursor)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'GET':
        return render_template('registro.html')

    if missing_fields('nombre', 'documento', 'clave', 'confirmar_clave'):
        flash('Completa todos los campos obligatorios.', 'warning')
        return redirect(url_for('registro'))

    nombre = request.form['nombre'].strip()
    documento = request.form['documento'].strip()
    telefono = request.form.get('telefono', '').strip()
    clave = request.form['clave']
    confirmar_clave = request.form['confirmar_clave']
    if len(clave) < 8:
        flash('La contraseña debe tener al menos 8 caracteres.', 'warning')
        return redirect(url_for('registro'))
    if clave != confirmar_clave:
        flash('Las contraseñas no coinciden.', 'warning')
        return redirect(url_for('registro'))

    clave_hash = generate_password_hash(clave)
    db = get_db()
    if db is None:
        if any(account['documento'] == documento for account in DEMO_CUENTAS.values()):
            flash('Ya existe una cuenta con ese documento.', 'warning')
            return redirect(url_for('registro'))
        DEMO_CUENTAS[documento] = {
            'nombre': nombre,
            'documento': documento,
            'telefono': telefono,
            'clave': clave_hash,
        }
        session.clear()
        session['usuario'] = nombre
        session['rol'] = 'usuario'
        flash('Cuenta creada en modo de demostración; no quedará guardada al reiniciar.', 'warning')
        return redirect(url_for('radicar_pqr'))

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE documento=%s", (documento,))
        existente = cursor.fetchone()
        if existente:
            flash('Ya existe una cuenta con ese documento.', 'warning')
            return redirect(url_for('registro'))
        cursor.execute(
            "INSERT INTO usuarios (nombre, documento, telefono, clave) VALUES (%s, %s, %s, %s)",
            (nombre, documento, telefono, clave_hash)
        )
        db.commit()
        session.clear()
        session['usuario'] = nombre
        session['rol'] = 'usuario'
        flash('Cuenta creada correctamente.', 'success')
        return redirect(url_for('radicar_pqr'))
    except Exception as e:
        print(f"Registro de usuario: {e}")
        flash('No se pudo completar el registro. Verifica la migración de contraseñas y vuelve a intentar.', 'error')
        return redirect(url_for('registro'))
    finally:
        close_db(db, cursor)


@app.route('/nuevo-asociado', methods=['GET', 'POST'])
@roles_required('administrador')
def nuevo_asociado():
    if request.method == 'GET':
        return render_template('nuevo_asociado.html')

    required = missing_fields('nombre', 'documento')
    if required:
        flash('Completa el nombre y el documento del asociado.', 'warning')
        return redirect(url_for('nuevo_asociado'))

    nombre = request.form['nombre'].strip()
    documento = request.form['documento'].strip()
    telefono = request.form.get('telefono', '').strip()
    vereda = request.form.get('vereda', '').strip()
    tarifa = request.form.get('tarifa', 'Residencial').strip()
    try:
        estrato = int(request.form.get('estrato', '2'))
    except ValueError:
        flash('Selecciona un estrato válido.', 'warning')
        return redirect(url_for('nuevo_asociado'))
    if estrato not in (1, 2, 3):
        flash('Selecciona un estrato válido.', 'warning')
        return redirect(url_for('nuevo_asociado'))

    db = get_db_or_fallback()
    if db is None:
        if any(user['documento'] == documento for user in DEMO_USUARIOS):
            flash('Ya existe un asociado con ese documento.', 'warning')
            return redirect(url_for('nuevo_asociado'))
        DEMO_USUARIOS.append({
            'id': max(user['id'] for user in DEMO_USUARIOS) + 1,
            'nombre': nombre,
            'documento': documento,
            'telefono': telefono,
            'vereda': vereda,
            'estrato': estrato,
            'medidor': 'Pendiente',
            'tarifa': tarifa,
            'estado': 'Activo',
            'ultimo_pago': '—',
        })
        flash('Asociado registrado en modo demostración.', 'success')
        return redirect(url_for('nuevo_asociado'))

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM asociados WHERE documento=%s", (documento,))
        if cursor.fetchone():
            flash('Ya existe un asociado con ese documento.', 'warning')
            close_db(db, cursor)
            return redirect(url_for('nuevo_asociado'))
        cursor.execute(
            """INSERT INTO asociados (nombre, documento, telefono, vereda, estrato, tarifa, estado)
               VALUES (%s, %s, %s, %s, %s, %s, 'Activo')""",
            (nombre, documento, telefono, vereda, estrato, tarifa)
        )
        db.commit()
        flash('Asociado registrado correctamente.', 'success')
    except Exception as e:
        print(f"Nuevo asociado: {e}")
        flash('No se pudo registrar el asociado. Intenta de nuevo.', 'error')
    finally:
        close_db(db, cursor)
    return redirect(url_for('nuevo_asociado'))


@app.route('/radicar-pqr', methods=['GET', 'POST'])
@roles_required('usuario')
def radicar_pqr():
    if request.method == 'GET':
        return render_template('radicar_pqr.html')

    if missing_fields('tipo', 'asunto'):
        flash('Selecciona el tipo de PQR y describe el motivo.', 'warning')
        return redirect(url_for('radicar_pqr'))

    tipo = request.form['tipo'].strip()
    asunto = request.form['asunto'].strip()
    sector = request.form.get('sector', '').strip()
    prioridad = request.form.get('prioridad', 'Media').strip()
    tipos_validos = ('Petición', 'Queja', 'Reclamo', 'Solicitud de Reparación')
    prioridades_validas = ('Baja', 'Media', 'Alta', 'Crítica')
    if tipo not in tipos_validos or prioridad not in prioridades_validas:
        flash('Revisa el tipo de PQR y la prioridad seleccionados.', 'warning')
        return redirect(url_for('radicar_pqr'))
    if len(asunto) > 200:
        flash('El asunto y la descripción pueden tener hasta 200 caracteres.', 'warning')
        return redirect(url_for('radicar_pqr'))

    db = get_db_or_fallback()
    if db is None:
        codigo = f"P-{len(DEMO_PQRS) + 1:03d}"
        DEMO_PQRS.append({
            'codigo': codigo,
            'tipo': tipo,
            'asunto': asunto,
            'sector': sector,
            'descripcion': asunto,
            'prioridad': prioridad,
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'estado': 'Pendiente',
            'responsable': 'Por asignar',
        })
        flash(f'PQR radicada en modo demostración. Código: {codigo}.', 'success')
        return redirect(url_for('radicar_pqr'))

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM pqrs")
        codigo = f"P-{cursor.fetchone()['total'] + 1:03d}"
        cursor.execute(
            """INSERT INTO pqrs (codigo, tipo, asunto, sector, prioridad, estado, fecha)
               VALUES (%s, %s, %s, %s, %s, 'Pendiente', CURDATE())""",
            (codigo, tipo, asunto, sector, prioridad)
        )
        db.commit()
        flash(f'PQR radicada correctamente. Código: {codigo}.', 'success')
    except Exception as e:
        print(f"Radicar PQR: {e}")
        flash('No se pudo radicar la PQR. Intenta de nuevo.', 'error')
    finally:
        close_db(db, cursor)
    return redirect(url_for('radicar_pqr'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))


@app.route('/productos', methods=['GET', 'POST'])
@app.route('/asociados', methods=['GET', 'POST'])
@roles_required('administrador')
def productos():
    """Asociados y Servicios - lista completa con gráficos"""
    db = get_db_or_fallback()
    if db is None:
        if request.method == 'POST':
            if missing_fields('nombre', 'documento'):
                flash('Completa el nombre y el documento del asociado.', 'warning')
            else:
                flash('Asociado registrado (modo demostración).', 'success')
        return render_template('productos.html',
            asociados=DEMO_USUARIOS,
            servicios=DEMO_SERVICIOS,
            veredas=DEMO_ASOCIADOS_VEREDA,
            tipos_servicio=DEMO_SERVICIOS_TIPO
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            if missing_fields('nombre', 'documento'):
                flash('Completa el nombre y el documento del asociado.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('productos'))
            nombre = request.form['nombre'].strip()
            documento = request.form['documento'].strip()
            telefono = request.form.get('telefono', '').strip()
            vereda = request.form.get('vereda', '')
            estrato = request.form.get('estrato', 1)
            tarifa = request.form.get('tarifa', 'Residencial')
            cursor.execute("""INSERT INTO asociados (nombre, documento, telefono, vereda, estrato, tarifa, estado)
                             VALUES (%s, %s, %s, %s, %s, %s, 'Activo')""",
                           (nombre, documento, telefono, vereda, estrato, tarifa))
            db.commit()
            flash('Asociado agregado correctamente', 'success')

        cursor.execute("SELECT * FROM asociados ORDER BY id DESC")
        asociados = cursor.fetchall()

        # Servicios desde BD o demo
        cursor.execute("SELECT * FROM servicios ORDER BY id")
        servicios = cursor.fetchall() or DEMO_SERVICIOS

        # Agregaciones para gráficos
        cursor.execute("SELECT vereda, COUNT(*) as total FROM asociados GROUP BY vereda")
        veredas = {row['vereda']: row['total'] for row in cursor.fetchall()} or DEMO_ASOCIADOS_VEREDA

        cursor.execute("SELECT tarifa, COUNT(*) as total FROM asociados GROUP BY tarifa")
        tipos_servicio = {row['tarifa']: row['total'] for row in cursor.fetchall()} or DEMO_SERVICIOS_TIPO

        close_db(db, cursor)
        return render_template('productos.html',
            asociados=asociados,
            servicios=servicios,
            veredas=veredas,
            tipos_servicio=tipos_servicio
        )
    except Exception as e:
        print(f"Productos fallback: {e}")
        close_db(db, cursor)
        return render_template('productos.html',
            asociados=DEMO_USUARIOS,
            servicios=DEMO_SERVICIOS,
            veredas=DEMO_ASOCIADOS_VEREDA,
            tipos_servicio=DEMO_SERVICIOS_TIPO
        )


@app.route('/agua', methods=['GET', 'POST'])
@roles_required('administrador')
def agua():
    """Gestión del Agua - telemetría, lecturas y gráficos de consumo"""
    db = get_db_or_fallback()
    if db is None:
        if request.method == 'POST':
            required = missing_fields('servicio', 'lectura_anterior', 'lectura_actual')
            if required:
                flash('Completa todos los datos de la lectura.', 'warning')
            else:
                try:
                    anterior = int(request.form['lectura_anterior'])
                    actual = int(request.form['lectura_actual'])
                    if anterior < 0 or actual < anterior:
                        flash('La lectura actual no puede ser menor que la anterior.', 'warning')
                    else:
                        flash('Lectura registrada (modo demostración).', 'success')
                except ValueError:
                    flash('Las lecturas deben ser valores numéricos.', 'warning')
        return render_template('agua2.html',
            lecturas=DEMO_LECTURAS,
            telemetria=DEMO_TELEMETRIA,
            consumo_diario=DEMO_CONSUMO_DIARIO,
            veredas_consumo={
                'El Roble': 420,
                'La Loma': 380,
                'San José': 310,
                'El Mirador': 270,
            }
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            if missing_fields('servicio', 'lectura_anterior', 'lectura_actual'):
                flash('Completa todos los datos de la lectura.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('agua'))
            servicio = request.form['servicio'].strip()
            try:
                ant = int(request.form['lectura_anterior'])
                act = int(request.form['lectura_actual'])
            except ValueError:
                flash('Las lecturas deben ser valores numéricos.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('agua'))
            if ant < 0 or act < ant:
                flash('La lectura actual no puede ser menor que la anterior.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('agua'))
            consumo = max(0, act - ant)
            cursor.execute("""INSERT INTO lecturas (servicio, lectura_anterior, lectura_actual, consumo)
                             VALUES (%s, %s, %s, %s)""", (servicio, ant, act, consumo))
            db.commit()
            flash('Lectura registrada correctamente', 'success')

        cursor.execute("SELECT * FROM lecturas ORDER BY id DESC LIMIT 10")
        lecturas = cursor.fetchall() or DEMO_LECTURAS

        cursor.execute("SELECT * FROM telemetria ORDER BY id DESC LIMIT 1")
        telemetria = cursor.fetchone() or DEMO_TELEMETRIA

        cursor.execute("SELECT fecha, consumo_m3, caudal_ls FROM consumo_diario ORDER BY fecha DESC LIMIT 7")
        consumo_diario = cursor.fetchall() or DEMO_CONSUMO_DIARIO

        cursor.execute("SELECT vereda, SUM(consumo) as total FROM lecturas GROUP BY vereda")
        veredas_consumo = {row['vereda']: row['total'] for row in cursor.fetchall()} or {
            'El Roble': 420, 'La Loma': 380, 'San José': 310, 'El Mirador': 270
        }

        close_db(db, cursor)
        return render_template('agua2.html',
            lecturas=lecturas,
            telemetria=telemetria,
            consumo_diario=consumo_diario,
            veredas_consumo=veredas_consumo
        )
    except Exception as e:
        print(f"Agua fallback: {e}")
        close_db(db, cursor)
        return render_template('agua2.html',
            lecturas=DEMO_LECTURAS,
            telemetria=DEMO_TELEMETRIA,
            consumo_diario=DEMO_CONSUMO_DIARIO,
            veredas_consumo={'El Roble': 420, 'La Loma': 380, 'San José': 310, 'El Mirador': 270}
        )


@app.route('/facturacion', methods=['GET', 'POST'])
@roles_required('administrador')
def facturacion():
    """Facturación y Pagos - cartera, KPIs y gráficos"""
    db = get_db_or_fallback()
    if db is None:
        if request.method == 'POST':
            if not request.form.get('id_factura', '').strip():
                flash('No se indicó la factura a pagar.', 'warning')
            else:
                flash('Pago registrado (modo demostración).', 'success')
        # KPIs
        total_facturado = sum(f['valor'] for f in DEMO_FACTURAS)
        total_recaudado = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'Pagada')
        total_mora = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'En Mora')
        total_pendiente = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'Pendiente')

        return render_template('facturacion.html',
            facturas=DEMO_FACTURAS,
            kpis={
                'facturado': total_facturado,
                'recaudado': total_recaudado,
                'mora': total_mora,
                'pendiente': total_pendiente,
                'porcentaje_recaudo': round((total_recaudado / total_facturado * 100) if total_facturado > 0 else 0, 1)
            },
            recaudo_mensual=DEMO_RECAUDO_MENSUAL,
            cartera_estado=DEMO_CARTERA_ESTADO,
            metodos_pago={
                'Efectivo': 45,
                'Transferencia': 25,
                'Nequi': 15,
                'Daviplata': 10,
                'Otro': 5
            }
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            id_factura = request.form.get('id_factura', '').strip()
            if not id_factura:
                flash('No se indicó la factura a pagar.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('facturacion'))
            cursor.execute("UPDATE facturas SET estado='Pagada', fecha_pago=CURDATE() WHERE id=%s", (id_factura,))
            db.commit()
            flash('Pago registrado correctamente', 'success')

        cursor.execute("SELECT * FROM facturas ORDER BY id DESC")
        facturas = cursor.fetchall() or DEMO_FACTURAS

        # KPIs
        cursor.execute("SELECT SUM(valor) as total FROM facturas WHERE YEAR(fecha)=2025")
        total_facturado = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT SUM(valor) as total FROM facturas WHERE estado='Pagada' AND YEAR(fecha)=2025")
        total_recaudado = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT SUM(valor) as total FROM facturas WHERE estado='En Mora'")
        total_mora = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT SUM(valor) as total FROM facturas WHERE estado='Pendiente'")
        total_pendiente = cursor.fetchone()['total'] or 0

        cursor.execute("""SELECT MONTH(fecha) as mes, SUM(valor) as facturado,
                         SUM(CASE WHEN estado='Pagada' THEN valor ELSE 0 END) as recaudado,
                         SUM(CASE WHEN estado='En Mora' THEN valor ELSE 0 END) as mora
                         FROM facturas WHERE YEAR(fecha)=2025 GROUP BY MONTH(fecha) ORDER BY mes""")
        recaudo_mensual = cursor.fetchall() or DEMO_RECAUDO_MENSUAL

        cursor.execute("SELECT estado, COUNT(*) as total FROM facturas GROUP BY estado")
        cartera_rows = cursor.fetchall()
        cartera_estado = {row['estado'].lower().replace(' ', '_'): row['total'] for row in cartera_rows} or DEMO_CARTERA_ESTADO

        cursor.execute("SELECT metodo, COUNT(*) as total FROM facturas WHERE metodo IS NOT NULL GROUP BY metodo")
        metodos_rows = cursor.fetchall()
        metodos_pago = {row['metodo']: row['total'] for row in metodos_rows} or {
            'Efectivo': 45, 'Transferencia': 25, 'Nequi': 15, 'Daviplata': 10, 'Otro': 5
        }

        close_db(db, cursor)
        return render_template('facturacion.html',
            facturas=facturas,
            kpis={
                'facturado': total_facturado,
                'recaudado': total_recaudado,
                'mora': total_mora,
                'pendiente': total_pendiente,
                'porcentaje_recaudo': round((total_recaudado / total_facturado * 100) if total_facturado > 0 else 0, 1)
            },
            recaudo_mensual=recaudo_mensual,
            cartera_estado=cartera_estado,
            metodos_pago=metodos_pago
        )
    except Exception as e:
        print(f"Facturación fallback: {e}")
        close_db(db, cursor)
        total_facturado = sum(f['valor'] for f in DEMO_FACTURAS)
        total_recaudado = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'Pagada')
        total_mora = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'En Mora')
        total_pendiente = sum(f['valor'] for f in DEMO_FACTURAS if f['estado'] == 'Pendiente')
        return render_template('facturacion.html',
            facturas=DEMO_FACTURAS,
            kpis={
                'facturado': total_facturado,
                'recaudado': total_recaudado,
                'mora': total_mora,
                'pendiente': total_pendiente,
                'porcentaje_recaudo': round((total_recaudado / total_facturado * 100) if total_facturado > 0 else 0, 1)
            },
            recaudo_mensual=DEMO_RECAUDO_MENSUAL,
            cartera_estado=DEMO_CARTERA_ESTADO,
            metodos_pago={'Efectivo': 45, 'Transferencia': 25, 'Nequi': 15, 'Daviplata': 10, 'Otro': 5}
        )


@app.route('/pqrs', methods=['GET', 'POST'])
@roles_required('administrador')
def pqrs():
    """Sistema PQRS - tickets, KPIs y gráficos"""
    db = get_db_or_fallback()
    if db is None:
        if request.method == 'POST':
            if missing_fields('tipo', 'asunto'):
                flash('Completa el tipo y el asunto de la PQRS.', 'warning')
            else:
                flash('PQRS radicado (modo demostración).', 'success')
        # KPIs
        abiertos = len([p for p in DEMO_PQRS if p['estado'] == 'Pendiente'])
        en_proceso = len([p for p in DEMO_PQRS if p['estado'] == 'En proceso'])
        resueltos = len([p for p in DEMO_PQRS if p['estado'] == 'Resuelto'])

        # Distribución por tipo
        por_tipo = {}
        for p in DEMO_PQRS:
            por_tipo[p['tipo']] = por_tipo.get(p['tipo'], 0) + 1

        # Distribución por estado
        por_estado = {}
        for p in DEMO_PQRS:
            por_estado[p['estado']] = por_estado.get(p['estado'], 0) + 1

        return render_template('pqrs.html',
            pqrs=DEMO_PQRS,
            kpis={'abiertos': abiertos, 'en_proceso': en_proceso, 'resueltos': resueltos, 'total': len(DEMO_PQRS)},
            por_tipo=por_tipo,
            por_estado=por_estado,
            por_sector={
                'El Roble': 2,
                'La Loma': 2,
                'San José': 2,
                'El Mirador': 1,
                'Nueva Esperanza': 1,
            },
            por_prioridad={
                'Crítica': 1,
                'Alta': 3,
                'Media': 3,
                'Baja': 1,
            }
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            if missing_fields('tipo', 'asunto'):
                flash('Completa el tipo y el asunto de la PQRS.', 'warning')
                close_db(db, cursor)
                return redirect(url_for('pqrs'))
            tipo = request.form['tipo'].strip()
            asunto = request.form['asunto'].strip()
            sector = request.form.get('sector', '')
            prioridad = request.form.get('prioridad', 'Media')
            cursor.execute("SELECT COUNT(*) AS total FROM pqrs")
            total = cursor.fetchone()['total'] + 1
            codigo = f"P-{total:03d}"
            cursor.execute("""INSERT INTO pqrs (codigo, tipo, asunto, sector, prioridad, estado, fecha)
                             VALUES (%s, %s, %s, %s, %s, 'Pendiente', CURDATE())""",
                           (codigo, tipo, asunto, sector, prioridad))
            db.commit()
            flash('PQRS radicado correctamente', 'success')

        cursor.execute("SELECT * FROM pqrs ORDER BY id DESC")
        pqrs_lista = cursor.fetchall() or DEMO_PQRS

        # KPIs
        cursor.execute("SELECT estado, COUNT(*) as total FROM pqrs GROUP BY estado")
        estado_rows = cursor.fetchall()
        kpis = {row['estado'].lower().replace(' ', '_'): row['total'] for row in estado_rows}
        kpis['abiertos'] = kpis.get('pendiente', 0)
        kpis['en_proceso'] = kpis.get('en_proceso', 0)
        kpis['resueltos'] = kpis.get('resuelto', 0)
        kpis['total'] = sum(row['total'] for row in estado_rows)

        cursor.execute("SELECT tipo, COUNT(*) as total FROM pqrs GROUP BY tipo")
        por_tipo = {row['tipo']: row['total'] for row in cursor.fetchall()}

        cursor.execute("SELECT estado, COUNT(*) as total FROM pqrs GROUP BY estado")
        por_estado = {row['estado']: row['total'] for row in cursor.fetchall()}

        cursor.execute("SELECT sector, COUNT(*) as total FROM pqrs WHERE sector IS NOT NULL AND sector != '' GROUP BY sector")
        por_sector = {row['sector']: row['total'] for row in cursor.fetchall()}

        cursor.execute("SELECT prioridad, COUNT(*) as total FROM pqrs WHERE prioridad IS NOT NULL GROUP BY prioridad")
        por_prioridad = {row['prioridad']: row['total'] for row in cursor.fetchall()}

        close_db(db, cursor)
        return render_template('pqrs.html',
            pqrs=pqrs_lista,
            kpis=kpis,
            por_tipo=por_tipo,
            por_estado=por_estado,
            por_sector=por_sector,
            por_prioridad=por_prioridad
        )
    except Exception as e:
        print(f"PQRS fallback: {e}")
        close_db(db, cursor)
        abiertos = len([p for p in DEMO_PQRS if p['estado'] == 'Pendiente'])
        en_proceso = len([p for p in DEMO_PQRS if p['estado'] == 'En proceso'])
        resueltos = len([p for p in DEMO_PQRS if p['estado'] == 'Resuelto'])
        por_tipo = {}
        for p in DEMO_PQRS:
            por_tipo[p['tipo']] = por_tipo.get(p['tipo'], 0) + 1
        por_estado = {}
        for p in DEMO_PQRS:
            por_estado[p['estado']] = por_estado.get(p['estado'], 0) + 1
        return render_template('pqrs.html',
            pqrs=DEMO_PQRS,
            kpis={'abiertos': abiertos, 'en_proceso': en_proceso, 'resueltos': resueltos, 'total': len(DEMO_PQRS)},
            por_tipo=por_tipo,
            por_estado=por_estado,
            por_sector={'El Roble': 2, 'La Loma': 2, 'San José': 2, 'El Mirador': 1, 'Nueva Esperanza': 1},
            por_prioridad={'Crítica': 1, 'Alta': 3, 'Media': 3, 'Baja': 1}
        )


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', '5050')))