
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
import bcrypt
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-novacapital-2024')

# Configuración de MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'novacapital_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Configuración de sesiones
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Inicializar MySQL
mysql = MySQL(app)

# ================================
# DECORADORES
# ================================
def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            session['next_url'] = request.url
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('login'))

        if session.get('user_rol') not in ['admin', 'asesor']:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

# ================================
# FUNCIONES DE BASE DE DATOS
# ================================

def crear_usuario(nombre, email, password, tipo_documento, numero_documento, apellido, celular, rol='cliente'):
    """Crea un nuevo usuario en la base de datos"""
    try:
        cursor = mysql.connection.cursor()

        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return None, "El email ya está registrado"

        # Verificar si el documento ya existe
        cursor.execute("SELECT id FROM clientes WHERE numero_documento = %s", (numero_documento,))
        if cursor.fetchone():
            cursor.close()
            return None, "El número de documento ya está registrado"

        # Hash de la contraseña
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insertar usuario
        query_usuario = """
            INSERT INTO usuarios (nombre, email, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_usuario, (nombre, email, password_hash, rol, True))
        usuario_id = cursor.lastrowid

        # Insertar cliente
        query_cliente = """
            INSERT INTO clientes
            (tipo_documento, numero_documento, nombres, apellidos, email, celular, estado, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, 'activo', %s)
        """
        cursor.execute(query_cliente,
                     (tipo_documento, numero_documento, nombre, apellido, email, celular, usuario_id))

        mysql.connection.commit()
        cursor.close()

        return usuario_id, None

    except Exception as e:
        mysql.connection.rollback()
        return None, f"Error al crear usuario: {str(e)}"

def verificar_credenciales(email, password):
    """Verifica las credenciales de un usuario"""
    try:
        cursor = mysql.connection.cursor()
        query = """
            SELECT id, nombre, email, password_hash, rol, activo
            FROM usuarios
            WHERE email = %s
        """
        cursor.execute(query, (email,))
        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            return None, "Usuario no encontrado"

        if not usuario['activo']:
            return None, "Usuario inactivo"

        # Verificar contraseña
        if bcrypt.checkpw(password.encode('utf-8'), usuario['password_hash'].encode('utf-8')):
            return usuario, None
        else:
            return None, "Contraseña incorrecta"

    except Exception as e:
        return None, f"Error al verificar credenciales: {str(e)}"

def obtener_cliente_por_usuario(usuario_id):
    """Obtiene los datos del cliente asociado a un usuario"""
    try:
        cursor = mysql.connection.cursor()
        query = """
            SELECT * FROM clientes WHERE usuario_id = %s
        """
        cursor.execute(query, (usuario_id,))
        cliente = cursor.fetchone()
        cursor.close()
        return cliente
    except Exception as e:
        print(f"Error al obtener cliente: {str(e)}")
        return None

def crear_solicitud_prestamo(cliente_id, datos_solicitud):
    """Crea una nueva solicitud de préstamo"""
    try:
        cursor = mysql.connection.cursor()

        # Generar número de préstamo único
        year = datetime.now().year
        cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE YEAR(fecha_solicitud) = %s", (year,))
        count = cursor.fetchone()['total']
        numero_prestamo = f"PRE{year}{(count + 1):05d}"

        # Insertar préstamo
        query = """
            INSERT INTO prestamos
            (cliente_id, numero_prestamo, monto_solicitado, tasa_interes, plazo_meses,
             cuota_mensual, estado, observaciones, cuenta_bancaria, banco)
            VALUES (%s, %s, %s, %s, %s, %s, 'solicitado', %s, %s, %s)
        """

        cursor.execute(query, (
            cliente_id,
            numero_prestamo,
            datos_solicitud.get('monto_solicitado'),
            1.9,  # Tasa por defecto
            datos_solicitud.get('plazo_meses'),
            datos_solicitud.get('cuota_mensual', 0),
            datos_solicitud.get('observaciones', ''),
            datos_solicitud.get('cuenta_bancaria', ''),
            datos_solicitud.get('banco', '')
        ))

        prestamo_id = cursor.lastrowid

        # Actualizar datos del cliente si es necesario
        if datos_solicitud.get('actualizar_cliente'):
            query_update = """
                UPDATE clientes
                SET tipo_cliente = %s, entidad_empleadora = %s, salario_mensual = %s,
                    direccion = %s, ciudad = %s, departamento = %s, fecha_nacimiento = %s,
                    telefono = %s
                WHERE id = %s
            """
            cursor.execute(query_update, (
                datos_solicitud.get('tipo_cliente'),
                datos_solicitud.get('entidad_empleadora'),
                datos_solicitud.get('salario_mensual'),
                datos_solicitud.get('direccion'),
                datos_solicitud.get('ciudad'),
                datos_solicitud.get('departamento'),
                datos_solicitud.get('fecha_nacimiento'),
                datos_solicitud.get('telefono'),
                cliente_id
            ))

        mysql.connection.commit()
        cursor.close()

        return numero_prestamo, prestamo_id, None

    except Exception as e:
        mysql.connection.rollback()
        return None, None, f"Error al crear solicitud: {str(e)}"

def obtener_estadisticas_dashboard():
    """Obtiene las estadísticas para el dashboard"""
    try:
        cursor = mysql.connection.cursor()

        stats = {}

        # Total clientes activos
        cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE estado = 'activo'")
        stats['clientes_activos'] = cursor.fetchone()['total']

        # Préstamos activos
        cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'desembolsado'")
        stats['prestamos_activos'] = cursor.fetchone()['total']

        # Cartera vigente
        cursor.execute("""
            SELECT COALESCE(SUM(monto_aprobado), 0) as total
            FROM prestamos
            WHERE estado = 'desembolsado'
        """)
        stats['cartera_vigente'] = cursor.fetchone()['total']

        # Cartera en mora
        cursor.execute("""
            SELECT COALESCE(SUM(valor_cuota - valor_pagado), 0) as total
            FROM pagos
            WHERE estado IN ('mora', 'vencido')
        """)
        stats['cartera_mora'] = cursor.fetchone()['total']

        cursor.close()
        return stats

    except Exception as e:
        print(f"Error al obtener estadísticas: {str(e)}")
        return {}

# ================================
# RUTAS PRINCIPALES
# ================================

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/contacto')
def contacto():
    """Página de contacto"""
    return render_template('contacto.html')

@app.route('/requisitos')
def requisitos():
    """Página de requisitos"""
    return render_template('requisitos.html')

# ================================
# RUTAS DE AUTENTICACIÓN
# ================================

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Endpoint para verificar si el usuario está autenticado"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session.get('user_id'),
            'user_nombre': session.get('user_nombre'),
            'user_email': session.get('user_email'),
            'user_rol': session.get('user_rol')
        })
    else:
        return jsonify({
            'authenticated': False
        })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if 'user_id' in session:
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)

        if session.get('user_rol') in ['admin', 'asesor']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        usuario, error = verificar_credenciales(email, password)

        if error:
            return render_template('login.html', error=error)

        # Crear sesión
        session['user_id'] = usuario['id']
        session['user_nombre'] = usuario['nombre']
        session['user_email'] = usuario['email']
        session['user_rol'] = usuario['rol']

        if remember:
            session.permanent = True

        # Redirigir
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)

        if usuario['rol'] in ['admin', 'asesor']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('solicitud'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        tipo_documento = request.form.get('tipo_documento')
        numero_documento = request.form.get('numero_documento')
        celular = request.form.get('celular')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validaciones
        if not all([nombre, apellido, email, tipo_documento, numero_documento,
                   celular, password, confirm_password]):
            return render_template('register.html',
                                 error='Todos los campos son obligatorios')

        if password != confirm_password:
            return render_template('register.html',
                                 error='Las contraseñas no coinciden')

        if len(password) < 8:
            return render_template('register.html',
                                 error='La contraseña debe tener al menos 8 caracteres')

        # Crear usuario
        usuario_id, error = crear_usuario(
            nombre=nombre,
            email=email,
            password=password,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            apellido=apellido,
            celular=celular,
            rol='cliente'
        )

        if error:
            return render_template('register.html', error=error)

        # Login automático después del registro
        usuario, _ = verificar_credenciales(email, password)
        if usuario:
            session['user_id'] = usuario['id']
            session['user_nombre'] = usuario['nombre']
            session['user_email'] = usuario['email']
            session['user_rol'] = usuario['rol']

            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            return redirect(url_for('solicitud'))

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('index'))

# ================================
# RUTAS DE SOLICITUD
# ================================

@app.route('/solicitud', methods=['GET', 'POST'])
@login_required
def solicitud():
    """Formulario de solicitud de préstamo"""

    if request.method == 'POST':
        try:
            # Obtener datos del cliente
            cliente = obtener_cliente_por_usuario(session.get('user_id'))
            if not cliente:
                flash('Error: No se encontró información del cliente', 'error')
                return redirect(url_for('solicitud'))

            # Recopilar datos del formulario
            datos_solicitud = {
                'monto_solicitado': request.form.get('monto_solicitado'),
                'plazo_meses': request.form.get('plazo_meses'),
                'cuota_mensual': request.form.get('cuota_estimada', 0),
                'observaciones': request.form.get('observaciones', ''),
                'cuenta_bancaria': request.form.get('cuenta_bancaria', ''),
                'banco': request.form.get('banco', ''),
                # Datos adicionales del cliente
                'actualizar_cliente': True,
                'tipo_cliente': request.form.get('tipo_empleado'),
                'entidad_empleadora': request.form.get('entidad_empleadora'),
                'salario_mensual': request.form.get('salario'),
                'direccion': request.form.get('direccion'),
                'ciudad': request.form.get('ciudad'),
                'departamento': request.form.get('departamento'),
                'fecha_nacimiento': request.form.get('fecha_nacimiento'),
                'telefono': request.form.get('telefono')
            }

            # Crear solicitud
            numero_prestamo, prestamo_id, error = crear_solicitud_prestamo(
                cliente['id'],
                datos_solicitud
            )

            if error:
                flash(f'Error al crear solicitud: {error}', 'error')
                return redirect(url_for('solicitud'))

            # Redirigir a página de éxito
            flash(f'¡Solicitud creada exitosamente! Número: {numero_prestamo}', 'success')
            return redirect(url_for('solicitud_exitosa', numero=numero_prestamo))

        except Exception as e:
            flash(f'Error al procesar la solicitud: {str(e)}', 'error')
            return redirect(url_for('solicitud'))

    # GET - Mostrar formulario
    user_data = {
        'nombre': session.get('user_nombre'),
        'email': session.get('user_email')
    }

    # Obtener datos del cliente si existen
    cliente = obtener_cliente_por_usuario(session.get('user_id'))

    return render_template('solicitud.html', user=user_data, cliente=cliente)

@app.route('/solicitud-exitosa')
@login_required
def solicitud_exitosa():
    """Página de confirmación de solicitud"""
    numero = request.args.get('numero', 'N/A')
    return render_template('solicitud_exitosa.html', numero_prestamo=numero)

# ================================
# RUTAS DE ADMINISTRACIÓN
# ================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard principal del administrador"""
    stats = obtener_estadisticas_dashboard()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    """Página de reportes"""
    return render_template('admin/reportes.html')

@app.route('/admin/clientes')
@admin_required
def admin_clientes():
    """Página de gestión de clientes"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.*, u.email as usuario_email, u.activo as usuario_activo
            FROM clientes c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            ORDER BY c.fecha_registro DESC
            LIMIT 100
        """)
        clientes = cursor.fetchall()
        cursor.close()
        return render_template('admin/clientes.html', clientes=clientes)
    except Exception as e:
        flash(f'Error al cargar clientes: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/prestamos')
@admin_required
def admin_prestamos():
    """Página de gestión de préstamos"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT p.*, c.nombres, c.apellidos, c.numero_documento
            FROM prestamos p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha_solicitud DESC
            LIMIT 100
        """)
        prestamos = cursor.fetchall()
        cursor.close()
        return render_template('admin/prestamos.html', prestamos=prestamos)
    except Exception as e:
        flash(f'Error al cargar préstamos: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

# ================================
# MANEJADORES DE ERRORES
# ================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

# ================================
# PUNTO DE ENTRADA
# ================================

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )
