from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_file
from flask_mysqldb import MySQL
import bcrypt
import os
import csv
import io
import secrets
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from logger import auth_logger, loan_logger, admin_logger

# Cargar variables de entorno
load_dotenv()

# ================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-novacapital-2024')

# Configuración de MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'novacapital')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Novacapital123$')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'novacapital_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Configuración de sesiones
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Configuración de uploads
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
DOCS_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'docs')
os.makedirs(DOCS_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_DOC_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(pw: str, stored_hash) -> bool:
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    return bcrypt.checkpw(pw.encode('utf-8'), stored_hash)

def make_csv_response(filename: str, headers: list, rows: list):
    """Construye una respuesta HTTP con contenido CSV listo para descarga."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

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

def crear_usuario(nombres, email, password, tipo_documento, numero_documento,
                  apellidos, celular, rol='cliente',
                  fecha_nacimiento=None, telefono=None, direccion=None,
                  ciudad=None, departamento=None, tipo_cliente=None,
                  entidad_empleadora=None, salario_mensual=None):
    try:
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return None, "El email ya está registrado"

        cursor.execute("SELECT id FROM clientes WHERE numero_documento = %s", (numero_documento,))
        if cursor.fetchone():
            cursor.close()
            return None, "El número de documento ya está registrado"

        password_hash_str = hash_password(password)

        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol, activo) VALUES (%s, %s, %s, %s, %s)",
            (nombres, email, password_hash_str, rol, True)
        )
        usuario_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO clientes
            (usuario_id, tipo_documento, numero_documento, nombres, apellidos,
             email, celular, fecha_nacimiento, telefono, direccion, ciudad,
             departamento, tipo_cliente, entidad_empleadora, salario_mensual, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'activo')
        """, (
            usuario_id, tipo_documento, numero_documento, nombres, apellidos,
            email, celular, fecha_nacimiento, telefono, direccion, ciudad,
            departamento, tipo_cliente, entidad_empleadora, salario_mensual
        ))

        mysql.connection.commit()
        cursor.close()
        return usuario_id, None

    except Exception as e:
        mysql.connection.rollback()
        return None, f"Error al crear usuario: {str(e)}"

def verificar_credenciales(email, password):
    """Devuelve (usuario_dict, None) si las credenciales son válidas, o (None, mensaje_error)."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT id, nombre, email, password_hash, rol, activo FROM usuarios WHERE email = %s",
            (email,)
        )
        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            return None, "Usuario no encontrado"
        if not usuario['activo']:
            return None, "Usuario inactivo"
        if check_password(password, usuario['password_hash']):
            return usuario, None
        return None, "Contraseña incorrecta"

    except Exception as e:
        return None, f"Error al verificar credenciales: {str(e)}"

def obtener_cliente_por_usuario(usuario_id):
    """Devuelve el dict del cliente asociado al usuario_id, o None si no existe."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM clientes WHERE usuario_id = %s", (usuario_id,))
        cliente = cursor.fetchone()
        cursor.close()
        return cliente
    except Exception:
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
    if 'user_id' in session:
        return redirect_by_role()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')

        usuario, error = verificar_credenciales(email, password)

        if error:
            auth_logger.log_login(email, request.remote_addr, False, razon=error)
            return render_template('login.html', error=error)

        session['user_id']     = usuario['id']
        session['user_nombre'] = usuario['nombre']
        session['user_email']  = usuario['email']
        session['user_rol']    = usuario['rol']

        if remember:
            session.permanent = True

        auth_logger.log_login(email, request.remote_addr, True,
                              user_id=usuario['id'], rol=usuario['rol'])
        return redirect_by_role()

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role()
    
    if request.method == 'POST':
        # Campos obligatorios (nombres nuevos del formulario)
        nombres          = request.form.get('nombres', '').strip()
        apellidos        = request.form.get('apellidos', '').strip()
        email            = request.form.get('email', '').strip()
        tipo_documento   = request.form.get('tipo_documento', '').strip()
        numero_documento = request.form.get('numero_documento', '').strip()
        fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()
        celular          = request.form.get('celular', '').strip()
        tipo_cliente     = request.form.get('tipo_cliente', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Campos opcionales
        telefono           = request.form.get('telefono', '').strip() or None
        direccion          = request.form.get('direccion', '').strip() or None
        ciudad             = request.form.get('ciudad', '').strip() or None
        departamento       = request.form.get('departamento', '').strip() or None
        entidad_empleadora = request.form.get('entidad_empleadora', '').strip() or None
        salario_mensual    = request.form.get('salario_mensual', '').strip() or None

        # Validaciones
        if not all([nombres, apellidos, email, tipo_documento, numero_documento,
                    fecha_nacimiento, celular, tipo_cliente, password, confirm_password]):
            return render_template('register.html',
                                   error='Todos los campos obligatorios deben completarse')

        if password != confirm_password:
            return render_template('register.html', error='Las contraseñas no coinciden')

        if len(password) < 8:
            return render_template('register.html',
                                   error='La contraseña debe tener al menos 8 caracteres')

        usuario_id, error = crear_usuario(
            nombres=nombres,
            email=email,
            password=password,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            apellidos=apellidos,
            celular=celular,
            rol='cliente',
            fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
            telefono=telefono,
            direccion=direccion,
            ciudad=ciudad,
            departamento=departamento,
            tipo_cliente=tipo_cliente,
            entidad_empleadora=entidad_empleadora,
            salario_mensual=salario_mensual
        )

        if error:
            return render_template('register.html', error=error)

        usuario, _ = verificar_credenciales(email, password)
        if usuario:
            session['user_id']     = usuario['id']
            session['user_nombre'] = usuario['nombre']
            session['user_email']  = usuario['email']
            session['user_rol']    = usuario['rol']
            auth_logger.log_register(usuario['id'], email, request.remote_addr)
            return redirect_by_role()

        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    nombre = session.get('user_nombre', 'Usuario')
    auth_logger.log_logout(session.get('user_id'), session.get('user_email'), request.remote_addr)
    session.clear()
    flash(f'Hasta pronto, {nombre}. Sesión cerrada correctamente.', 'success')
    return redirect(url_for('index'))


# ================================
# RECUPERACIÓN DE CONTRASEÑA
# ================================

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Página de recuperación de contraseña"""
    reset_link = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            return render_template('forgot_password.html', error='Ingresa tu correo electrónico')

        try:
            cursor = mysql.connection.cursor()

            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expira_en TIMESTAMP NOT NULL,
                    usado TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("SELECT id, email FROM usuarios WHERE email = %s AND activo = 1", (email,))
            usuario = cursor.fetchone()

            if usuario:
                token = secrets.token_urlsafe(32)   # 256 bits de entropía
                expira_en = datetime.now() + timedelta(hours=1)

                # Invalidar tokens anteriores del usuario
                cursor.execute("UPDATE password_resets SET usado = 1 WHERE usuario_id = %s AND usado = 0", (usuario['id'],))

                cursor.execute("""
                    INSERT INTO password_resets (usuario_id, token, expira_en, usado)
                    VALUES (%s, %s, %s, 0)
                """, (usuario['id'], token, expira_en))
                mysql.connection.commit()

                base_url = request.host_url.rstrip('/')
                reset_link = f"{base_url}/reset-password/{token}"

            cursor.close()

            # Siempre mostrar el formulario de éxito para no revelar si el email existe
            return render_template('forgot_password.html', email_enviado=True, reset_link=reset_link, email=email)

        except Exception as e:
            return render_template('forgot_password.html', error=f'Error al procesar la solicitud: {str(e)}')

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para restablecer la contraseña"""
    try:
        cursor = mysql.connection.cursor()

        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                token VARCHAR(64) NOT NULL UNIQUE,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expira_en TIMESTAMP NOT NULL,
                usado TINYINT(1) DEFAULT 0,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            SELECT pr.*, u.email
            FROM password_resets pr
            JOIN usuarios u ON u.id = pr.usuario_id
            WHERE pr.token = %s AND pr.usado = 0 AND pr.expira_en > NOW()
        """, (token,))
        reset_record = cursor.fetchone()

        if not reset_record:
            cursor.close()
            return render_template('reset_password.html', token_invalido=True)

        if request.method == 'POST':
            password_nueva = request.form.get('password_nueva', '')
            confirmar = request.form.get('confirmar', '')

            if len(password_nueva) < 8:
                cursor.close()
                return render_template('reset_password.html', token=token, error='La contraseña debe tener al menos 8 caracteres')

            if password_nueva != confirmar:
                cursor.close()
                return render_template('reset_password.html', token=token, error='Las contraseñas no coinciden')

            password_hash = hash_password(password_nueva)

            cursor.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", (password_hash, reset_record['usuario_id']))
            cursor.execute("UPDATE password_resets SET usado = 1 WHERE token = %s", (token,))
            mysql.connection.commit()
            cursor.close()

            flash('Contraseña actualizada correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))

        cursor.close()
        return render_template('reset_password.html', token=token, email=reset_record['email'])

    except Exception as e:
        flash(f'Error al procesar la solicitud: {str(e)}', 'error')
        return redirect(url_for('forgot_password'))


# ================================================
# FUNCIÓN AUXILIAR PARA REDIRECCIÓN POR ROL
# ================================================

def redirect_by_role():
    """Redirige al dashboard correcto según el rol del usuario"""
    rol = session.get('user_rol', 'cliente')
    
    if rol == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif rol == 'asesor':
        return redirect(url_for('asesor_dashboard'))
    else:  # cliente
        return redirect(url_for('cliente_dashboard'))



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
                'cuota_mensual': request.form.get('cuota_estimada', '0').replace('$', '').replace(',', ''),
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

            loan_logger.log_nueva_solicitud(
                prestamo_id, numero_prestamo, cliente['id'],
                datos_solicitud.get('monto_solicitado'),
                session.get('user_id'), request.remote_addr
            )

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
    try:
        cursor = mysql.connection.cursor()
        
        # Estadísticas generales
        stats = {}
        
        # Total clientes
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        stats['total_clientes'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE estado = 'activo'")
        stats['clientes_activos'] = cursor.fetchone()['total']
        
        # Solicitudes pendientes
        cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'solicitado'")
        stats['solicitudes_pendientes'] = cursor.fetchone()['total']
        
        # Préstamos activos
        cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'desembolsado'")
        stats['prestamos_activos'] = cursor.fetchone()['total']
        
        # Cartera total
        cursor.execute("SELECT COALESCE(SUM(monto_aprobado), 0) as total FROM prestamos WHERE estado = 'desembolsado'")
        stats['cartera_total'] = cursor.fetchone()['total']
        
        # Total asesores activos
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'asesor' AND activo = TRUE")
        stats['total_asesores'] = cursor.fetchone()['total']
        
        # Solicitudes recientes
        cursor.execute("""
            SELECT p.*, c.nombres as cliente_nombres, c.apellidos as cliente_apellidos
            FROM prestamos p
            JOIN clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha_solicitud DESC
            LIMIT 5
        """)
        solicitudes_recientes = cursor.fetchall()
        
        # Asesores con estadísticas
        cursor.execute("""
            SELECT u.id, u.nombre, u.email,
                   COUNT(DISTINCT aa.cliente_id) as total_clientes,
                   COUNT(DISTINCT CASE WHEN p.estado = 'solicitado' THEN p.id END) as solicitudes_pendientes
            FROM usuarios u
            LEFT JOIN asignaciones_asesores aa ON aa.asesor_id = u.id
            LEFT JOIN prestamos p ON p.cliente_id = aa.cliente_id
            WHERE u.rol = 'asesor' AND u.activo = TRUE
            GROUP BY u.id, u.nombre, u.email
            ORDER BY total_clientes DESC
            LIMIT 5
        """)
        asesores = cursor.fetchall()
        
        cursor.execute("""
            SELECT * FROM notificaciones
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
            LIMIT 50
        """, (session.get('user_id'),))
        notificaciones = cursor.fetchall()
        notificaciones_pendientes = sum(1 for n in notificaciones if not n['leida'])

        cursor.close()

        return render_template('admin/dashboard.html',
                             stats=stats,
                             solicitudes_recientes=solicitudes_recientes,
                             asesores=asesores,
                             notificaciones=notificaciones,
                             notificaciones_pendientes=notificaciones_pendientes,
                             now=datetime.now())

    except Exception as e:
        flash(f'Error al cargar dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/admin/clientes')
@admin_required
def admin_clientes():
    """Página de gestión de clientes"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener filtros
        buscar = request.args.get('buscar', '')
        estado = request.args.get('estado', '')
        asesor_filter = request.args.get('asesor', '')
        
        # Query base
        query = """
            SELECT c.*,
                   u.email as usuario_email,
                   a.nombre as asesor_nombre,
                   COUNT(DISTINCT p.id) as total_prestamos,
                   SUM(CASE WHEN p.estado = 'solicitado' THEN 1 ELSE 0 END) as solicitudes_pendientes
            FROM clientes c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            LEFT JOIN asignaciones_asesores aa ON aa.cliente_id = c.id AND aa.activa = TRUE
            LEFT JOIN usuarios a ON a.id = aa.asesor_id
            LEFT JOIN prestamos p ON p.cliente_id = c.id
            WHERE 1=1
        """

        params = []

        # Aplicar filtros
        if buscar:
            query += """ AND (c.nombres LIKE %s OR c.apellidos LIKE %s
                           OR c.numero_documento LIKE %s OR c.email LIKE %s)"""
            like_buscar = f'%{buscar}%'
            params.extend([like_buscar, like_buscar, like_buscar, like_buscar])

        if estado:
            query += " AND c.estado = %s"
            params.append(estado)

        if asesor_filter == 'sin_asignar':
            query += " AND aa.asesor_id IS NULL"
        elif asesor_filter:
            query += " AND aa.asesor_id = %s"
            params.append(asesor_filter)
        
        query += " GROUP BY c.id, u.email, a.nombre ORDER BY c.fecha_registro DESC"
        
        cursor.execute(query, params)
        clientes = cursor.fetchall()
        
        # Obtener total de clientes
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        total_clientes = cursor.fetchone()['total']
        
        # Obtener lista de asesores para filtros
        cursor.execute("""
            SELECT u.id, u.nombre, u.email,
                   COUNT(aa.cliente_id) as total_clientes
            FROM usuarios u
            LEFT JOIN asignaciones_asesores aa ON aa.asesor_id = u.id AND aa.activa = TRUE
            WHERE u.rol = 'asesor' AND u.activo = TRUE
            GROUP BY u.id, u.nombre, u.email
            ORDER BY u.nombre
        """)
        asesores = cursor.fetchall()
        
        cursor.close()
        
        return render_template('admin/clientes.html',
                             clientes=clientes,
                             total_clientes=total_clientes,
                             asesores=asesores)
        
    except Exception as e:
        flash(f'Error al cargar clientes: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))
    

@app.route('/admin/asignar-asesor', methods=['POST'])
@admin_required
def asignar_asesor():
    """Asigna un asesor a un cliente"""
    try:
        cliente_id = request.form.get('cliente_id')
        asesor_id = request.form.get('asesor_id')
        
        if not cliente_id or not asesor_id:
            flash('Datos incompletos', 'error')
            return redirect(url_for('admin_clientes'))
        
        cursor = mysql.connection.cursor()
        
        # Desactivar asignaciones previas
        cursor.execute("""
            UPDATE asignaciones_asesores SET activa = FALSE WHERE cliente_id = %s
        """, (cliente_id,))

        # Registrar nueva asignación
        cursor.execute("""
            INSERT INTO asignaciones_asesores
            (cliente_id, asesor_id, activa, notas)
            VALUES (%s, %s, TRUE, 'Asignación desde panel admin')
        """, (cliente_id, asesor_id))
        
        # Obtener nombres para notificación
        cursor.execute("SELECT nombres, apellidos FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (asesor_id,))
        asesor = cursor.fetchone()
        
        # Crear notificación para el asesor
        cursor.execute("""
            INSERT INTO notificaciones
            (usuario_id, titulo, mensaje, tipo)
            VALUES (%s, %s, %s, 'info')
        """, (
            asesor_id,
            'Nuevo cliente asignado',
            f'Se te ha asignado el cliente {cliente["nombres"]} {cliente["apellidos"]}'
        ))
        
        mysql.connection.commit()
        cursor.close()

        admin_logger.log_asignar_asesor(
            int(cliente_id), int(asesor_id),
            session.get('user_id'), request.remote_addr
        )

        flash(f'Asesor {asesor["nombre"]} asignado correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al asignar asesor: {str(e)}', 'error')

    return redirect(url_for('admin_clientes'))


@app.route('/admin/enviar-notificacion', methods=['POST'])
@admin_required
def enviar_notificacion():
    """Envía una notificación a un cliente"""
    try:
        cliente_id = request.form.get('cliente_id')
        titulo = request.form.get('titulo')
        mensaje = request.form.get('mensaje')
        
        if not all([cliente_id, titulo, mensaje]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('admin_clientes'))
        
        cursor = mysql.connection.cursor()
        
        # Obtener usuario_id del cliente
        cursor.execute("SELECT usuario_id FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        if not cliente or not cliente['usuario_id']:
            flash('Cliente no tiene usuario asociado', 'error')
            return redirect(url_for('admin_clientes'))
        
        # Crear notificación
        cursor.execute("""
            INSERT INTO notificaciones
            (usuario_id, titulo, mensaje, tipo, leida)
            VALUES (%s, %s, %s, 'info', FALSE)
        """, (cliente['usuario_id'], titulo, mensaje))
        
        mysql.connection.commit()
        cursor.close()
        
        flash('Notificación enviada correctamente', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al enviar notificación: {str(e)}', 'error')
    
    return redirect(url_for('admin_clientes'))

@app.route('/admin/solicitudes')
@admin_required
def admin_solicitudes():
    """Página de gestión de solicitudes y préstamos"""
    try:
        cursor = mysql.connection.cursor()
        estado_filter = request.args.get('estado', '')

        # Stats de cartera
        stats = {}
        try:
            cursor.execute("SELECT COUNT(*) as t FROM prestamos WHERE estado='solicitado'")
            stats['pendientes'] = cursor.fetchone()['t']
            cursor.execute("SELECT COUNT(*) as t FROM prestamos WHERE estado='desembolsado'")
            stats['desembolsados'] = cursor.fetchone()['t']
            cursor.execute("SELECT COALESCE(SUM(monto_aprobado),0) as t FROM prestamos WHERE estado='desembolsado'")
            stats['cartera'] = float(cursor.fetchone()['t'])
            cursor.execute("SELECT COUNT(*) as t FROM prestamos")
            stats['total'] = cursor.fetchone()['t']
        except Exception:
            stats = {'pendientes':0,'desembolsados':0,'cartera':0.0,'total':0}

        query = """
            SELECT p.*,
                   c.nombres as cliente_nombres,
                   c.apellidos as cliente_apellidos,
                   c.numero_documento as cliente_documento,
                   c.email as cliente_email,
                   c.celular as cliente_celular,
                   a.nombre as asesor_nombre
            FROM prestamos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN asignaciones_asesores aa ON aa.cliente_id = c.id AND aa.activa = TRUE
            LEFT JOIN usuarios a ON a.id = aa.asesor_id
            WHERE 1=1
        """
        params = []
        if estado_filter:
            query += " AND p.estado = %s"
            params.append(estado_filter)
        query += " ORDER BY p.fecha_solicitud DESC LIMIT 200"
        cursor.execute(query, params)
        solicitudes = cursor.fetchall()
        cursor.close()

        return render_template('admin/solicitudes.html',
                               solicitudes=solicitudes,
                               stats=stats,
                               estado_filter=estado_filter)

    except Exception as e:
        flash(f'Error al cargar solicitudes: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))
    


@app.route('/admin/cambiar-estado-prestamo', methods=['POST'])
@admin_required
def admin_cambiar_estado_prestamo():
    """Cambiar el estado de un préstamo"""
    try:
        prestamo_id = request.form.get('prestamo_id')
        nuevo_estado = request.form.get('nuevo_estado')
        observaciones = request.form.get('observaciones', '')

        estados_validos = ['solicitado', 'en_analisis', 'aprobado', 'rechazado', 'desembolsado', 'finalizado']
        if not prestamo_id or nuevo_estado not in estados_validos:
            flash('Datos inválidos para cambiar el estado.', 'error')
            return redirect(url_for('admin_solicitudes'))

        cursor = mysql.connection.cursor()

        # Obtener estado anterior y número para el log
        cursor.execute("SELECT estado, numero_prestamo FROM prestamos WHERE id = %s", (prestamo_id,))
        prestamo_actual = cursor.fetchone()
        estado_anterior = prestamo_actual['estado'] if prestamo_actual else 'desconocido'
        numero_prestamo = prestamo_actual['numero_prestamo'] if prestamo_actual else ''

        campos_extra = ""
        params = [nuevo_estado]

        if nuevo_estado == 'aprobado':
            campos_extra = ", fecha_aprobacion = NOW(), usuario_aprobador_id = %s"
            params.append(session.get('user_id'))
        elif nuevo_estado == 'desembolsado':
            campos_extra = ", fecha_desembolso = NOW()"

        if observaciones:
            campos_extra += ", observaciones = %s"
            params.append(observaciones)

        params.append(prestamo_id)
        cursor.execute(
            f"UPDATE prestamos SET estado = %s{campos_extra} WHERE id = %s",
            params
        )
        mysql.connection.commit()
        cursor.close()

        loan_logger.log_cambio_estado(
            int(prestamo_id), numero_prestamo,
            estado_anterior, nuevo_estado,
            session.get('user_id'), request.remote_addr
        )

        flash('Estado del préstamo actualizado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al cambiar el estado: {str(e)}', 'error')

    return redirect(url_for('admin_solicitudes'))


# ================================================
# DASHBOARD DEL CLIENTE
# ================================================

@app.route('/cliente/dashboard')
@login_required
def cliente_dashboard():
    """Dashboard principal del cliente"""
    try:
        # Verificar que el usuario sea cliente
        if session.get('user_rol') not in ['cliente']:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect_by_role()
        
        cursor = mysql.connection.cursor()
        
        # Obtener información del cliente
        cursor.execute("""
            SELECT c.*, u.email as usuario_email
            FROM clientes c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.usuario_id = %s
        """, (session.get('user_id'),))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('No se encontró información del cliente', 'error')
            return redirect(url_for('index'))
        
        # Obtener solicitudes del cliente
        cursor.execute("""
            SELECT * FROM prestamos
            WHERE cliente_id = %s
            ORDER BY fecha_solicitud DESC
        """, (cliente['id'],))
        prestamos = cursor.fetchall()
        
        # Obtener notificaciones no leídas
        cursor.execute("""
            SELECT * FROM notificaciones
            WHERE usuario_id = %s AND leida = FALSE
            ORDER BY fecha_creacion DESC
            LIMIT 5
        """, (session.get('user_id'),))
        notificaciones = cursor.fetchall()
        
        # Contar notificaciones pendientes
        cursor.execute("""
            SELECT COUNT(*) as total FROM notificaciones
            WHERE usuario_id = %s AND leida = FALSE
        """, (session.get('user_id'),))
        notificaciones_pendientes = cursor.fetchone()['total']
        
        # Estadísticas
        stats = {
            'total_solicitudes': len(prestamos),
            'solicitudes_pendientes': sum(1 for p in prestamos if p['estado'] == 'solicitado'),
            'prestamos_aprobados': sum(1 for p in prestamos if p['estado'] in ['aprobado', 'desembolsado']),
            'prestamos_activos': sum(1 for p in prestamos if p['estado'] == 'desembolsado'),
        }
        
        cursor.close()
        
        return render_template('cliente/dashboard.html',
                             cliente=cliente,
                             prestamos=prestamos,
                             notificaciones=notificaciones,
                             notificaciones_pendientes=notificaciones_pendientes,
                             stats=stats,
                             now=datetime.now())
        
    except Exception as e:
        flash(f'Error al cargar dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/cliente/configuracion')
@login_required
def cliente_configuracion():
    """Página de configuración del cliente con perfil, documentos y preferencias"""
    try:
        cursor = mysql.connection.cursor()

        # Crear tabla documentos_cliente si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_cliente (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT NOT NULL,
                tipo ENUM('cedula','comprobante_ingresos','desprendible_pago','carta_laboral','otro') NOT NULL DEFAULT 'otro',
                nombre_original VARCHAR(255) NOT NULL,
                nombre_archivo VARCHAR(255) NOT NULL,
                fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
            )
        """)

        # Obtener datos del cliente
        cursor.execute("""
            SELECT c.*, u.nombre as usuario_nombre
            FROM clientes c
            JOIN usuarios u ON u.id = c.usuario_id
            WHERE c.usuario_id = %s
        """, (session.get('user_id'),))
        cliente = cursor.fetchone()

        documentos = []
        if cliente:
            cursor.execute("""
                SELECT * FROM documentos_cliente
                WHERE cliente_id = %s
                ORDER BY fecha_subida DESC
            """, (cliente['id'],))
            documentos = cursor.fetchall()

        cursor.close()
        return render_template('cliente/configuracion.html', cliente=cliente, documentos=documentos)

    except Exception as e:
        return render_template('cliente/configuracion.html', cliente=None, documentos=[])


@app.route('/cliente/actualizar-perfil', methods=['POST'])
@login_required
def cliente_actualizar_perfil():
    """Actualiza los datos personales del cliente"""
    if session.get('user_rol') != 'cliente':
        flash('No autorizado', 'error')
        return redirect(url_for('cliente_configuracion'))

    try:
        nombre = request.form.get('nombre', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        celular = request.form.get('celular', '').strip()
        telefono = request.form.get('telefono', '').strip() or None
        direccion = request.form.get('direccion', '').strip() or None
        ciudad = request.form.get('ciudad', '').strip() or None
        departamento = request.form.get('departamento', '').strip() or None

        if not nombre:
            flash('El nombre no puede estar vacío', 'error')
            return redirect(url_for('cliente_configuracion'))

        cursor = mysql.connection.cursor()

        cursor.execute("UPDATE usuarios SET nombre = %s WHERE id = %s", (nombre, session.get('user_id')))
        cursor.execute("""
            UPDATE clientes
            SET apellidos = %s, celular = %s, telefono = %s, direccion = %s, ciudad = %s, departamento = %s
            WHERE usuario_id = %s
        """, (apellidos, celular, telefono, direccion, ciudad, departamento, session.get('user_id')))

        mysql.connection.commit()
        cursor.close()

        session['user_nombre'] = nombre
        flash('Perfil actualizado correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al actualizar perfil: {str(e)}', 'error')

    return redirect(url_for('cliente_configuracion'))


@app.route('/cliente/cambiar-password', methods=['POST'])
@login_required
def cliente_cambiar_password():
    """Cambia la contraseña del cliente"""
    try:
        password_actual = request.form.get('password_actual', '')
        password_nueva = request.form.get('password_nueva', '')
        confirmar = request.form.get('confirmar', '')

        if not password_actual or not password_nueva or not confirmar:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('cliente_configuracion'))

        if len(password_nueva) < 8:
            flash('La nueva contraseña debe tener al menos 8 caracteres', 'error')
            return redirect(url_for('cliente_configuracion'))

        if password_nueva != confirmar:
            flash('La nueva contraseña y la confirmación no coinciden', 'error')
            return redirect(url_for('cliente_configuracion'))

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE id = %s", (session.get('user_id'),))
        usuario = cursor.fetchone()

        if not usuario:
            cursor.close()
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('cliente_configuracion'))

        if not check_password(password_actual, usuario['password_hash']):
            cursor.close()
            flash('La contraseña actual es incorrecta', 'error')
            return redirect(url_for('cliente_configuracion'))

        cursor.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s",
                       (hash_password(password_nueva), session.get('user_id')))
        mysql.connection.commit()
        cursor.close()

        flash('Contraseña actualizada correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al cambiar contraseña: {str(e)}', 'error')

    return redirect(url_for('cliente_configuracion'))


@app.route('/cliente/subir-documento', methods=['POST'])
@login_required
def cliente_subir_documento():
    """Sube un documento del cliente"""
    try:
        cursor = mysql.connection.cursor()

        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_cliente (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT NOT NULL,
                tipo ENUM('cedula','comprobante_ingresos','desprendible_pago','carta_laboral','otro') NOT NULL DEFAULT 'otro',
                nombre_original VARCHAR(255) NOT NULL,
                nombre_archivo VARCHAR(255) NOT NULL,
                fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("SELECT id FROM clientes WHERE usuario_id = %s", (session.get('user_id'),))
        cliente_row = cursor.fetchone()

        if not cliente_row:
            cursor.close()
            flash('No se encontró información del cliente', 'error')
            return redirect(url_for('cliente_configuracion'))

        cliente_id = cliente_row['id']

        if 'archivo' not in request.files:
            cursor.close()
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('cliente_configuracion'))

        archivo = request.files['archivo']
        tipo_doc = request.form.get('tipo', 'otro')

        if archivo.filename == '':
            cursor.close()
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('cliente_configuracion'))

        if not allowed_doc(archivo.filename):
            cursor.close()
            flash('Tipo de archivo no permitido. Use PDF, JPG, JPEG o PNG', 'error')
            return redirect(url_for('cliente_configuracion'))

        nombre_original = archivo.filename
        nombre_seguro   = secure_filename(archivo.filename)
        # Prefijo aleatorio para evitar colisiones de nombres entre clientes
        nombre_archivo  = f"{cliente_id}_{secrets.token_hex(8)}_{nombre_seguro}"

        ruta_archivo = os.path.join(DOCS_UPLOAD_FOLDER, nombre_archivo)
        archivo.save(ruta_archivo)

        cursor.execute("""
            INSERT INTO documentos_cliente (cliente_id, tipo, nombre_original, nombre_archivo)
            VALUES (%s, %s, %s, %s)
        """, (cliente_id, tipo_doc, nombre_original, nombre_archivo))
        mysql.connection.commit()
        cursor.close()

        flash('Documento subido correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al subir documento: {str(e)}', 'error')

    return redirect(url_for('cliente_configuracion'))


@app.route('/doc/<int:doc_id>')
@login_required
def ver_documento(doc_id):
    """Sirve un documento al usuario autorizado"""
    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT dc.*, c.usuario_id
            FROM documentos_cliente dc
            JOIN clientes c ON c.id = dc.cliente_id
            WHERE dc.id = %s
        """, (doc_id,))
        doc = cursor.fetchone()
        cursor.close()

        if not doc:
            flash('Documento no encontrado', 'error')
            return redirect(url_for('cliente_configuracion'))

        # Verificar permisos: dueño del doc o admin/asesor
        user_id = session.get('user_id')
        user_rol = session.get('user_rol')
        if doc['usuario_id'] != user_id and user_rol not in ['admin', 'asesor']:
            flash('No tienes permisos para ver este documento', 'error')
            return redirect(url_for('cliente_configuracion'))

        ruta_archivo = os.path.join(DOCS_UPLOAD_FOLDER, doc['nombre_archivo'])
        if not os.path.exists(ruta_archivo):
            flash('El archivo no se encontró en el servidor', 'error')
            return redirect(url_for('cliente_configuracion'))

        return send_file(ruta_archivo, download_name=doc['nombre_original'], as_attachment=False)

    except Exception as e:
        flash(f'Error al cargar documento: {str(e)}', 'error')
        return redirect(url_for('cliente_configuracion'))


@app.route('/cliente/mis-documentos')
@login_required
def cliente_mis_documentos():
    """Retorna lista de documentos del cliente (AJAX)"""
    try:
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT id FROM clientes WHERE usuario_id = %s", (session.get('user_id'),))
        cliente_row = cursor.fetchone()

        if not cliente_row:
            cursor.close()
            return jsonify([])

        cursor.execute("""
            SELECT id, tipo, nombre_original, fecha_subida
            FROM documentos_cliente
            WHERE cliente_id = %s
            ORDER BY fecha_subida DESC
        """, (cliente_row['id'],))
        documentos = cursor.fetchall()
        cursor.close()

        resultado = []
        for d in documentos:
            resultado.append({
                'id': d['id'],
                'tipo': d['tipo'],
                'nombre_original': d['nombre_original'],
                'fecha_subida': d['fecha_subida'].strftime('%d/%m/%Y %H:%M') if d['fecha_subida'] else ''
            })

        return jsonify(resultado)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# DASHBOARD DEL ASESOR
# ================================

@app.route('/asesor/dashboard')
@login_required
def asesor_dashboard():
    """Dashboard principal del asesor"""
    try:
        if session.get('user_rol') != 'asesor':
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect_by_role()

        cursor = mysql.connection.cursor()
        asesor_id = session.get('user_id')

        # Clientes asignados con sus préstamos
        cursor.execute("""
            SELECT c.*,
                   COUNT(DISTINCT p.id) as total_prestamos,
                   SUM(CASE WHEN p.estado = 'solicitado' THEN 1 ELSE 0 END) as pendientes
            FROM clientes c
            JOIN asignaciones_asesores aa ON aa.cliente_id = c.id AND aa.asesor_id = %s AND aa.activa = TRUE
            LEFT JOIN prestamos p ON p.cliente_id = c.id
            GROUP BY c.id
            ORDER BY c.fecha_registro DESC
        """, (asesor_id,))
        clientes = cursor.fetchall()

        # Todas las solicitudes de sus clientes
        cursor.execute("""
            SELECT p.*, c.nombres as cliente_nombres, c.apellidos as cliente_apellidos
            FROM prestamos p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN asignaciones_asesores aa ON aa.cliente_id = c.id AND aa.asesor_id = %s AND aa.activa = TRUE
            ORDER BY p.fecha_solicitud DESC
            LIMIT 100
        """, (asesor_id,))
        todas_solicitudes = cursor.fetchall()

        solicitudes_pendientes = [s for s in todas_solicitudes if s['estado'] == 'solicitado']

        # Notificaciones
        cursor.execute("""
            SELECT * FROM notificaciones
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
            LIMIT 30
        """, (asesor_id,))
        notificaciones = cursor.fetchall()
        notificaciones_pendientes = sum(1 for n in notificaciones if not n['leida'])

        stats = {
            'total_clientes':         len(clientes),
            'solicitudes_pendientes': len(solicitudes_pendientes),
            'clientes_activos':       sum(1 for c in clientes if c['estado'] == 'activo'),
            'prestamos_desembolsados':sum(1 for s in todas_solicitudes if s['estado'] == 'desembolsado'),
        }

        cursor.close()

        return render_template('asesor/dashboard.html',
                               clientes=clientes,
                               todas_solicitudes=todas_solicitudes,
                               solicitudes_pendientes=solicitudes_pendientes,
                               notificaciones=notificaciones,
                               notificaciones_pendientes=notificaciones_pendientes,
                               stats=stats,
                               now=datetime.now())

    except Exception as e:
        flash(f'Error al cargar dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/asesor/marcar-notificaciones', methods=['POST'])
@login_required
def asesor_marcar_notificaciones():
    """Marca todas las notificaciones del asesor como leídas"""
    if session.get('user_rol') != 'asesor':
        return jsonify({'error': 'No autorizado'}), 403
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE notificaciones SET leida = TRUE
            WHERE usuario_id = %s AND leida = FALSE
        """, (session.get('user_id'),))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/asesor/actualizar-perfil', methods=['POST'])
@login_required
def asesor_actualizar_perfil():
    """Actualiza nombre y/o contraseña del asesor"""
    if session.get('user_rol') != 'asesor':
        flash('No autorizado', 'error')
        return redirect(url_for('asesor_dashboard'))
    try:
        nombre   = request.form.get('nombre', '').strip()
        password = request.form.get('password', '').strip()
        if not nombre:
            flash('El nombre no puede estar vacío', 'error')
            return redirect(url_for('asesor_dashboard'))
        cursor = mysql.connection.cursor()
        if password:
            cursor.execute("UPDATE usuarios SET nombre=%s, password_hash=%s WHERE id=%s",
                           (nombre, hash_password(password), session.get('user_id')))
        else:
            cursor.execute("UPDATE usuarios SET nombre=%s WHERE id=%s",
                           (nombre, session.get('user_id')))
        cursor.execute("UPDATE clientes SET nombres=%s WHERE usuario_id=%s",
                       (nombre, session.get('user_id')))
        mysql.connection.commit()
        cursor.close()
        session['user_nombre'] = nombre
        flash('Perfil actualizado correctamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al actualizar perfil: {str(e)}', 'error')
    return redirect(url_for('asesor_dashboard'))


@app.route('/asesor/contactar-admin', methods=['POST'])
@login_required
def asesor_contactar_admin():
    """Envia un mensaje a todos los administradores activos como notificacion"""
    if session.get('user_rol') != 'asesor':
        flash('No autorizado', 'error')
        return redirect(url_for('asesor_dashboard'))
    titulo  = request.form.get('titulo', '').strip()
    mensaje = request.form.get('mensaje', '').strip()
    if not titulo or not mensaje:
        flash('Titulo y mensaje son obligatorios', 'error')
        return redirect(url_for('asesor_dashboard'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE rol='admin' AND activo=TRUE")
        admins = cursor.fetchall()
        if not admins:
            flash('No se encontro ningun administrador activo', 'error')
            cursor.close()
            return redirect(url_for('asesor_dashboard'))
        asesor_nombre = session.get('user_nombre', 'Asesor')
        for admin in admins:
            cursor.execute("""
                INSERT INTO notificaciones (usuario_id, titulo, mensaje, tipo)
                VALUES (%s, %s, %s, 'info')
            """, (admin['id'],
                  f"Mensaje de asesor: {titulo}",
                  f"[{asesor_nombre}]: {mensaje}"))
        mysql.connection.commit()
        cursor.close()
        flash('Mensaje enviado a administracion correctamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al enviar mensaje: {str(e)}', 'error')
    return redirect(url_for('asesor_dashboard'))


@app.route('/asesor/notificar-cliente', methods=['POST'])
@login_required
def asesor_notificar_cliente():
    """Envia una notificacion a un cliente asignado al asesor"""
    if session.get('user_rol') != 'asesor':
        flash('No autorizado', 'error')
        return redirect(url_for('asesor_dashboard'))
    cliente_id = request.form.get('cliente_id', '').strip()
    titulo     = request.form.get('titulo', '').strip()
    mensaje    = request.form.get('mensaje', '').strip()
    if not all([cliente_id, titulo, mensaje]):
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('asesor_dashboard'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.usuario_id, c.nombres, c.apellidos
            FROM clientes c
            JOIN asignaciones_asesores aa ON aa.cliente_id = c.id
                AND aa.asesor_id = %s AND aa.activa = TRUE
            WHERE c.id = %s
        """, (session.get('user_id'), cliente_id))
        cliente = cursor.fetchone()
        if not cliente or not cliente['usuario_id']:
            flash('Cliente no encontrado o no asignado a ti', 'error')
            cursor.close()
            return redirect(url_for('asesor_dashboard'))
        cursor.execute("""
            INSERT INTO notificaciones (usuario_id, titulo, mensaje, tipo)
            VALUES (%s, %s, %s, 'info')
        """, (cliente['usuario_id'], titulo, mensaje))
        mysql.connection.commit()
        cursor.close()
        flash(f'Notificacion enviada a {cliente["nombres"]} {cliente["apellidos"]} correctamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al enviar notificacion: {str(e)}', 'error')
    return redirect(url_for('asesor_dashboard'))


# ================================
# GESTIÓN DE ASESORES
# ================================

@app.route('/admin/asesores')
@admin_required
def admin_asesores():
    """Página de gestión de asesores"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT u.id, u.nombre, u.email, u.activo, u.fecha_creacion,
                   COUNT(DISTINCT aa.cliente_id) as total_clientes,
                   COUNT(DISTINCT p.id) as total_prestamos,
                   SUM(CASE WHEN p.estado = 'solicitado' THEN 1 ELSE 0 END) as solicitudes_pendientes
            FROM usuarios u
            LEFT JOIN asignaciones_asesores aa ON aa.asesor_id = u.id AND aa.activa = TRUE
            LEFT JOIN prestamos p ON p.cliente_id = aa.cliente_id
            WHERE u.rol = 'asesor'
            GROUP BY u.id, u.nombre, u.email, u.activo, u.fecha_creacion
            ORDER BY u.nombre
        """)
        asesores = cursor.fetchall()
        
        cursor.close()
        
        return render_template('admin/asesores.html',
                             asesores=asesores)
        
    except Exception as e:
        flash(f'Error al cargar asesores: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

# ================================
# CREAR NUEVO ASESOR
# ================================

@app.route('/admin/crear-asesor', methods=['POST'])
@admin_required
def crear_asesor():
    """Crea un nuevo asesor"""
    try:
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password', '').strip() or 'Asesor123!'
        
        usuario_id, error = crear_usuario(
            nombres=nombre,
            email=email,
            password=password,
            tipo_documento='CC',
            numero_documento='0000000000',  # Temporal
            apellidos='',
            celular='0000000000',  # Temporal
            fecha_nacimiento='1990-01-01',  # Requerido por BD
            rol='asesor',
            tipo_cliente='empleado_publico'
        )
        
        if error:
            flash(error, 'error')
        else:
            admin_logger.log_crear_asesor(
                usuario_id, nombre, email,
                session.get('user_id'), request.remote_addr
            )
            flash(f'Asesor {nombre} creado correctamente', 'success')

    except Exception as e:
        flash(f'Error al crear asesor: {str(e)}', 'error')

    return redirect(url_for('admin_asesores'))

# ================================
# EDITAR ASESOR
# ================================

@app.route('/admin/editar-asesor', methods=['POST'])
@admin_required
def editar_asesor():
    """Edita nombre, email y contraseña de un asesor"""
    try:
        asesor_id  = request.form.get('asesor_id')
        nombre     = request.form.get('nombre', '').strip()
        email      = request.form.get('email', '').strip()
        password   = request.form.get('password', '').strip()

        if not asesor_id or not nombre or not email:
            flash('Nombre y correo son obligatorios', 'error')
            return redirect(url_for('admin_asesores'))

        cursor = mysql.connection.cursor()

        # Verificar que el email no lo use otro usuario
        cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, asesor_id))
        if cursor.fetchone():
            flash('El correo ya está en uso por otro usuario', 'error')
            cursor.close()
            return redirect(url_for('admin_asesores'))

        if password:
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, email = %s, password_hash = %s WHERE id = %s",
                (nombre, email, hash_password(password), asesor_id)
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s",
                (nombre, email, asesor_id)
            )

        # Sincronizar email en la tabla clientes
        cursor.execute(
            "UPDATE clientes SET email = %s, nombres = %s WHERE usuario_id = %s",
            (email, nombre, asesor_id)
        )

        mysql.connection.commit()
        cursor.close()

        flash(f'Asesor {nombre} actualizado correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al editar asesor: {str(e)}', 'error')

    return redirect(url_for('admin_asesores'))


# ================================
# ELIMINAR/DESACTIVAR ASESOR
# ================================

@app.route('/admin/toggle-asesor/<int:asesor_id>', methods=['POST'])
@admin_required
def toggle_asesor(asesor_id):
    """Activa o desactiva un asesor"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("SELECT activo FROM usuarios WHERE id = %s", (asesor_id,))
        asesor = cursor.fetchone()
        
        nuevo_estado = not asesor['activo']
        
        cursor.execute("""
            UPDATE usuarios 
            SET activo = %s 
            WHERE id = %s
        """, (nuevo_estado, asesor_id))
        
        mysql.connection.commit()
        cursor.close()

        admin_logger.log_toggle_asesor(
            asesor_id, nuevo_estado,
            session.get('user_id'), request.remote_addr
        )

        estado_texto = 'activado' if nuevo_estado else 'desactivado'
        flash(f'Asesor {estado_texto} correctamente', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('admin_asesores'))

@app.route('/admin/marcar-notificaciones', methods=['POST'])
@admin_required
def admin_marcar_notificaciones():
    """Marca todas las notificaciones del admin como leidas"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE notificaciones SET leida = TRUE
            WHERE usuario_id = %s AND leida = FALSE
        """, (session.get('user_id'),))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    """Página de reportes con estadísticas y exportaciones"""
    try:
        cursor = mysql.connection.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        stats['total_clientes'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM prestamos")
        stats['total_prestamos'] = cursor.fetchone()['total']

        cursor.execute("SELECT COALESCE(SUM(monto_aprobado), 0) as total FROM prestamos WHERE estado = 'desembolsado'")
        stats['cartera_activa'] = float(cursor.fetchone()['total'])

        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'asesor' AND activo = 1")
        stats['total_asesores'] = cursor.fetchone()['total']

        # Distribución de estados
        cursor.execute("""
            SELECT estado, COUNT(*) as conteo
            FROM prestamos
            GROUP BY estado
        """)
        filas_estados = cursor.fetchall()
        cursor.close()

        estados_posibles = ['solicitado', 'en_analisis', 'aprobado', 'rechazado', 'desembolsado', 'finalizado']
        dist_dict = {f['estado']: f['conteo'] for f in filas_estados}
        total_prest = stats['total_prestamos'] or 1

        distribucion_estados = []
        for estado in estados_posibles:
            conteo = dist_dict.get(estado, 0)
            distribucion_estados.append({
                'estado': estado,
                'conteo': conteo,
                'porcentaje': round(conteo / total_prest * 100, 1)
            })

        return render_template('admin/reportes.html', stats=stats, distribucion_estados=distribucion_estados)

    except Exception as e:
        flash(f'Error al cargar reportes: {str(e)}', 'error')
        return render_template('admin/reportes.html', stats={}, distribucion_estados=[])


@app.route('/admin/exportar/clientes')
@admin_required
def exportar_clientes():
    """Exporta todos los clientes en formato CSV."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT c.nombres, c.apellidos, c.email, c.tipo_documento, c.numero_documento,
                   c.celular, c.ciudad, c.tipo_cliente, c.estado, c.fecha_registro
            FROM clientes c ORDER BY c.fecha_registro DESC
        """)
        rows = [
            [c['nombres'], c['apellidos'], c['email'],
             c['tipo_documento'], c['numero_documento'],
             c['celular'], c['ciudad'] or '', c['tipo_cliente'] or '',
             c['estado'],
             c['fecha_registro'].strftime('%d/%m/%Y') if c['fecha_registro'] else '']
            for c in cursor.fetchall()
        ]
        cursor.close()
        return make_csv_response(
            'clientes_novacapital.csv',
            ['Nombres','Apellidos','Email','Tipo Documento','Numero Documento',
             'Celular','Ciudad','Tipo Cliente','Estado','Fecha Registro'],
            rows
        )
    except Exception as e:
        flash(f'Error al exportar clientes: {str(e)}', 'error')
        return redirect(url_for('admin_reportes'))


@app.route('/admin/exportar/prestamos')
@admin_required
def exportar_prestamos():
    """Exporta todos los préstamos en formato CSV."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT p.numero_prestamo, c.nombres as cliente_nombres, c.apellidos as cliente_apellidos,
                   p.monto_solicitado, p.monto_aprobado, p.tasa_interes, p.plazo_meses,
                   p.estado, p.fecha_solicitud
            FROM prestamos p JOIN clientes c ON c.id = p.cliente_id
            ORDER BY p.fecha_solicitud DESC
        """)
        rows = [
            [p['numero_prestamo'], p['cliente_nombres'], p['cliente_apellidos'],
             p['monto_solicitado'], p['monto_aprobado'] or '',
             p['tasa_interes'] or '', p['plazo_meses'], p['estado'],
             p['fecha_solicitud'].strftime('%d/%m/%Y') if p['fecha_solicitud'] else '']
            for p in cursor.fetchall()
        ]
        cursor.close()
        return make_csv_response(
            'prestamos_novacapital.csv',
            ['Numero Prestamo','Nombres Cliente','Apellidos Cliente',
             'Monto Solicitado','Monto Aprobado','Tasa Interes',
             'Plazo Meses','Estado','Fecha Solicitud'],
            rows
        )
    except Exception as e:
        flash(f'Error al exportar préstamos: {str(e)}', 'error')
        return redirect(url_for('admin_reportes'))


@app.route('/admin/exportar/cartera')
@admin_required
def exportar_cartera():
    """Exporta la cartera activa (préstamos desembolsados) en formato CSV."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT p.numero_prestamo, c.nombres as cliente_nombres, c.apellidos as cliente_apellidos,
                   p.monto_aprobado, p.tasa_interes, p.plazo_meses, p.cuota_mensual,
                   p.fecha_desembolso
            FROM prestamos p JOIN clientes c ON c.id = p.cliente_id
            WHERE p.estado = 'desembolsado'
            ORDER BY p.fecha_desembolso DESC
        """)
        rows = [
            [p['numero_prestamo'], p['cliente_nombres'], p['cliente_apellidos'],
             p['monto_aprobado'] or '', p['tasa_interes'] or '',
             p['plazo_meses'], p['cuota_mensual'] or '',
             p['fecha_desembolso'].strftime('%d/%m/%Y') if p['fecha_desembolso'] else '']
            for p in cursor.fetchall()
        ]
        cursor.close()
        return make_csv_response(
            'cartera_activa_novacapital.csv',
            ['Numero Prestamo','Nombres Cliente','Apellidos Cliente',
             'Monto Aprobado','Tasa Interes','Plazo Meses',
             'Cuota Mensual','Fecha Desembolso'],
            rows
        )
    except Exception as e:
        flash(f'Error al exportar cartera: {str(e)}', 'error')
        return redirect(url_for('admin_reportes'))

@app.route('/admin/prestamos')
@admin_required
def admin_prestamos():
    """Redirige a solicitudes (fusionado)"""
    return redirect(url_for('admin_solicitudes'))


@app.route('/admin/configuracion')
@admin_required
def admin_configuracion():
    """Página de configuración del panel"""
    return render_template('admin/configuracion.html')

# ================================
# VISTA DE REGISTROS JSONL
# ================================

@app.route('/admin/logs')
@admin_required
def admin_logs():
    """Visor de registros de log JSONL"""
    tipo = request.args.get('tipo', 'todos')

    if tipo == 'auth':
        entradas = auth_logger.read_last(200)
    elif tipo == 'loans':
        entradas = loan_logger.read_last(200)
    elif tipo == 'admin':
        entradas = admin_logger.read_last(200)
    else:
        todos = auth_logger.read_all() + loan_logger.read_all() + admin_logger.read_all()
        todos.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        entradas = todos[:200]

    totales = {
        'auth':  auth_logger.total(),
        'loans': loan_logger.total(),
        'admin': admin_logger.total(),
    }
    totales['todos'] = totales['auth'] + totales['loans'] + totales['admin']

    return render_template('admin/logs.html',
                           entradas=entradas,
                           tipo=tipo,
                           totales=totales,
                           now=datetime.now())


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
    print("\n" + "="*70)
    print("🏦 NOVACAPITAL SAS - Sistema de Préstamos por Libranza")
    print("="*70)
    print("✅ Servidor iniciado en: http://localhost:5000")
    print("👤 Admin: admin@novacapital.com / Admin123!")
    print("="*70 + "\n")
    
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )