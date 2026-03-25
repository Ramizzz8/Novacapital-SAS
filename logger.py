"""
logger.py — Sistema de logging JSONL orientado a objetos
Novacapital SAS

Arquitectura:
    LogEntry        Clase base: modelo de un registro de log
    JSONLLogger     Clase base: persistencia en archivos .jsonl
    AuthLogger      Subclase: eventos de autenticación  (logs/auth.jsonl)
    LoanLogger      Subclase: eventos de préstamos      (logs/loans.jsonl)
    AdminLogger     Subclase: acciones administrativas  (logs/admin.jsonl)
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# CLASES DE MODELO — orientadas a objetos
# ============================================================

@dataclass
class LogEntry:
    """Clase base que representa un registro de log."""
    event: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    user_id: Optional[int] = None
    ip: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la entrada filtrando campos nulos."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_jsonl(self) -> str:
        """Devuelve una línea JSON lista para escribir en el archivo."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class AuthEntry(LogEntry):
    """Registro de evento de autenticación."""
    email: Optional[str] = None
    rol: Optional[str] = None
    resultado: Optional[str] = None   # 'exitoso' | 'fallido'
    razon: Optional[str] = None


@dataclass
class LoanEntry(LogEntry):
    """Registro de evento relacionado con un préstamo."""
    prestamo_id: Optional[int] = None
    numero_prestamo: Optional[str] = None
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    monto: Optional[float] = None
    cliente_id: Optional[int] = None


@dataclass
class AdminEntry(LogEntry):
    """Registro de acción administrativa."""
    accion: Optional[str] = None
    objetivo_id: Optional[int] = None
    detalle: Optional[str] = None


# ============================================================
# CLASE DE PERSISTENCIA — lectura y escritura JSONL
# ============================================================

class JSONLLogger:
    """
    Maneja la persistencia de registros LogEntry en archivos JSONL.
    Cada línea del archivo es un objeto JSON independiente.
    """

    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

    def __init__(self, filename: str):
        self.filepath = os.path.join(self.LOG_DIR, filename)
        os.makedirs(self.LOG_DIR, exist_ok=True)

    # --- escritura ---

    def write(self, entry: LogEntry) -> None:
        """Agrega una entrada al final del archivo JSONL (append)."""
        try:
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(entry.to_jsonl() + '\n')
        except OSError:
            pass  # No interrumpir la aplicación si el log falla

    # --- lectura ---

    def read_all(self) -> List[Dict[str, Any]]:
        """Lee todos los registros del archivo JSONL."""
        if not os.path.exists(self.filepath):
            return []
        entries = []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries

    def read_last(self, n: int = 100) -> List[Dict[str, Any]]:
        """Devuelve los últimos N registros (más recientes primero)."""
        all_entries = self.read_all()
        return list(reversed(all_entries[-n:]))

    def read_filtered(self, event: str = None, user_id: int = None) -> List[Dict[str, Any]]:
        """Filtra registros por tipo de evento y/o usuario."""
        entries = self.read_all()
        if event:
            entries = [e for e in entries if e.get('event') == event]
        if user_id is not None:
            entries = [e for e in entries if e.get('user_id') == user_id]
        return list(reversed(entries))

    def total(self) -> int:
        """Cuenta el número total de registros."""
        return len(self.read_all())


# ============================================================
# LOGGERS ESPECIALIZADOS
# ============================================================

class AuthLogger(JSONLLogger):
    """Logger para eventos de autenticación → logs/auth.jsonl"""

    def __init__(self):
        super().__init__('auth.jsonl')

    def log_login(self, email: str, ip: str, exitoso: bool,
                  user_id: int = None, rol: str = None, razon: str = None) -> None:
        entry = AuthEntry(
            event='login_exitoso' if exitoso else 'login_fallido',
            user_id=user_id,
            ip=ip,
            email=email,
            rol=rol,
            resultado='exitoso' if exitoso else 'fallido',
            razon=razon,
        )
        self.write(entry)

    def log_logout(self, user_id: int, email: str, ip: str) -> None:
        entry = AuthEntry(
            event='logout',
            user_id=user_id,
            ip=ip,
            email=email,
        )
        self.write(entry)

    def log_register(self, user_id: int, email: str, ip: str) -> None:
        entry = AuthEntry(
            event='registro_nuevo_cliente',
            user_id=user_id,
            ip=ip,
            email=email,
            rol='cliente',
            resultado='exitoso',
        )
        self.write(entry)


class LoanLogger(JSONLLogger):
    """Logger para eventos de préstamos → logs/loans.jsonl"""

    def __init__(self):
        super().__init__('loans.jsonl')

    def log_nueva_solicitud(self, prestamo_id: int, numero: str,
                            cliente_id: int, monto, user_id: int, ip: str) -> None:
        try:
            monto_float = float(str(monto).replace('$', '').replace(',', '')) if monto else None
        except (ValueError, TypeError):
            monto_float = None

        entry = LoanEntry(
            event='nueva_solicitud',
            user_id=user_id,
            ip=ip,
            prestamo_id=prestamo_id,
            numero_prestamo=numero,
            cliente_id=cliente_id,
            monto=monto_float,
            estado_nuevo='solicitado',
        )
        self.write(entry)

    def log_cambio_estado(self, prestamo_id: int, numero: str,
                          estado_anterior: str, estado_nuevo: str,
                          admin_id: int, ip: str) -> None:
        entry = LoanEntry(
            event='cambio_estado_prestamo',
            user_id=admin_id,
            ip=ip,
            prestamo_id=prestamo_id,
            numero_prestamo=numero,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
        )
        self.write(entry)


class AdminLogger(JSONLLogger):
    """Logger para acciones administrativas → logs/admin.jsonl"""

    def __init__(self):
        super().__init__('admin.jsonl')

    def log_crear_asesor(self, asesor_id: int, nombre: str, email: str,
                         admin_id: int, ip: str) -> None:
        entry = AdminEntry(
            event='crear_asesor',
            user_id=admin_id,
            ip=ip,
            accion='crear_asesor',
            objetivo_id=asesor_id,
            detalle=f'Asesor creado: {nombre} ({email})',
        )
        self.write(entry)

    def log_toggle_asesor(self, asesor_id: int, nuevo_estado: bool,
                          admin_id: int, ip: str) -> None:
        estado = 'activado' if nuevo_estado else 'desactivado'
        entry = AdminEntry(
            event='toggle_asesor',
            user_id=admin_id,
            ip=ip,
            accion='toggle_asesor',
            objetivo_id=asesor_id,
            detalle=f'Asesor {asesor_id} {estado}',
        )
        self.write(entry)

    def log_asignar_asesor(self, cliente_id: int, asesor_id: int,
                           admin_id: int, ip: str) -> None:
        entry = AdminEntry(
            event='asignar_asesor',
            user_id=admin_id,
            ip=ip,
            accion='asignar_asesor',
            objetivo_id=cliente_id,
            detalle=f'Cliente {cliente_id} asignado a asesor {asesor_id}',
        )
        self.write(entry)


# ============================================================
# INSTANCIAS GLOBALES (singleton por módulo)
# ============================================================

auth_logger  = AuthLogger()
loan_logger  = LoanLogger()
admin_logger = AdminLogger()
