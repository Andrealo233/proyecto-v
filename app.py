from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

# Si tu carpeta de páginas se llama 'templates', cambia template_folder='templates'
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'clave_secreta_veredal_antioquia'

DB_AVAILABLE = False

def get_db():
    global DB_AVAILABLE
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',          # Coloca tu contraseña de MySQL si tienes una
            database='veredal_db'
        )
        DB_AVAILABLE = True
        return conn
    except Error as e:
        DB_AVAILABLE = False
        print(f"Database connection failed: {e}")
        return None

def get_db_or_fallback():
    db = get_db()
    if db is None:
        flash('Base de datos no disponible. Funcionando en modo demostración.', 'warning')
    return db

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db_or_fallback()
    if db is None:
        recientes = [
            {'nombre': 'Juan Pérez', 'documento': '1.234.567.890'},
            {'nombre': 'María López', 'documento': '1.098.765.432'},
        ]
        if request.method == 'POST':
            session['usuario'] = request.form['usuario']
            return redirect(url_for('dashboard'))
        return render_template('secion.html', recientes=recientes)

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        cursor.execute("SELECT * FROM usuarios WHERE (nombre=%s OR documento=%s) AND clave=%s", (usuario, usuario, clave))
        user = cursor.fetchone()
        if user:
            session['usuario'] = user['nombre']
            cursor.close()
            db.close()
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    cursor.execute("SELECT nombre, documento FROM usuarios ORDER BY id DESC LIMIT 4")
    recientes = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('secion.html', recientes=recientes)

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form['nombre']
    documento = request.form['documento']
    telefono = request.form['telefono']
    clave = request.form['clave']

    db = get_db_or_fallback()
    if db is None:
        session['usuario'] = nombre
        flash('Registro exitoso (modo demo)', 'success')
        return redirect(url_for('dashboard'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE documento=%s OR nombre=%s", (documento, nombre))
    existente = cursor.fetchone()

    if existente:
        flash(f"La persona {existente['nombre']} (Doc: {existente['documento']}) ya está registrada.", 'warning')
    else:
        cursor.execute("INSERT INTO usuarios (nombre, documento, telefono, clave) VALUES (%s, %s, %s, %s)",
                       (nombre, documento, telefono, clave))
        db.commit()
        session['usuario'] = nombre
        flash('Registro exitoso', 'success')
        cursor.close()
        db.close()
        return redirect(url_for('dashboard'))

    cursor.close()
    db.close()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/productos', methods=['GET', 'POST'])
def productos():
    db = get_db_or_fallback()
    if db is None:
        lista = [
            {'id': 1, 'nombre': 'Juan Pérez', 'documento': '1.234.567.890', 'telefono': '310 456 7890', 'estado': 'Activo'},
            {'id': 2, 'nombre': 'María López', 'documento': '1.098.765.432', 'telefono': '320 111 2233', 'estado': 'Activo'},
        ]
        if request.method == 'POST':
            flash('Asociado agregado (modo demo)', 'success')
        return render_template('productos.html', asociados=lista)

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        nombre = request.form['nombre']
        documento = request.form['documento']
        telefono = request.form['telefono']
        cursor.execute("INSERT IGNORE INTO asociados (nombre, documento, telefono) VALUES (%s, %s, %s)",
                       (nombre, documento, telefono))
        db.commit()
    cursor.execute("SELECT * FROM asociados ORDER BY id DESC")
    lista = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('productos.html', asociados=lista)

@app.route('/agua', methods=['GET', 'POST'])
def agua():
    db = get_db_or_fallback()
    if db is None:
        lecturas = [
            {'servicio': 'AV-001 · Juan Pérez (M-101)', 'lectura_anterior': 1200, 'lectura_actual': 1220, 'consumo': 20, 'fecha': '2025-07-15 10:30:00'},
            {'servicio': 'AV-002 · María López (M-102)', 'lectura_anterior': 850, 'lectura_actual': 875, 'consumo': 25, 'fecha': '2025-07-14 09:15:00'},
        ]
        if request.method == 'POST':
            flash('Lectura registrada (modo demo)', 'success')
        return render_template('agua2.html', lecturas=lecturas)

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        servicio = request.form['servicio']
        ant = int(request.form['lectura_anterior'])
        act = int(request.form['lectura_actual'])
        consumo = max(0, act - ant)
        cursor.execute("INSERT INTO lecturas (servicio, lectura_anterior, lectura_actual, consumo) VALUES (%s, %s, %s, %s)",
                       (servicio, ant, act, consumo))
        db.commit()
    cursor.execute("SELECT * FROM lecturas ORDER BY id DESC LIMIT 6")
    lecturas = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('agua2.html', lecturas=lecturas)

@app.route('/facturacion', methods=['GET', 'POST'])
def facturacion():
    db = get_db_or_fallback()
    if db is None:
        facturas = [
            {'id': 1, 'numero': 'FV-2025-001', 'asociado': 'Juan Pérez', 'valor': 55000, 'estado': 'Pagada'},
            {'id': 2, 'numero': 'FV-2025-002', 'asociado': 'María López', 'valor': 48000, 'estado': 'Pendiente'},
        ]
        if request.method == 'POST':
            flash('Pago registrado (modo demo)', 'success')
        return render_template('facturacion.html', facturas=facturas)

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        id_factura = request.form['id_factura']
        cursor.execute("UPDATE facturas SET estado='Pagada' WHERE id=%s", (id_factura,))
        db.commit()
    cursor.execute("SELECT * FROM facturas")
    facturas = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('facturacion.html', facturas=facturas)

@app.route('/pqrs', methods=['GET', 'POST'])
def pqrs():
    db = get_db_or_fallback()
    if db is None:
        lista_pqrs = [
            {'codigo': 'P-001', 'tipo': 'Petición', 'asunto': 'Solicitud de nueva conexión', 'estado': 'En proceso'},
            {'codigo': 'P-002', 'tipo': 'Queja', 'asunto': 'Agua con mal olor', 'estado': 'Resuelto'},
            {'codigo': 'P-003', 'tipo': 'Reclamo', 'asunto': 'Factura incorrecta', 'estado': 'En proceso'},
        ]
        if request.method == 'POST':
            flash('PQRS radicado (modo demo)', 'success')
        return render_template('pqrs.html', pqrs=lista_pqrs)

    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        tipo = request.form['tipo']
        asunto = request.form['asunto']
        cursor.execute("SELECT COUNT(*) AS total FROM pqrs")
        total = cursor.fetchone()['total'] + 1
        codigo = f"P-00{total}"
        cursor.execute("INSERT INTO pqrs (codigo, tipo, asunto) VALUES (%s, %s, %s)", (codigo, tipo, asunto))
        db.commit()
    cursor.execute("SELECT * FROM pqrs ORDER BY id DESC")
    lista_pqrs = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('pqrs.html', pqrs=lista_pqrs)

if __name__ == '__main__':
    app.run(debug=True)
