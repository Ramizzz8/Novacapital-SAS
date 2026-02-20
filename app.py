# ================================
# app/__init__.py
# ================================
from flask import Flask
from flask_mysqldb import MySQL
from .config import Config

mysql = MySQL()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    app.config.from_object(Config)
    
    # Inicializar extensiones
    mysql.init_app(app)
    
    # Registrar blueprints
    from app.routes import main_routes, auth_routes, admin_routes
    
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    
    return app


# ================================
# app/config.py
# ================================
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-novacapital-2024')
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'novacapital_db')
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # File Upload
    UPLOAD_FOLDER = 'uploads/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max


# ================================
# app/database.py
# ================================
from flask import g
from app import mysql

def get_db():
    """Obtiene la conexión a la base de datos"""
    if 'db' not in g:
        g.db = mysql.connection.cursor()
    return g.db

def close_db(e=None):
    """Cierra la conexión a la base de datos"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ================================
# app/models/usuario.py
# ================================
from app import mysql
import bcrypt
from datetime import datetime

class Usuario:
    def __init__(self, id=None, nombre=None, email=None, password_hash=None, 
                 rol='cliente', activo=True, fecha_creacion=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash
        self.rol = rol
        self.activo = activo
        self.fecha_creacion = fecha_creacion
    
    @staticmethod
    def crear_usuario(nombre, email, password, tipo_documento, numero_documento, 
                     apellido, celular, rol='cliente'):
        """Crea un nuevo usuario en la base de datos"""
        try:
            cursor = mysql.connection.cursor()
            
            # Verificar si el email ya existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                return None, "El email ya está registrado"
            
            # Verificar si el documento ya existe
            cursor.execute("SELECT id FROM clientes WHERE numero_documento = %s", 
                         (numero_documento,))
            if cursor.fetchone():
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
                (tipo_documento, numero_documento, nombres, apellidos, email, celular, estado) 
                VALUES (%s, %s, %s, %s, %s, %s, 'activo')
            """
            cursor.execute(query_cliente, 
                         (tipo_documento, numero_documento, nombre, apellido, email, celular))
            
            mysql.connection.commit()
            cursor.close()
            
            return usuario_id, None
            
        except Exception as e:
            mysql.connection.rollback()
            return None, f"Error al crear usuario: {str(e)}"
    
    @staticmethod
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
    
    @staticmethod
    def obtener_por_id(usuario_id):
        """Obtiene un usuario por su ID"""
        try:
            cursor = mysql.connection.cursor()
            query = """
                SELECT id, nombre, email, rol, activo, fecha_creacion 
                FROM usuarios 
                WHERE id = %s
            """
            cursor.execute(query, (usuario_id,))
            usuario = cursor.fetchone()
            cursor.close()
            return usuario
        except Exception as e:
            return None
    
    @staticmethod
    def obtener_por_email(email):
        """Obtiene un usuario por su email"""
        try:
            cursor = mysql.connection.cursor()
            query = """
                SELECT id, nombre, email, rol, activo 
                FROM usuarios 
                WHERE email = %s
            """
            cursor.execute(query, (email,))
            usuario = cursor.fetchone()
            cursor.close()
            return usuario
        except Exception as e:
            return None


# ================================
# app/routes/__init__.py
# ================================
# Archivo vacío para hacer el directorio un paquete


# ================================
# app/routes/main_routes.py
# ================================
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@bp.route('/nosotros')
def nosotros():
    """Página sobre nosotros"""
    return render_template('nosotros.html')

@bp.route('/contacto')
def contacto():
    """Página de contacto"""
    return render_template('contacto.html')


# ================================
# app/routes/auth_routes.py
# ================================
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.usuario import Usuario
from functools import wraps

bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))
        
        if session.get('user_rol') not in ['admin', 'asesor']:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        usuario, error = Usuario.verificar_credenciales(email, password)
        
        if error:
            return render_template('login.html', error=error)
        
        # Crear sesión
        session['user_id'] = usuario['id']
        session['user_nombre'] = usuario['nombre']
        session['user_email'] = usuario['email']
        session['user_rol'] = usuario['rol']
        
        if remember:
            session.permanent = True
        
        # Redirigir según rol
        if usuario['rol'] in ['admin', 'asesor']:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.index'))
    
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
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
        usuario_id, error = Usuario.crear_usuario(
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
        
        # Registro exitoso
        return redirect(url_for('auth.login', success='Cuenta creada exitosamente'))
    
    return render_template('register.html')

@bp.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('main.index'))


# ================================
# app/routes/admin_routes.py
# ================================
from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.auth_routes import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard principal del administrador"""
    return render_template('admin/dashboard.html')

@bp.route('/reportes')
@admin_required
def reportes():
    """Página de reportes"""
    return render_template('admin/reportes.html')

@bp.route('/clientes')
@admin_required
def clientes():
    """Página de gestión de clientes"""
    return render_template('admin/clientes.html')

@bp.route('/simulador')
@admin_required
def simulador():
    """Simulador de préstamos"""
    return render_template('admin/simulador.html')


# ================================
# app/services/auth_service.py
# ================================
import bcrypt
from datetime import datetime, timedelta
import jwt
from flask import current_app

class AuthService:
    @staticmethod
    def hash_password(password):
        """Genera hash de contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verifica una contraseña contra su hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id, expiration_hours=24):
        """Genera un token JWT"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expiration_hours)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """Verifica un token JWT"""
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], 
                               algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


# ================================
# app/utils/validators.py
# ================================
import re

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_celular_colombia(celular):
    """Valida número de celular colombiano"""
    pattern = r'^3\d{9}$'
    celular_limpio = celular.replace(' ', '').replace('-', '')
    return re.match(pattern, celular_limpio) is not None

def validar_documento(tipo, numero):
    """Valida número de documento según tipo"""
    patterns = {
        'CC': r'^\d{6,10}$',
        'CE': r'^\d{6,10}$',
        'TI': r'^\d{10,11}$',
        'PP': r'^[A-Z0-9]{6,10}$'
    }
    return re.match(patterns.get(tipo, ''), numero) is not None

def validar_password(password):
    """Valida que la contraseña cumpla requisitos mínimos"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una letra minúscula"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una letra mayúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe tener al menos un número"
    
    return True, "Contraseña válida"