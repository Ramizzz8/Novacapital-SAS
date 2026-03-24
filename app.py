from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
import bcrypt
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime

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

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        password_hash_str = password_hash.decode('utf-8')

        query_usuario = """
            INSERT INTO usuarios (nombre, email, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_usuario, (nombres, email, password_hash_str, rol, True))
        usuario_id = cursor.lastrowid

        query_cliente = """
            INSERT INTO clientes
            (usuario_id, tipo_documento, numero_documento, nombres, apellidos,
             email, celular, fecha_nacimiento, telefono, direccion, ciudad,
             departamento, tipo_cliente, entidad_empleadora, salario_mensual, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'activo')
        """
        cursor.execute(query_cliente, (
            usuario_id, tipo_documento, numero_documento, nombres, apellidos,
            email, celular, fecha_nacimiento, telefono, direccion, ciudad,
            departamento, tipo_cliente, entidad_empleadora, salario_mensual
        ))

        mysql.connection.commit()
        cursor.close()
        return usuario_id, None

    except Exception as e:
        mysql.connection.rollback()
        print(f"ERROR: {str(e)}")
        return None, f"Error al crear usuario: {str(e)}"

def verificar_credenciales(email, password):
    """Verifica las credenciales de un usuario - VERSIÓN CORREGIDA"""
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
            print(f"DEBUG: Usuario no encontrado: {email}")
            return None, "Usuario no encontrado"
        
        if not usuario['activo']:
            return None, "Usuario inactivo"
        
        # Obtener el hash de la base de datos
        password_hash_db = usuario['password_hash']
        
        # Si el hash está en formato string, convertir a bytes
        if isinstance(password_hash_db, str):
            password_hash_db = password_hash_db.encode('utf-8')
        
        # Verificar contraseña - CORREGIDO
        print(f"DEBUG: Verificando password para {email}")
        print(f"DEBUG: Hash length: {len(password_hash_db)}")
        
        if bcrypt.checkpw(password.encode('utf-8'), password_hash_db):
            print(f"DEBUG: Password correcta para {email}")
            return usuario, None
        else:
            print(f"DEBUG: Password incorrecta para {email}")
            return None, "Contraseña incorrecta"
            
    except Exception as e:
        print(f"ERROR en verificar_credenciales: {str(e)}")
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
    """Página de inicio de sesión - ACTUALIZADO"""
    if 'user_id' in session:
        # Si ya está logueado, redirigir según rol
        return redirect_by_role()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        print(f"DEBUG: Intento de login para: {email}")
        
        usuario, error = verificar_credenciales(email, password)
        
        if error:
            print(f"DEBUG: Error en login: {error}")
            return render_template('login.html', error=error)
        
        # Crear sesión
        session['user_id'] = usuario['id']
        session['user_nombre'] = usuario['nombre']
        session['user_email'] = usuario['email']
        session['user_rol'] = usuario['rol']
        
        if remember:
            session.permanent = True
        
        print(f"DEBUG: Login exitoso para {email} - Rol: {usuario['rol']}")
        
        # Redirigir según el rol del usuario
        return redirect_by_role()
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro - ACTUALIZADO"""
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
            return redirect_by_role()

        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    nombre = session.get('user_nombre', 'Usuario')
    session.clear()
    flash(f'Hasta pronto, {nombre}. Sesión cerrada correctamente.', 'success')
    return redirect(url_for('index'))


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
        
        notificaciones_pendientes = 0
        try:
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM notificaciones
                WHERE leida = FALSE AND destinatario_tipo = 'admin'
            """)
            notificaciones_pendientes = cursor.fetchone()['total']
        except Exception:
            pass

        cursor.close()

        return render_template('admin/dashboard.html',
                             stats=stats,
                             solicitudes_recientes=solicitudes_recientes,
                             asesores=asesores,
                             notificaciones_pendientes=notificaciones_pendientes,
                             now=datetime.now())

    except Exception as e:
        print(f"ERROR admin_dashboard: {str(e)}")
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
        except Exception as e:
            print(f'ERR stats: {e}')
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
    return render_template('cliente/configuracion.html')

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

        # Clientes asignados al asesor
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

        # Solicitudes pendientes de sus clientes
        cursor.execute("""
            SELECT p.*, c.nombres as cliente_nombres, c.apellidos as cliente_apellidos
            FROM prestamos p
            JOIN clientes c ON p.cliente_id = c.id
            JOIN asignaciones_asesores aa ON aa.cliente_id = c.id AND aa.asesor_id = %s AND aa.activa = TRUE
            WHERE p.estado = 'solicitado'
            ORDER BY p.fecha_solicitud DESC
            LIMIT 10
        """, (asesor_id,))
        solicitudes_pendientes = cursor.fetchall()

        # Notificaciones no leídas
        cursor.execute("""
            SELECT COUNT(*) as total FROM notificaciones
            WHERE usuario_id = %s AND leida = FALSE
        """, (asesor_id,))
        notificaciones_pendientes = cursor.fetchone()['total']

        stats = {
            'total_clientes':        len(clientes),
            'solicitudes_pendientes': len(solicitudes_pendientes),
            'clientes_activos':      sum(1 for c in clientes if c['estado'] == 'activo'),
        }

        cursor.close()

        return render_template('asesor/dashboard.html',
                               clientes=clientes,
                               solicitudes_pendientes=solicitudes_pendientes,
                               notificaciones_pendientes=notificaciones_pendientes,
                               stats=stats,
                               now=datetime.now())

    except Exception as e:
        flash(f'Error al cargar dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

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
        password = request.form.get('password', 'Asesor123!')  # Password por defecto
        
        usuario_id, error = crear_usuario(
            nombre=nombre,
            email=email,
            password=password,
            tipo_documento='CC',
            numero_documento='0000000000',  # Temporal
            apellido='',
            celular='0000000000',  # Temporal
            rol='asesor'
        )
        
        if error:
            flash(error, 'error')
        else:
            flash(f'Asesor {nombre} creado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al crear asesor: {str(e)}', 'error')
    
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
        
        estado_texto = 'activado' if nuevo_estado else 'desactivado'
        flash(f'Asesor {estado_texto} correctamente', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_asesores'))

@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    """Página de reportes"""
    return render_template('admin/reportes.html')

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