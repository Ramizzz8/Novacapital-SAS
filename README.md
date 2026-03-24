# Novacapital SAS – Plataforma de Préstamos por Libranza

Esta aplicación web fue construida con **Flask + MySQL** y sirve para gestionar el ciclo de originación de créditos por libranza: registro de clientes, autenticación por roles, solicitud de préstamo y operación interna para administradores y asesores.

## 1) Características principales

- Registro e inicio de sesión con contraseñas cifradas con `bcrypt`.
- Flujo de solicitud de préstamo en varios pasos para clientes.
- Panel administrativo con:
  - Dashboard de indicadores.
  - Gestión de clientes.
  - Gestión de solicitudes y préstamos.
  - Gestión de asesores (alta / activación / desactivación).
  - Reportes y configuración.
- Panel de asesor para seguimiento comercial.
- Panel de cliente para revisar estado y actualizar datos.

## 2) Arquitectura del proyecto

```text
Novacapital-SAS/
├── app.py                    # Aplicación Flask principal y rutas
├── run.py                    # Script alterno de arranque (requiere ajuste de factory)
├── requirements.txt          # Dependencias Python
├── novacapital_db.sql        # Esquema y datos base de la BD
├── password_generator.py     # Utilidades de diagnóstico y corrección de credenciales
├── templates/                # Vistas HTML (cliente, asesor y admin)
└── static/                   # Recursos estáticos (JS, imágenes)
```

## 3) Requisitos

- Python 3.10+ (recomendado).
- MySQL 8+ o MariaDB compatible.
- pip.

## 4) Instalación y ejecución local

### Paso 1: clonar e ingresar

```bash
git clone <URL_DEL_REPOSITORIO>
cd Novacapital-SAS
```

### Paso 2: crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows PowerShell
```

### Paso 3: instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: preparar base de datos

1. Crea la base de datos (si no existe).
2. Importa el script SQL principal:

```bash
mysql -u <usuario> -p <nombre_bd> < novacapital_db.sql
```

> También existe `usuario.sql` para utilidades puntuales, pero la carga principal está en `novacapital_db.sql`.

### Paso 5: configurar variables de entorno

Crea un archivo `.env` en la raíz:

```env
SECRET_KEY=tu_clave_secreta
MYSQL_HOST=localhost
MYSQL_USER=novacapital
MYSQL_PASSWORD=Novacapital123$
MYSQL_DB=novacapital_db
FLASK_DEBUG=True
PORT=5000
```

### Paso 6: iniciar aplicación

```bash
python app.py
```

La app quedará en: `http://localhost:5000`

## 5) Credenciales y acceso inicial

En el script SQL y en el arranque de `app.py` se usa el usuario administrador:

- **Correo:** `admin@novacapital.com`
- **Contraseña:** `Admin123!`

Si tienes problemas de acceso, ejecuta la utilidad de diagnóstico:

```bash
python password_generator.py
```

## 6) Rutas funcionales relevantes

### Públicas

- `GET /` – Inicio.
- `GET /contacto` – Página de contacto.
- `GET /requisitos` – Requisitos del préstamo.
- `GET|POST /login` – Inicio de sesión.
- `GET|POST /register` – Registro de cliente.

### Cliente autenticado

- `GET|POST /solicitud` – Formulario y envío de solicitud.
- `GET /solicitud-exitosa` – Confirmación.
- `GET /cliente/dashboard` – Panel del cliente.
- `GET /cliente/configuracion` – Configuración del cliente.

### Asesor / Administrador

- `GET /admin/dashboard` – Dashboard operativo.
- `GET /admin/clientes` – Gestión de clientes.
- `GET /admin/solicitudes` – Gestión de solicitudes.
- `POST /admin/asignar-asesor` – Asignación de asesor.
- `POST /admin/enviar-notificacion` – Envío de notificaciones.
- `GET /admin/asesores` – Gestión de asesores.
- `POST /admin/crear-asesor` – Alta de asesor.
- `POST /admin/toggle-asesor/<id>` – Activar/desactivar asesor.
- `GET /admin/reportes` – Reportes.
- `GET /admin/configuracion` – Configuración del panel.

## 7) Modelo de roles

- **cliente:** puede registrarse, solicitar crédito y hacer seguimiento.
- **asesor:** accede a funciones comerciales y acompañamiento.
- **admin:** control total de operación y administración.

## 8) Estructura de datos (tablas clave)

- `usuarios`: autenticación, rol y estado activo.
- `clientes`: perfil demográfico/laboral del cliente.
- `prestamos`: solicitudes y estado de préstamos.
- `asignaciones_asesores`: relación asesor-cliente/solicitud.
- `notificaciones`, `pagos`, `bitacora`, etc. para operación.

## 9) Mantenimiento y troubleshooting

### Error de credenciales o hashes

Ejecuta:

```bash
python password_generator.py
```

Incluye opciones para:

- Verificar estructura.
- Corregir columnas.
- Resetear usuario administrador.
- Probar login.

### Error de conexión MySQL

Valida:

1. Servicio MySQL iniciado.
2. Usuario/clave correctos en `.env`.
3. Base de datos importada.

## 10) Manual de usuario

Consulta el documento completo aquí:

- **[`MANUAL_USUARIO.md`](./MANUAL_USUARIO.md)**

