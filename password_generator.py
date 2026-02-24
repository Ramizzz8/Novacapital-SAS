"""
Script de diagnóstico y corrección - Novacapital
Ejecuta esto para verificar y corregir problemas
"""

import bcrypt
import MySQLdb
from dotenv import load_dotenv
import os

load_dotenv()

def conectar_bd():
    """Conecta a la base de datos"""
    try:
        db = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'novacapital'),
            password=os.getenv('MYSQL_PASSWORD', 'Novacapital123$'),
            db=os.getenv('MYSQL_DB', 'novacapital_db'),
            charset='utf8mb4'
        )
        return db
    except Exception as e:
        print(f"❌ Error al conectar: {str(e)}")
        return None

def verificar_estructura_bd():
    """Verifica la estructura de las tablas"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO ESTRUCTURA DE BASE DE DATOS")
    print("="*70 + "\n")
    
    db = conectar_bd()
    if not db:
        return False
    
    cursor = db.cursor()
    
    # Verificar tabla usuarios
    print("📋 Estructura de tabla 'usuarios':")
    cursor.execute("DESCRIBE usuarios")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Verificar si password_hash tiene longitud suficiente
    cursor.execute("SHOW COLUMNS FROM usuarios LIKE 'password_hash'")
    result = cursor.fetchone()
    if result:
        tipo = result[1]
        print(f"\n✓ Tipo de password_hash: {tipo}")
        if 'varchar(255)' not in tipo.lower() and 'varchar(60)' not in tipo.lower():
            print("⚠️  ADVERTENCIA: password_hash debería ser VARCHAR(255)")
    
    print("\n📋 Estructura de tabla 'clientes':")
    cursor.execute("DESCRIBE clientes")
    tiene_usuario_id = False
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
        if row[0] == 'usuario_id':
            tiene_usuario_id = True
    
    if not tiene_usuario_id:
        print("\n⚠️  FALTA columna 'usuario_id' en tabla clientes")
    else:
        print("\n✓ Columna 'usuario_id' existe")
    
    cursor.close()
    db.close()
    return True

def corregir_estructura_bd():
    """Corrige la estructura de la base de datos"""
    print("\n" + "="*70)
    print("🔧 CORRIGIENDO ESTRUCTURA DE BASE DE DATOS")
    print("="*70 + "\n")
    
    db = conectar_bd()
    if not db:
        return False
    
    cursor = db.cursor()
    
    try:
        # Corregir password_hash
        print("🔧 Ajustando longitud de password_hash...")
        cursor.execute("ALTER TABLE usuarios MODIFY COLUMN password_hash VARCHAR(255) NOT NULL")
        print("✓ password_hash corregido")
        
        # Verificar si existe usuario_id
        cursor.execute("SHOW COLUMNS FROM clientes LIKE 'usuario_id'")
        if not cursor.fetchone():
            print("🔧 Agregando columna usuario_id a tabla clientes...")
            cursor.execute("""
                ALTER TABLE clientes 
                ADD COLUMN usuario_id INT NULL AFTER id,
                ADD KEY idx_usuario_id (usuario_id)
            """)
            print("✓ Columna usuario_id agregada")
        else:
            print("✓ Columna usuario_id ya existe")
        
        db.commit()
        print("\n✅ Estructura corregida exitosamente\n")
        
    except Exception as e:
        print(f"❌ Error al corregir estructura: {str(e)}")
        db.rollback()
        return False
    finally:
        cursor.close()
        db.close()
    
    return True

def crear_hash_correcto(password):
    """Genera hash de bcrypt correctamente"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def resetear_usuario_admin():
    """Resetea el usuario administrador con hash correcto"""
    print("\n" + "="*70)
    print("👤 RESETEANDO USUARIO ADMINISTRADOR")
    print("="*70 + "\n")
    
    db = conectar_bd()
    if not db:
        return False
    
    cursor = db.cursor()
    
    try:
        # Eliminar admin existente
        cursor.execute("DELETE FROM usuarios WHERE email = 'admin@novacapital.com'")
        print("🗑️  Usuario admin anterior eliminado")
        
        # Crear hash correcto
        password = 'Admin123!'
        hash_correcto = crear_hash_correcto(password)
        
        print(f"🔐 Generando nuevo hash...")
        print(f"   Password: {password}")
        print(f"   Hash (primeros 50 chars): {hash_correcto[:50]}...")
        print(f"   Longitud del hash: {len(hash_correcto)}")
        
        # Insertar usuario con hash correcto
        query = """
            INSERT INTO usuarios (nombre, email, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, ('Administrador Sistema', 'admin@novacapital.com', hash_correcto, 'admin', True))
        db.commit()
        
        print("\n✅ Usuario administrador creado exitosamente")
        print("   Email: admin@novacapital.com")
        print("   Password: Admin123!")
        
        # Verificar que se creó correctamente
        cursor.execute("SELECT id, nombre, email, LENGTH(password_hash) as hash_len FROM usuarios WHERE email = 'admin@novacapital.com'")
        result = cursor.fetchone()
        if result:
            print(f"\n✓ Verificación:")
            print(f"   ID: {result[0]}")
            print(f"   Nombre: {result[1]}")
            print(f"   Email: {result[2]}")
            print(f"   Longitud hash: {result[3]}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        return False
    finally:
        cursor.close()
        db.close()
    
    return True

def probar_login():
    """Prueba el login del usuario admin"""
    print("\n" + "="*70)
    print("🧪 PROBANDO LOGIN")
    print("="*70 + "\n")
    
    db = conectar_bd()
    if not db:
        return False
    
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        email = 'admin@novacapital.com'
        password = 'Admin123!'
        
        # Obtener usuario
        cursor.execute("SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            print(f"❌ Usuario {email} no encontrado")
            return False
        
        print(f"✓ Usuario encontrado: {usuario['nombre']}")
        print(f"  Email: {usuario['email']}")
        print(f"  Rol: {usuario['rol']}")
        print(f"  Hash length: {len(usuario['password_hash'])}")
        
        # Verificar password
        password_hash = usuario['password_hash']
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        
        print(f"\n🔐 Verificando password '{password}'...")
        
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            print("✅ ¡PASSWORD CORRECTA! El login debería funcionar")
            return True
        else:
            print("❌ PASSWORD INCORRECTA")
            print("\n💡 Ejecuta la opción 3 para resetear el usuario admin")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        cursor.close()
        db.close()

def menu():
    """Menú interactivo"""
    while True:
        print("\n" + "="*70)
        print("  🏦 NOVACAPITAL - HERRAMIENTA DE DIAGNÓSTICO Y CORRECCIÓN")
        print("="*70)
        print("\n1. Verificar estructura de base de datos")
        print("2. Corregir estructura de base de datos")
        print("3. Resetear usuario administrador")
        print("4. Probar login")
        print("5. Ejecutar TODAS las correcciones")
        print("6. Salir")
        print()
        
        opcion = input("Selecciona una opción: ")
        
        if opcion == '1':
            verificar_estructura_bd()
            
        elif opcion == '2':
            corregir_estructura_bd()
            
        elif opcion == '3':
            resetear_usuario_admin()
            
        elif opcion == '4':
            probar_login()
            
        elif opcion == '5':
            print("\n🚀 EJECUTANDO TODAS LAS CORRECCIONES...\n")
            if corregir_estructura_bd():
                if resetear_usuario_admin():
                    print("\n" + "="*70)
                    print("  ✅ TODAS LAS CORRECCIONES COMPLETADAS")
                    print("="*70)
                    print("\n  Ahora puedes hacer login con:")
                    print("  📧 Email: admin@novacapital.com")
                    print("  🔐 Password: Admin123!")
                    print("\n  Ejecuta: python app.py")
                    print("  Luego ve a: http://localhost:5000/login")
                    print("="*70 + "\n")
                    probar_login()
            
        elif opcion == '6':
            print("\n¡Hasta luego!\n")
            break
            
        else:
            print("\n❌ Opción inválida\n")
        
        if opcion != '6':
            input("\nPresiona Enter para continuar...")

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     🏦 NOVACAPITAL - HERRAMIENTA DE DIAGNÓSTICO                   ║
║                                                                    ║
║  Esta herramienta soluciona los problemas comunes:               ║
║                                                                    ║
║  ❌ Error: "Data truncated for column 'rol'"                     ║
║  ❌ Error: "Unknown column 'usuario_id'"                         ║
║  ❌ Error: "Contraseña incorrecta"                               ║
║                                                                    ║
║  💡 Recomendación: Ejecuta la opción 5 para solucionarlo todo   ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    menu()