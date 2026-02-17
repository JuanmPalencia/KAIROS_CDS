"""
KAIROS CDS — Módulo central de ciberseguridad.

Contiene: rate-limiter, detección de fuerza bruta, validación de entrada,
security headers middleware, IP blacklisting, session tracking y
generación de alertas de seguridad.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import re
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("kairos.security")

# ═══════════════════════════════════════════════════════════════════════
# 1. IN-MEMORY STORES  (lightweight — no Redis dependency required)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class _RateEntry:
    hits: int = 0
    window_start: float = 0.0

@dataclass
class _BruteForceEntry:
    failures: int = 0
    first_failure: float = 0.0
    locked_until: float = 0.0

@dataclass
class SecurityEvent:
    timestamp: str
    event_type: str          # BRUTE_FORCE | RATE_LIMIT | SUSPICIOUS_INPUT | BLOCKED_IP | TOKEN_REUSE ...
    severity: str            # LOW | MEDIUM | HIGH | CRITICAL
    source_ip: str
    details: str
    user: Optional[str] = None
    blocked: bool = False

# Global stores
_rate_limits: dict[str, _RateEntry] = defaultdict(_RateEntry)
_brute_force: dict[str, _BruteForceEntry] = defaultdict(_BruteForceEntry)
_blocked_ips: dict[str, dict] = {}       # ip → {reason, blocked_at}
_security_events: list[SecurityEvent] = []
_active_sessions: dict[str, dict] = {}   # token_hash → {user, ip, created, last_seen}

MAX_SECURITY_EVENTS = 2000


# ═══════════════════════════════════════════════════════════════════════
# 2. RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════

# Limits: requests per window (seconds)
RATE_LIMITS = {
    "/api/auth/login":    (5,  60),    # 5 intentos por minuto
    "/api/auth/register": (3,  60),    # 3 por minuto
    "/api/auth/init-admin":(2, 300),   # 2 en 5 min
    "DEFAULT":            (120, 60),   # 120 req/min general
}

def _get_rate_key(ip: str, path: str) -> str:
    """Generar clave de rate-limit por IP + ruta."""
    # Normalizar path — quitar query strings
    base = path.split("?")[0].rstrip("/")
    return f"{ip}:{base}"


def check_rate_limit(ip: str, path: str) -> tuple[bool, int]:
    """Devuelve (allowed, retry_after_seconds). allowed=False si está limitado."""
    base_path = path.split("?")[0].rstrip("/")
    max_hits, window = RATE_LIMITS.get(base_path, RATE_LIMITS["DEFAULT"])

    key = _get_rate_key(ip, base_path)
    entry = _rate_limits[key]
    now = time.time()

    if now - entry.window_start > window:
        entry.hits = 1
        entry.window_start = now
        return True, 0

    entry.hits += 1
    if entry.hits > max_hits:
        retry = int(window - (now - entry.window_start)) + 1
        return False, retry

    return True, 0


# ═══════════════════════════════════════════════════════════════════════
# 3. BRUTE-FORCE DETECTOR
# ═══════════════════════════════════════════════════════════════════════

BRUTE_FORCE_THRESHOLD = 5          # fallos antes de lock
BRUTE_FORCE_WINDOW    = 300        # ventana de 5 min
BRUTE_FORCE_LOCKOUT   = 600        # lock de 10 min


def record_login_failure(ip: str, username: str = ""):
    """Registrar un intento de login fallido."""
    entry = _brute_force[ip]
    now = time.time()

    # Reset si la ventana expiró
    if now - entry.first_failure > BRUTE_FORCE_WINDOW:
        entry.failures = 0
        entry.first_failure = now

    if entry.failures == 0:
        entry.first_failure = now

    entry.failures += 1

    if entry.failures >= BRUTE_FORCE_THRESHOLD:
        entry.locked_until = now + BRUTE_FORCE_LOCKOUT
        _emit_event(
            event_type="BRUTE_FORCE",
            severity="HIGH",
            source_ip=ip,
            details=f"IP bloqueada por {BRUTE_FORCE_LOCKOUT}s tras {entry.failures} intentos fallidos. Último user: {username}",
            blocked=True,
        )
        logger.warning("[SEC] Brute-force lockout: %s (%d failures)", ip, entry.failures)


def record_login_success(ip: str):
    """Limpiar registro de fuerza bruta tras login exitoso."""
    _brute_force.pop(ip, None)


def is_brute_force_locked(ip: str) -> tuple[bool, int]:
    """Devuelve (locked, seconds_remaining)."""
    entry = _brute_force.get(ip)
    if not entry:
        return False, 0
    now = time.time()
    if entry.locked_until > now:
        return True, int(entry.locked_until - now)
    return False, 0


# ═══════════════════════════════════════════════════════════════════════
# 4. INPUT SANITIZATION / SUSPICIOUS PATTERN DETECTION
# ═══════════════════════════════════════════════════════════════════════

_SQL_INJECTION_PATTERNS = [
    r"(\b(UNION|SELECT|INSERT|DELETE|UPDATE|DROP|ALTER|CREATE|EXEC)\b.*\b(FROM|INTO|TABLE|SET|WHERE)\b)",
    r"(--|;|/\*|\*/|xp_|sp_)",
    r"('\s*(OR|AND)\s*'?\s*\d+\s*=\s*\d+)",
    r"(SLEEP\s*\(|BENCHMARK\s*\(|WAITFOR\s+DELAY)",
]

_XSS_PATTERNS = [
    r"<\s*script",
    r"javascript\s*:",
    r"on(error|load|click|mouseover)\s*=",
    r"<\s*iframe",
    r"<\s*object",
    r"<\s*embed",
    r"document\.(cookie|location|write)",
    r"eval\s*\(",
]

_PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e",
    r"%252e%252e",
]

_COMPILED_SQL = [re.compile(p, re.IGNORECASE) for p in _SQL_INJECTION_PATTERNS]
_COMPILED_XSS = [re.compile(p, re.IGNORECASE) for p in _XSS_PATTERNS]
_COMPILED_PATH = [re.compile(p, re.IGNORECASE) for p in _PATH_TRAVERSAL_PATTERNS]


def scan_input(value: str) -> Optional[str]:
    """Escanea un string y devuelve el tipo de amenaza o None si limpio."""
    if not value:
        return None
    for pat in _COMPILED_SQL:
        if pat.search(value):
            return "SQL_INJECTION"
    for pat in _COMPILED_XSS:
        if pat.search(value):
            return "XSS"
    for pat in _COMPILED_PATH:
        if pat.search(value):
            return "PATH_TRAVERSAL"
    return None


def sanitize_string(value: str) -> str:
    """Sanitizar HTML básico de un string (sin eliminar datos válidos)."""
    return (
        value
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# ═══════════════════════════════════════════════════════════════════════
# 5. IP BLOCKING
# ═══════════════════════════════════════════════════════════════════════

def block_ip(ip: str, reason: str = "manual"):
    _blocked_ips[ip] = {
        "reason": reason,
        "blocked_at": datetime.now(timezone.utc).isoformat(),
    }
    _emit_event("BLOCKED_IP", "HIGH", ip, f"IP bloqueada: {reason}", blocked=True)

def unblock_ip(ip: str):
    _blocked_ips.pop(ip, None)

def is_ip_blocked(ip: str) -> bool:
    return ip in _blocked_ips

def get_blocked_ips() -> list[dict]:
    return [
        {"ip": ip, "reason": info["reason"], "blocked_at": info["blocked_at"]}
        for ip, info in sorted(_blocked_ips.items())
    ]


def _is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


# ═══════════════════════════════════════════════════════════════════════
# 6. SESSION TRACKING
# ═══════════════════════════════════════════════════════════════════════

def register_session(token: str, username: str, ip: str):
    """Registrar una nueva sesión activa."""
    h = hashlib.sha256(token.encode()).hexdigest()[:16]
    _active_sessions[h] = {
        "user": username,
        "ip": ip,
        "created": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }

def touch_session(token: str):
    """Actualizar last_seen de una sesión."""
    h = hashlib.sha256(token.encode()).hexdigest()[:16]
    if h in _active_sessions:
        _active_sessions[h]["last_seen"] = datetime.now(timezone.utc).isoformat()

def revoke_session(token: str):
    h = hashlib.sha256(token.encode()).hexdigest()[:16]
    _active_sessions.pop(h, None)

def get_active_sessions() -> list[dict]:
    """Lista sesiones activas (sin revelar tokens)."""
    return [
        {"session_id": k, **v}
        for k, v in _active_sessions.items()
    ]


# ═══════════════════════════════════════════════════════════════════════
# 7. SECURITY EVENT LOG
# ═══════════════════════════════════════════════════════════════════════

def _emit_event(
    event_type: str,
    severity: str,
    source_ip: str,
    details: str,
    user: str | None = None,
    blocked: bool = False,
):
    global _security_events
    evt = SecurityEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        severity=severity,
        source_ip=source_ip,
        details=details,
        user=user,
        blocked=blocked,
    )
    _security_events.append(evt)
    if len(_security_events) > MAX_SECURITY_EVENTS:
        _security_events = _security_events[-MAX_SECURITY_EVENTS:]
    logger.info("[SEC-EVENT] %s | %s | %s | %s", severity, event_type, source_ip, details[:120])


def get_security_events(limit: int = 100, severity: str | None = None) -> list[dict]:
    events = _security_events
    if severity:
        events = [e for e in events if e.severity == severity]
    return [
        {
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "severity": e.severity,
            "source_ip": e.source_ip,
            "details": e.details,
            "user": e.user,
            "blocked": e.blocked,
        }
        for e in reversed(events[-limit:])
    ]


def get_security_stats() -> dict:
    """Resumen de métricas de seguridad."""
    now = time.time()
    events_1h = [e for e in _security_events if (now - _iso_to_ts(e.timestamp)) < 3600]
    by_type = defaultdict(int)
    by_severity = defaultdict(int)
    for e in events_1h:
        by_type[e.event_type] += 1
        by_severity[e.severity] += 1

    locked_ips = sum(1 for e in _brute_force.values() if e.locked_until > now)

    return {
        "total_events": len(_security_events),
        "events_last_hour": len(events_1h),
        "by_type": dict(by_type),
        "by_severity": dict(by_severity),
        "blocked_ips": len(_blocked_ips),
        "locked_ips_brute_force": locked_ips,
        "active_sessions": len(_active_sessions),
    }


def _iso_to_ts(iso: str) -> float:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0


# ═══════════════════════════════════════════════════════════════════════
# 8. PASSWORD POLICY
# ═══════════════════════════════════════════════════════════════════════

PASSWORD_MIN_LENGTH       = 8
PASSWORD_REQUIRE_UPPER    = True
PASSWORD_REQUIRE_LOWER    = True
PASSWORD_REQUIRE_DIGIT    = True
PASSWORD_REQUIRE_SPECIAL  = False     # relajado para demo


def validate_password(password: str) -> tuple[bool, str]:
    """Valida que la contraseña cumpla la política. Devuelve (ok, error_msg)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Mínimo {PASSWORD_MIN_LENGTH} caracteres"
    if PASSWORD_REQUIRE_UPPER and not re.search(r"[A-Z]", password):
        return False, "Debe incluir al menos una mayúscula"
    if PASSWORD_REQUIRE_LOWER and not re.search(r"[a-z]", password):
        return False, "Debe incluir al menos una minúscula"
    if PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "Debe incluir al menos un número"
    if PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Debe incluir un carácter especial"
    return True, ""


# ═══════════════════════════════════════════════════════════════════════
# 9. SECURITY HEADERS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade cabeceras de seguridad estándar a todas las respuestas."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Standard security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com; "
            "connect-src 'self' ws: wss: http://localhost:* http://127.0.0.1:* https://api.openai.com; "
            "frame-ancestors 'none'"
        )

        # Remove server fingerprint
        if "server" in response.headers:
            del response.headers["server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response


# ═══════════════════════════════════════════════════════════════════════
# 10. RATE-LIMIT + INPUT SCAN MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware combinado:
    - Bloqueo de IPs
    - Rate-limiting
    - Detección de fuerza bruta (lockout)
    - Escaneo de inputs en query/body
    """

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "0.0.0.0"
        path = request.url.path

        # ── IP block check ──
        if is_ip_blocked(ip):
            return Response(
                content='{"detail":"IP bloqueada"}',
                status_code=403,
                media_type="application/json",
            )

        # ── Rate limit ──
        from app.config import SECURITY_RATE_LIMIT_ENABLED
        if SECURITY_RATE_LIMIT_ENABLED:
            allowed, retry_after = check_rate_limit(ip, path)
        else:
            allowed, retry_after = True, 0
        if not allowed:
            _emit_event("RATE_LIMIT", "MEDIUM", ip, f"Rate-limit superado en {path}")
            return Response(
                content='{"detail":"Demasiadas peticiones. Intenta de nuevo más tarde."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        # ── Brute-force lockout en login ──
        if path.rstrip("/") == "/api/auth/login" and request.method == "POST":
            locked, remaining = is_brute_force_locked(ip)
            if locked:
                return Response(
                    content=f'{{"detail":"Cuenta bloqueada temporalmente. Espera {remaining}s."}}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(remaining)},
                )

        # ── Scan query params ──
        for key, val in request.query_params.items():
            threat = scan_input(val)
            if threat:
                _emit_event(
                    "SUSPICIOUS_INPUT", "HIGH", ip,
                    f"{threat} detectado en query ?{key}=... en {path}",
                    blocked=True,
                )
                return Response(
                    content='{"detail":"Petición bloqueada por contenido sospechoso"}',
                    status_code=400,
                    media_type="application/json",
                )

        # ── Scan URL path ──
        path_threat = scan_input(path)
        if path_threat:
            _emit_event(
                "SUSPICIOUS_INPUT", "HIGH", ip,
                f"{path_threat} detectado en URL path: {path[:200]}",
                blocked=True,
            )
            return Response(
                content='{"detail":"Petición bloqueada"}',
                status_code=400,
                media_type="application/json",
            )

        response = await call_next(request)
        return response


# ═══════════════════════════════════════════════════════════════════════
# 11. CSRF TOKEN UTILS
# ═══════════════════════════════════════════════════════════════════════

_csrf_tokens: dict[str, float] = {}   # token → created_at
CSRF_TOKEN_TTL = 3600                  # 1h


def generate_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    _csrf_tokens[token] = time.time()
    # Limpieza
    cutoff = time.time() - CSRF_TOKEN_TTL
    for k in list(_csrf_tokens):
        if _csrf_tokens[k] < cutoff:
            del _csrf_tokens[k]
    return token


def validate_csrf_token(token: str) -> bool:
    if token not in _csrf_tokens:
        return False
    if time.time() - _csrf_tokens[token] > CSRF_TOKEN_TTL:
        del _csrf_tokens[token]
        return False
    del _csrf_tokens[token]    # single-use
    return True
