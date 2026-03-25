# Manual de Usuario – Novacapital SAS

En este manual se explica cómo usar la plataforma de Novacapital desde el punto de vista de cada tipo de usuario: **Cliente**, **Asesor** y **Administrador**.

---

## 1) Acceso al sistema

1. Abre el navegador y entra a: `http://localhost:5000` (o la URL productiva que te asigne la empresa).
2. Haz clic en **Iniciar Sesión**.
3. Ingresa correo y contraseña.

Si aún no tienes cuenta de cliente:

1. Ve a **Regístrate aquí**.
2. Diligencia el formulario con tus datos.
3. Acepta términos y finaliza el registro.

---

## 2) Manual para Cliente

### 2.1 Registrar una cuenta

En el formulario de registro diligencia:

- Nombres y apellidos.
- Tipo y número de documento.
- Fecha de nacimiento.
- Email y celular.
- Dirección, ciudad, departamento.
- Tipo de cliente (empleado público / pensionado).
- Entidad empleadora y salario mensual.
- Contraseña.

Al finalizar, inicia sesión con tus credenciales.

### 2.2 Iniciar una solicitud de préstamo

1. Inicia sesión como cliente.
2. Entra al módulo **Solicitud de Préstamo**.
3. Completa los 4 pasos del formulario:

#### Paso 1: Datos personales

- Documento, nombres, apellidos.
- Fecha de nacimiento.
- Contacto y dirección.

#### Paso 2: Datos laborales

- Tipo de empleado.
- Entidad empleadora o fondo.
- Salario mensual y otros ingresos.

#### Paso 3: Información del préstamo

- Monto solicitado (entre $1.000.000 y $50.000.000).
- Plazo en meses.
- Datos bancarios de desembolso.

#### Paso 4: Documentos

- Adjunta los soportes requeridos.
- Verifica que cada archivo sea legible antes de enviar.

4. Haz clic en **Enviar**.
5. Verás la pantalla de **Solicitud exitosa** con confirmación.

### 2.3 Consultar estado de solicitudes

Desde **Dashboard Cliente** puedes:

- Revisar solicitudes enviadas.
- Ver estado (solicitado, en revisión, aprobado, etc.).
- Consultar información básica de tus créditos.

### 2.4 Actualizar configuración y preferencias

En **Configuración** puedes ajustar:

- Apariencia.
- Idioma.
- Preferencias de notificaciones.

---

## 3) Manual para Asesor

El asesor accede a su panel para acompañamiento comercial.

### 3.1 Funciones principales del asesor

- Ver su dashboard de gestión.
- Consultar clientes asignados.
- Revisar solicitudes pendientes.
- Dar trazabilidad comercial a los casos.

### 3.2 Buenas prácticas del asesor

- Priorizar solicitudes por antigüedad/urgencia.
- Mantener registro claro de observaciones.
- Notificar oportunamente avances al cliente.

---

## 4) Manual para Administrador

El administrador tiene acceso operativo completo.

### 4.1 Dashboard administrativo

Visualiza métricas globales del negocio, por ejemplo:

- Total de clientes.
- Solicitudes pendientes.
- Préstamos aprobados.
- Resumen de actividad.

### 4.2 Gestión de clientes

Desde **Gestión de Clientes** puede:

- Buscar y consultar clientes.
- Revisar información personal y financiera.
- Evaluar estado general de cartera.

### 4.3 Gestión de solicitudes y préstamos

Desde **Solicitudes y Préstamos** puede:

- Revisar solicitudes recibidas.
- Asignar asesor responsable.
- Actualizar estado y observaciones.
- Coordinar respuesta al cliente.

### 4.4 Gestión de asesores

Desde **Gestión de Asesores** puede:

- Crear nuevos asesores.
- Activar o desactivar asesores existentes.
- Consultar carga operativa por asesor.

### 4.5 Reportes

Desde **Reportes** puede:

- Filtrar información por fecha/estado.
- Revisar desempeño comercial.
- Apoyar decisiones operativas.

### 4.6 Configuración del panel

Desde **Configuración** puede modificar parámetros de la experiencia administrativa.

---

## 5) Flujo operativo recomendado

1. Cliente se registra.
2. Cliente envía solicitud.
3. Admin valida información inicial.
4. Admin asigna asesor.
5. Asesor acompaña y documenta avance.
6. Admin consolida decisión final.
7. Se notifica resultado al cliente.

---

## 6) Mensajes de error frecuentes y solución

### “Debes iniciar sesión para acceder a esta página”

- Causa: sesión expirada o no iniciada.
- Solución: vuelve a iniciar sesión.

### “No tienes permisos para acceder a esta página”

- Causa: intentas entrar a un módulo de otro rol.
- Solución: verifica tu rol o solicita permisos.

### Problemas con usuario administrador

- Ejecuta: `python password_generator.py`.
- Usa la opción de reset para el admin si es necesario.

---

## 7) Recomendaciones de seguridad para usuarios

- Usa contraseñas robustas y únicas.
- No compartas tus credenciales.
- Cierra sesión al terminar.
- Evita usar redes públicas para operaciones sensibles.

---

## 8) Soporte interno

Si se presenta un incidente:

1. Toma captura del error.
2. Registra fecha/hora y acción realizada.
3. Escala al equipo de soporte con esos datos.

---

**Fin del manual.**
