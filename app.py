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


@app.template_filter('cop')
def format_cop(value):
    return f"{int(value or 0):,}".replace(',', '.')


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


DEFAULT_TARIFF_MONTHLY = 15000
PAYMENT_FREQUENCIES = ('Mensual', 'Quincenal')
DEMO_TARIFF_MONTHLY = DEFAULT_TARIFF_MONTHLY
DEMO_CARGOS_RECURRENTES = []


def parse_viviendas(values, required=False):
    viviendas = []
    seen = set()
    for value in values:
        nombre = value.strip()
        if not nombre:
            continue
        if len(nombre) > 120:
            raise ValueError('Cada casa o predio admite hasta 120 caracteres.')
        key = nombre.casefold()
        if key in seen:
            raise ValueError('No repitas el nombre de una casa o predio.')
        seen.add(key)
        viviendas.append(nombre)
    if required and not viviendas:
        raise ValueError('Registra al menos una casa o predio.')
    return viviendas


def calculate_account_summary(tarifa_mensual, frecuencia_pago, viviendas, cargos):
    tarifa_mensual = int(tarifa_mensual)
    if tarifa_mensual <= 0 or tarifa_mensual % 2:
        raise ValueError('La tarifa mensual debe ser positiva y par.')
    if frecuencia_pago not in PAYMENT_FREQUENCIES:
        raise ValueError('La frecuencia de pago no es válida.')
    valor_por_vivienda = tarifa_mensual if frecuencia_pago == 'Mensual' else tarifa_mensual // 2
    valor_viviendas = valor_por_vivienda * len(viviendas)
    valor_cargos = sum(int(cargo['valor']) for cargo in cargos)
    return {
        'cantidad_viviendas': len(viviendas),
        'valor_por_vivienda': valor_por_vivienda,
        'valor_viviendas': valor_viviendas,
        'valor_cargos': valor_cargos,
        'total': valor_viviendas + valor_cargos,
    }


def enrich_billing_account(asociado, viviendas, cargos, tarifa_mensual):
    normalized_viviendas = [
        {'identificador': vivienda} if isinstance(vivienda, str) else vivienda
        for vivienda in viviendas
    ]
    asociado = dict(asociado)
    asociado['frecuencia_pago'] = asociado.get('frecuencia_pago') or 'Mensual'
    asociado['viviendas'] = normalized_viviendas
    asociado['cargos'] = cargos
    asociado.update(calculate_account_summary(
        tarifa_mensual,
        asociado['frecuencia_pago'],
        normalized_viviendas,
        cargos
    ))
    return asociado


def load_billing_accounts(cursor, tarifa_mensual, documento=None):
    query = """SELECT id, nombre, documento, telefono, vereda, estado, frecuencia_pago
               FROM asociados"""
    params = ()
    if documento is not None:
        query += " WHERE documento=%s"
        params = (documento,)
    query += " ORDER BY nombre"
    cursor.execute(query, params)
    asociados = cursor.fetchall()
    if not asociados:
        return []

    asociado_ids = [asociado['id'] for asociado in asociados]
    placeholders = ','.join(['%s'] * len(asociado_ids))
    cursor.execute(
        f"SELECT id, asociado_id, identificador FROM viviendas WHERE asociado_id IN ({placeholders}) ORDER BY id",
        tuple(asociado_ids)
    )
    viviendas_por_asociado = {}
    for vivienda in cursor.fetchall():
        viviendas_por_asociado.setdefault(vivienda['asociado_id'], []).append(vivienda)

    cursor.execute(
        f"""SELECT id, asociado_id, descripcion, valor
            FROM cargos_recurrentes
            WHERE activo=1 AND asociado_id IN ({placeholders})
            ORDER BY id""",
        tuple(asociado_ids)
    )
    cargos_por_asociado = {}
    for cargo in cursor.fetchall():
        cargos_por_asociado.setdefault(cargo['asociado_id'], []).append(cargo)

    return [
        enrich_billing_account(
            asociado,
            viviendas_por_asociado.get(asociado['id'], []),
            cargos_por_asociado.get(asociado['id'], []),
            tarifa_mensual
        )
        for asociado in asociados
    ]


def load_demo_billing_accounts(tarifa_mensual, documento=None):
    accounts = []
    for asociado in DEMO_USUARIOS:
        if documento is not None and asociado['documento'] != documento:
            continue
        cargos = [
            cargo for cargo in DEMO_CARGOS_RECURRENTES
            if cargo['asociado_id'] == asociado['id'] and cargo['activo']
        ]
        accounts.append(enrich_billing_account(
            asociado,
            asociado.get('viviendas', []),
            cargos,
            tarifa_mensual
        ))
    return accounts


# ============================================================
# FALLBACK DEMO DATA - Colombian Rural Aqueduct Community
# ============================================================

DEMO_USUARIOS = [
    {'id': 1, 'nombre': 'Carlos Méndez', 'documento': '1.023.456.789', 'telefono': '310 234 5678', 'vereda': 'El Roble', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-10'},
    {'id': 2, 'nombre': 'Ana Torres', 'documento': '1.098.765.432', 'telefono': '320 111 2233', 'vereda': 'La Loma', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-12'},
    {'id': 3, 'nombre': 'Jorge Herrera', 'documento': '1.145.678.901', 'telefono': '315 789 0123', 'vereda': 'San José', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-08'},
    {'id': 4, 'nombre': 'María Rojas', 'documento': '1.202.345.678', 'telefono': '300 456 7890', 'vereda': 'El Mirador', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-14'},
    {'id': 5, 'nombre': 'Luis Gómez', 'documento': '1.334.567.890', 'telefono': '312 345 6789', 'vereda': 'El Roble', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-05'},
    {'id': 6, 'nombre': 'Patricia Vélez', 'documento': '1.456.789.012', 'telefono': '318 901 2345', 'vereda': 'La Loma', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Suspendido', 'ultimo_pago': '2025-06-20'},
    {'id': 7, 'nombre': 'Roberto Díaz', 'documento': '1.567.890.123', 'telefono': '314 567 8901', 'vereda': 'San José', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-11'},
    {'id': 8, 'nombre': 'Carmen López', 'documento': '1.678.901.234', 'telefono': '311 678 9012', 'vereda': 'El Mirador', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-13'},
    {'id': 9, 'nombre': 'Fernando Castro', 'documento': '1.789.012.345', 'telefono': '319 789 0123', 'vereda': 'El Roble', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-09'},
    {'id': 10, 'nombre': 'Gloria Muñoz', 'documento': '1.890.123.456', 'telefono': '316 890 1234', 'vereda': 'La Loma', 'viviendas': [], 'frecuencia_pago': 'Mensual', 'estado': 'Activo', 'ultimo_pago': '2025-07-15'},
]

DEMO_FACTURAS = []

DEMO_PQRS = [
    {'codigo': 'P-001', 'tipo': 'Petición', 'asunto': 'Solicitud de nueva conexión domiciliaria', 'sector': 'El Roble', 'descripcion': 'Nueva vivienda requiere conexión a red matriz', 'prioridad': 'Media', 'fecha': '2025-07-10', 'estado': 'En proceso', 'responsable': 'Técnico Carlos'},
    {'codigo': 'P-002', 'tipo': 'Queja', 'asunto': 'Agua con mal olor y color amarillento', 'sector': 'La Loma', 'descripcion': 'Varios usuarios reportan olor a azufre desde hace 3 días', 'prioridad': 'Alta', 'fecha': '2025-07-12', 'estado': 'En proceso', 'responsable': 'Químico María'},
    {'codigo': 'P-003', 'tipo': 'Reclamo', 'asunto': 'Cobro aplicado de forma incorrecta', 'sector': 'San José', 'descripcion': 'El valor cobrado no coincide con la tarifa informada.', 'prioridad': 'Alta', 'fecha': '2025-07-08', 'estado': 'Resuelto', 'responsable': 'Facturación'},
    {'codigo': 'P-004', 'tipo': 'Solicitud de Reparación', 'asunto': 'Fuga en tubería madre sector El Roble', 'sector': 'El Roble', 'descripcion': 'Fuga visible a 50m de la bocatoma, pérdida estimada 15 L/min', 'prioridad': 'Crítica', 'fecha': '2025-07-14', 'estado': 'En proceso', 'responsable': 'Cuadrilla A'},
    {'codigo': 'P-005', 'tipo': 'Petición', 'asunto': 'Revisión de conexión domiciliaria', 'sector': 'El Mirador', 'descripcion': 'El usuario solicita revisar la conexión de su vivienda.', 'prioridad': 'Baja', 'fecha': '2025-07-05', 'estado': 'Pendiente', 'responsable': 'Técnico Luis'},
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

DEMO_ACTIVIDAD_RECIENTE = [
    {'icono': '💰', 'tipo': 'success', 'titulo': 'Pago recibido', 'detalle': 'Carlos Méndez - $58.500 - Hace 15 min', 'estado': 'Completado'},
    {'icono': '💧', 'tipo': 'info', 'titulo': 'Nivel de tanque actualizado', 'detalle': 'Tanque principal - Estado operativo', 'estado': 'Registrado'},
    {'icono': '⚡', 'tipo': 'warning', 'titulo': 'Corte programado', 'detalle': 'Sector La Loma - Mañana 8:00 AM - Mantenimiento', 'estado': 'Programado'},
    {'icono': '🚨', 'tipo': 'danger', 'titulo': 'PQRS Urgente', 'detalle': 'Fuga en tubería madre El Roble - Sin resolver', 'estado': 'En proceso'},
    {'icono': '📋', 'tipo': 'info', 'titulo': 'Nueva solicitud', 'detalle': 'Gloria Muñoz - Revisión de conexión domiciliaria', 'estado': 'Pendiente'},
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
            session['documento'] = account['documento']
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
        session['documento'] = user['documento']
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
        session['documento'] = documento
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
        session['documento'] = documento
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
        db = get_db_or_fallback()
        tarifa_mensual = DEFAULT_TARIFF_MONTHLY
        if db is not None:
            cursor = None
            try:
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT tarifa_mensual FROM configuracion_facturacion WHERE id=1")
                setting = cursor.fetchone()
                if setting:
                    tarifa_mensual = int(setting['tarifa_mensual'])
            except Exception as e:
                print(f"Tarifa de registro de asociado: {e}")
                flash('No se pudo consultar la tarifa vigente.', 'error')
            finally:
                close_db(db, cursor)
        return render_template('nuevo_asociado.html', tarifa_mensual=tarifa_mensual)

    required = missing_fields('nombre', 'documento')
    if required:
        flash('Completa el nombre y el documento del asociado.', 'warning')
        return redirect(url_for('nuevo_asociado'))

    nombre = request.form['nombre'].strip()
    documento = request.form['documento'].strip()
    telefono = request.form.get('telefono', '').strip()
    vereda = request.form.get('vereda', '').strip()
    frecuencia_pago = request.form.get('frecuencia_pago', '').strip()
    try:
        viviendas = parse_viviendas(request.form.getlist('viviendas[]'), required=True)
    except ValueError as e:
        flash(str(e), 'warning')
        return redirect(url_for('nuevo_asociado'))
    if frecuencia_pago not in PAYMENT_FREQUENCIES:
        flash('Selecciona una frecuencia de pago válida.', 'warning')
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
            'viviendas': viviendas,
            'frecuencia_pago': frecuencia_pago,
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
        db.start_transaction()
        cursor.execute(
            """INSERT INTO asociados (nombre, documento, telefono, vereda, frecuencia_pago, estado)
               VALUES (%s, %s, %s, %s, %s, 'Activo')""",
            (nombre, documento, telefono, vereda, frecuencia_pago)
        )
        asociado_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO viviendas (asociado_id, identificador) VALUES (%s, %s)",
            [(asociado_id, vivienda) for vivienda in viviendas]
        )
        db.commit()
        flash('Asociado registrado correctamente.', 'success')
    except Exception as e:
        db.rollback()
        print(f"Nuevo asociado: {e}")
        flash('No se pudo registrar el asociado. Verifica que la migración de viviendas esté aplicada.', 'error')
    finally:
        close_db(db, cursor)
    return redirect(url_for('nuevo_asociado'))


@app.route('/asociados/<int:asociado_id>/viviendas', methods=['POST'])
@roles_required('administrador')
def actualizar_viviendas(asociado_id):
    frecuencia_pago = request.form.get('frecuencia_pago', '').strip()
    try:
        viviendas = parse_viviendas(request.form.get('viviendas', '').splitlines())
    except ValueError as e:
        flash(str(e), 'warning')
        return redirect(url_for('productos'))
    if frecuencia_pago not in PAYMENT_FREQUENCIES:
        flash('Selecciona una frecuencia de pago válida.', 'warning')
        return redirect(url_for('productos'))

    db = get_db_or_fallback()
    if db is None:
        asociado = next((a for a in DEMO_USUARIOS if a['id'] == asociado_id), None)
        if asociado is None:
            flash('No se encontró el asociado.', 'warning')
        else:
            asociado['viviendas'] = viviendas
            asociado['frecuencia_pago'] = frecuencia_pago
            flash('Viviendas y frecuencia de pago actualizadas en modo demostración.', 'success')
        return redirect(url_for('productos'))

    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM asociados WHERE id=%s", (asociado_id,))
        if cursor.fetchone() is None:
            flash('No se encontró el asociado.', 'warning')
            return redirect(url_for('productos'))
        db.start_transaction()
        cursor.execute(
            "UPDATE asociados SET frecuencia_pago=%s WHERE id=%s",
            (frecuencia_pago, asociado_id)
        )
        cursor.execute("DELETE FROM viviendas WHERE asociado_id=%s", (asociado_id,))
        if viviendas:
            cursor.executemany(
                "INSERT INTO viviendas (asociado_id, identificador) VALUES (%s, %s)",
                [(asociado_id, vivienda) for vivienda in viviendas]
            )
        db.commit()
        flash('Viviendas y frecuencia de pago actualizadas.', 'success')
    except Exception as e:
        db.rollback()
        print(f"Actualizar viviendas: {e}")
        flash('No se pudieron guardar las viviendas. Revisa la migración de facturación.', 'error')
    finally:
        close_db(db, cursor)
    return redirect(url_for('productos'))


@app.route('/mi-cuenta')
@roles_required('usuario')
def mi_cuenta():
    documento = session.get('documento')
    if not documento:
        flash('Tu sesión no tiene un documento asociado. Vuelve a ingresar.', 'warning')
        return redirect(url_for('login'))

    db = get_db_or_fallback()
    tarifa_mensual = DEFAULT_TARIFF_MONTHLY
    asociado = None
    if db is None:
        accounts = load_demo_billing_accounts(tarifa_mensual, documento)
        asociado = accounts[0] if accounts else None
    else:
        cursor = None
        try:
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT tarifa_mensual FROM configuracion_facturacion WHERE id=1")
            setting = cursor.fetchone()
            tarifa_mensual = int(setting['tarifa_mensual']) if setting else DEFAULT_TARIFF_MONTHLY
            accounts = load_billing_accounts(cursor, tarifa_mensual, documento)
            asociado = accounts[0] if accounts else None
        except Exception as e:
            print(f"Cuenta del asociado: {e}")
            flash('No se pudo cargar el estado de cuenta. Verifica la migración de facturación.', 'error')
        finally:
            close_db(db, cursor)

    return render_template(
        'mi_cuenta.html',
        asociado=asociado,
        tarifa_mensual=tarifa_mensual
    )


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


@app.route('/productos')
@app.route('/asociados')
@roles_required('administrador')
def productos():
    """Asociados, viviendas y frecuencia de pago."""
    db = get_db_or_fallback()
    if db is None:
        asociados = load_demo_billing_accounts(DEMO_TARIFF_MONTHLY)
        veredas = {}
        frecuencias_pago = {}
        for asociado in asociados:
            veredas[asociado['vereda']] = veredas.get(asociado['vereda'], 0) + 1
            frecuencia = asociado['frecuencia_pago']
            frecuencias_pago[frecuencia] = frecuencias_pago.get(frecuencia, 0) + 1
        return render_template('productos.html',
            asociados=asociados,
            veredas=veredas,
            frecuencias_pago=frecuencias_pago
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT tarifa_mensual FROM configuracion_facturacion WHERE id=1")
        setting = cursor.fetchone()
        tarifa_mensual = int(setting['tarifa_mensual']) if setting else DEFAULT_TARIFF_MONTHLY
        asociados = load_billing_accounts(cursor, tarifa_mensual)
        cursor.execute("SELECT vereda, COUNT(*) as total FROM asociados GROUP BY vereda")
        veredas = {row['vereda'] or 'Sin vereda': row['total'] for row in cursor.fetchall()}
        frecuencias_pago = {}
        for asociado in asociados:
            frecuencia = asociado['frecuencia_pago']
            frecuencias_pago[frecuencia] = frecuencias_pago.get(frecuencia, 0) + 1

        close_db(db, cursor)
        return render_template('productos.html',
            asociados=asociados,
            veredas=veredas,
            frecuencias_pago=frecuencias_pago
        )
    except Exception as e:
        print(f"Productos fallback: {e}")
        close_db(db, cursor)
        asociados = load_demo_billing_accounts(DEMO_TARIFF_MONTHLY)
        veredas = {}
        frecuencias_pago = {}
        for asociado in asociados:
            veredas[asociado['vereda']] = veredas.get(asociado['vereda'], 0) + 1
            frecuencia = asociado['frecuencia_pago']
            frecuencias_pago[frecuencia] = frecuencias_pago.get(frecuencia, 0) + 1
        return render_template('productos.html',
            asociados=asociados,
            veredas=veredas,
            frecuencias_pago=frecuencias_pago
        )


@app.route('/agua')
@roles_required('administrador')
def agua():
    """Estado operativo de tanques, caudal y calidad del agua."""
    db = get_db_or_fallback()
    if db is None:
        return render_template('agua2.html', telemetria=DEMO_TELEMETRIA)

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM telemetria ORDER BY id DESC LIMIT 1")
        telemetria = cursor.fetchone() or DEMO_TELEMETRIA
        close_db(db, cursor)
        return render_template('agua2.html', telemetria=telemetria)
    except Exception as e:
        print(f"Agua fallback: {e}")
        close_db(db, cursor)
        return render_template('agua2.html', telemetria=DEMO_TELEMETRIA)


@app.route('/facturacion', methods=['GET', 'POST'])
@roles_required('administrador')
def facturacion():
    """Tarifas por vivienda, cobros recurrentes e historial de pagos."""
    global DEMO_TARIFF_MONTHLY
    db = get_db_or_fallback()
    if db is None:
        if request.method == 'POST':
            action = request.form.get('action', '')
            if action == 'update_tariff':
                try:
                    tarifa = int(request.form.get('tarifa_mensual', ''))
                    if tarifa <= 0 or tarifa % 2:
                        raise ValueError
                except ValueError:
                    flash('La tarifa mensual debe ser un valor entero, positivo y par para calcular la quincena.', 'warning')
                else:
                    DEMO_TARIFF_MONTHLY = tarifa
                    flash('Tarifa actualizada en modo demostración.', 'success')
            elif action == 'add_charge':
                descripcion = request.form.get('descripcion', '').strip()
                try:
                    asociado_id = int(request.form.get('asociado_id', ''))
                    valor = int(request.form.get('valor', ''))
                except ValueError:
                    flash('Selecciona un asociado y un valor válido.', 'warning')
                else:
                    asociado = next((a for a in DEMO_USUARIOS if a['id'] == asociado_id), None)
                    if not descripcion or len(descripcion) > 160 or valor <= 0 or asociado is None:
                        flash('Completa una descripción válida y un valor mayor que cero.', 'warning')
                    else:
                        DEMO_CARGOS_RECURRENTES.append({
                            'id': max((c['id'] for c in DEMO_CARGOS_RECURRENTES), default=0) + 1,
                            'asociado_id': asociado_id,
                            'descripcion': descripcion,
                            'valor': valor,
                            'activo': 1,
                        })
                        flash('Aporte recurrente agregado en modo demostración.', 'success')
            elif action == 'deactivate_charge':
                try:
                    cargo_id = int(request.form.get('cargo_id', ''))
                except ValueError:
                    flash('El aporte seleccionado no es válido.', 'warning')
                else:
                    cargo = next((c for c in DEMO_CARGOS_RECURRENTES if c['id'] == cargo_id), None)
                    if cargo:
                        cargo['activo'] = 0
                        flash('Aporte recurrente retirado en modo demostración.', 'success')
                    else:
                        flash('No se encontró el aporte.', 'warning')
            else:
                flash('La acción de facturación solicitada no es válida.', 'warning')
            return redirect(url_for('facturacion'))

        asociados = load_demo_billing_accounts(DEMO_TARIFF_MONTHLY)
        return render_template(
            'facturacion.html',
            asociados=asociados,
            tarifa_mensual=DEMO_TARIFF_MONTHLY,
            facturas=DEMO_FACTURAS,
            migration_error=False
        )

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            action = request.form.get('action', '')
            if action == 'update_tariff':
                try:
                    tarifa = int(request.form.get('tarifa_mensual', ''))
                    if tarifa <= 0 or tarifa % 2:
                        raise ValueError
                except ValueError:
                    flash('La tarifa mensual debe ser un valor entero, positivo y par para calcular la quincena.', 'warning')
                else:
                    cursor.execute(
                        "UPDATE configuracion_facturacion SET tarifa_mensual=%s WHERE id=1",
                        (tarifa,)
                    )
                    db.commit()
                    flash('Tarifa mensual actualizada.', 'success')
            elif action == 'add_charge':
                descripcion = request.form.get('descripcion', '').strip()
                try:
                    asociado_id = int(request.form.get('asociado_id', ''))
                    valor = int(request.form.get('valor', ''))
                except ValueError:
                    flash('Selecciona un asociado y un valor válido.', 'warning')
                else:
                    cursor.execute("SELECT id FROM asociados WHERE id=%s", (asociado_id,))
                    if not descripcion or len(descripcion) > 160 or valor <= 0 or cursor.fetchone() is None:
                        flash('Completa una descripción válida, un asociado y un valor mayor que cero.', 'warning')
                    else:
                        cursor.execute(
                            """INSERT INTO cargos_recurrentes (asociado_id, descripcion, valor, activo)
                               VALUES (%s, %s, %s, 1)""",
                            (asociado_id, descripcion, valor)
                        )
                        db.commit()
                        flash('Aporte recurrente agregado.', 'success')
            elif action == 'deactivate_charge':
                try:
                    cargo_id = int(request.form.get('cargo_id', ''))
                except ValueError:
                    flash('El aporte seleccionado no es válido.', 'warning')
                else:
                    cursor.execute(
                        "UPDATE cargos_recurrentes SET activo=0 WHERE id=%s AND activo=1",
                        (cargo_id,)
                    )
                    db.commit()
                    flash('Aporte recurrente retirado.' if cursor.rowcount else 'No se encontró el aporte activo.', 'success' if cursor.rowcount else 'warning')
            elif action == 'pay_invoice':
                try:
                    invoice_id = int(request.form.get('id_factura', ''))
                except ValueError:
                    flash('La factura seleccionada no es válida.', 'warning')
                else:
                    cursor.execute(
                        """UPDATE facturas SET estado='Pagada', fecha_pago=CURDATE()
                           WHERE id=%s AND estado!='Pagada'""",
                        (invoice_id,)
                    )
                    db.commit()
                    flash('Pago histórico registrado.' if cursor.rowcount else 'No se encontró una factura pendiente.', 'success' if cursor.rowcount else 'warning')
            else:
                flash('La acción de facturación solicitada no es válida.', 'warning')
            close_db(db, cursor)
            return redirect(url_for('facturacion'))

        cursor.execute("SELECT tarifa_mensual FROM configuracion_facturacion WHERE id=1")
        setting = cursor.fetchone()
        tarifa_mensual = int(setting['tarifa_mensual']) if setting else DEFAULT_TARIFF_MONTHLY
        asociados = load_billing_accounts(cursor, tarifa_mensual)
        cursor.execute(
            """SELECT id, numero, asociado, documento, fecha, periodo, valor, estado, fecha_pago, metodo
               FROM facturas ORDER BY id DESC LIMIT 100"""
        )
        facturas = cursor.fetchall()
        close_db(db, cursor)
        return render_template(
            'facturacion.html',
            asociados=asociados,
            tarifa_mensual=tarifa_mensual,
            facturas=facturas,
            migration_error=False
        )
    except Exception as e:
        print(f"Facturación fallback: {e}")
        close_db(db, cursor)
        return render_template('facturacion.html',
            asociados=[],
            tarifa_mensual=DEFAULT_TARIFF_MONTHLY,
            facturas=[],
            migration_error=True
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