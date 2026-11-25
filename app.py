from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

# Si tu carpeta de páginas se llama 'templates', cambia template_folder='templates'
app = Flask(__name__, template_folder='html', static_folder='static')
app.secret_key = 'clave_secreta_veredal_antioquia'

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',          # Coloca tu contraseña de MySQL si tienes una
        database='veredal_db'
    )

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
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
    return render_template('login.html', recientes=recientes)

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form['nombre']
    documento = request.form['documento']
    telefono = request.form['telefono']
    clave = request.form['clave']

    db = get_db()
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
    db = get_db()
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
    db = get_db()
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
    db = get_db()
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
    db = get_db()
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
