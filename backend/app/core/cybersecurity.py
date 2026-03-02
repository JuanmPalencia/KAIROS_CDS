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
    "/api/live":          (9999, 60),  # Excluido: polling del Dashboard (sin límite efectivo)
    "DEFAULT":            (120, 60),   # 120 req/min general
}

def _get_rate_key(ip: str, path: str) -> str:
    """Generar clave de rate-limit por IP + ruta."""
    # Normalizar path — quitar query strings
    base = path.split("?")[0].rstrip("/")
    return f"{ip}:{base}"


def check_rate_limit(ip: str, path: str) -> tuple[bool, int, dict]:
    """Returns (allowed, retry_after_seconds, rate_info).
    rate_info contains: limit, remaining, reset (epoch seconds)."""
    base_path = path.split("?")[0].rstrip("/")
    max_hits, window = RATE_LIMITS.get(base_path, RATE_LIMITS["DEFAULT"])

    key = _get_rate_key(ip, base_path)
    entry = _rate_limits[key]
    now = time.time()

    if now - entry.window_start > window:
        entry.hits = 1
        entry.window_start = now
        return True, 0, {
            "limit": max_hits,
            "remaining": max_hits - 1,
            "reset": int(entry.window_start + window),
        }

    entry.hits += 1
    remaining = max(0, max_hits - entry.hits)
    reset_at = int(entry.window_start + window)

    if entry.hits > max_hits:
        retry = int(window - (now - entry.window_start)) + 1
        return False, retry, {"limit": max_hits, "remaining": 0, "reset": reset_at}

    return True, 0, {"limit": max_hits, "remaining": remaining, "reset": reset_at}


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
    _maybe_queue_alert(evt)
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

        # Skip security headers on CORS preflight to avoid conflicts
        if request.method == "OPTIONS":
            return response

        # Standard security headers - comprehensive protection
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com https://fastapi.tiangolo.com; "
            "connect-src 'self' ws: wss: http://localhost:* http://127.0.0.1:* https://api.openai.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Remove server fingerprint headers
        if "server" in response.headers:
            del response.headers["server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        if "Server" in response.headers:
            del response.headers["Server"]

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
        # Let CORS preflight pass through without any security checks
        if request.method == "OPTIONS":
            return await call_next(request)

        ip = get_real_ip(request)
        path = request.url.path

        # ── IP block check ──
        if is_ip_blocked(ip):
            return Response(
                content='{"detail":"IP bloqueada"}',
                status_code=403,
                media_type="application/json",
            )

        # ── Rate limit ──
        from ..config import SECURITY_RATE_LIMIT_ENABLED
        rate_info = None
        if SECURITY_RATE_LIMIT_ENABLED:
            allowed, retry_after, rate_info = check_rate_limit(ip, path)
        else:
            allowed, retry_after = True, 0
        if not allowed:
            _emit_event("RATE_LIMIT", "MEDIUM", ip, f"Rate-limit superado en {path}")
            return Response(
                content='{"detail":"Demasiadas peticiones. Intenta de nuevo más tarde."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_info["limit"]) if rate_info else "0",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]) if rate_info else "0",
                },
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

        # ── Scan request body (JSON POST/PUT/PATCH) ──
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            base_path = path.split("?")[0].rstrip("/")
            if "application/json" in content_type and base_path not in _BODY_SCAN_SKIP_PATHS:
                try:
                    body_bytes = await request.body()
                    body_text = body_bytes.decode("utf-8", errors="ignore")
                    if len(body_text) < 65536:
                        body_threat = _scan_json_values(body_text)
                        if body_threat:
                            _emit_event(
                                "SUSPICIOUS_INPUT", "HIGH", ip,
                                f"{body_threat[0]} detectado en body field "
                                f"'{body_threat[1]}' en {path}",
                                blocked=True,
                            )
                            return Response(
                                content='{"detail":"Petición bloqueada por contenido sospechoso en body"}',
                                status_code=400,
                                media_type="application/json",
                            )
                except Exception:
                    pass

        response = await call_next(request)

        # ── Add rate limit headers to all responses ──
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

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


# ═══════════════════════════════════════════════════════════════════════
# 12. JWT TOKEN BLACKLIST (real revocation on logout)
# ═══════════════════════════════════════════════════════════════════════

_token_blacklist: dict[str, float] = {}   # jti → expiry timestamp
_TOKEN_BLACKLIST_CLEANUP_INTERVAL = 300
_last_blacklist_cleanup: float = 0.0


def blacklist_token(jti: str, exp_timestamp: float):
    """Add a JTI to the blacklist. Auto-expires when token would have."""
    global _last_blacklist_cleanup
    _token_blacklist[jti] = exp_timestamp
    now = time.time()
    if now - _last_blacklist_cleanup > _TOKEN_BLACKLIST_CLEANUP_INTERVAL:
        _last_blacklist_cleanup = now
        expired = [k for k, v in _token_blacklist.items() if v < now]
        for k in expired:
            del _token_blacklist[k]
    _emit_event("TOKEN_REVOKED", "LOW", "system", f"Token revocado: jti={jti[:8]}...")


def is_token_blacklisted(jti: str) -> bool:
    """Check if a JTI has been revoked."""
    if jti not in _token_blacklist:
        return False
    if _token_blacklist[jti] < time.time():
        del _token_blacklist[jti]
        return False
    return True


def get_blacklist_size() -> int:
    return len(_token_blacklist)


# ═══════════════════════════════════════════════════════════════════════
# 13. REAL CLIENT IP EXTRACTION (X-Forwarded-For support)
# ═══════════════════════════════════════════════════════════════════════

def get_real_ip(request: Request) -> str:
    """Extract the real client IP considering reverse proxies.

    Priority: CF-Connecting-IP > X-Real-IP > X-Forwarded-For > client.host
    """
    from ..config import TRUSTED_PROXY_COUNT

    if TRUSTED_PROXY_COUNT == 0:
        return request.client.host if request.client else "0.0.0.0"

    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    xff = request.headers.get("x-forwarded-for")
    if xff:
        ips = [ip.strip() for ip in xff.split(",")]
        idx = max(0, len(ips) - TRUSTED_PROXY_COUNT)
        candidate = ips[idx] if idx < len(ips) else ips[0]
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            pass

    return request.client.host if request.client else "0.0.0.0"


# ═══════════════════════════════════════════════════════════════════════
# 14. REQUEST BODY INJECTION SCANNING
# ═══════════════════════════════════════════════════════════════════════

import json as _json

_BODY_SCAN_SKIP_PATHS = {
    "/api/security/scan-input",    # The threat scanner tool itself
    "/api/security/check-password",
}


def _scan_json_values(text: str) -> Optional[tuple[str, str]]:
    """Recursively scan all string values in a JSON body.
    Returns (threat_type, field_name) or None."""
    try:
        data = _json.loads(text)
    except (ValueError, TypeError):
        return None
    return _scan_obj(data, "")


def _scan_obj(obj, prefix: str) -> Optional[tuple[str, str]]:
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            result = _scan_obj(val, path)
            if result:
                return result
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            result = _scan_obj(item, f"{prefix}[{i}]")
            if result:
                return result
    elif isinstance(obj, str):
        threat = scan_input(obj)
        if threat:
            return (threat, prefix)
    return None


# ═══════════════════════════════════════════════════════════════════════
# 15. HIBP PASSWORD BREACH CHECK (k-anonymity, privacy-safe)
# ═══════════════════════════════════════════════════════════════════════

_breach_cache: dict[str, tuple[bool, int]] = {}
_BREACH_CACHE_MAX = 500


async def check_password_breach(password: str) -> tuple[bool, int]:
    """Check HIBP Pwned Passwords using k-anonymity.
    Only sends first 5 chars of SHA-1 hash (never the full hash or password).
    Returns (is_breached, breach_count).
    """
    import httpx

    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]

    cache_key = f"{prefix}:{suffix}"
    if cache_key in _breach_cache:
        return _breach_cache[cache_key]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "KAIROS-CDS-Security/1.0"},
            )
            if resp.status_code != 200:
                return False, 0

            for line in resp.text.splitlines():
                parts = line.strip().split(":")
                if len(parts) == 2 and parts[0] == suffix:
                    count = int(parts[1])
                    result = (True, count)
                    _cache_breach(cache_key, result)
                    return result

            result = (False, 0)
            _cache_breach(cache_key, result)
            return result
    except Exception:
        return False, 0  # Fail open


def _cache_breach(key: str, val: tuple[bool, int]):
    if len(_breach_cache) > _BREACH_CACHE_MAX:
        keys = list(_breach_cache.keys())[:_BREACH_CACHE_MAX // 2]
        for k in keys:
            del _breach_cache[k]
    _breach_cache[key] = val


# ═══════════════════════════════════════════════════════════════════════
# 16. LOGIN ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class LoginRecord:
    timestamp: float
    ip: str
    username: str

_login_history: dict[str, list[LoginRecord]] = defaultdict(list)
_user_known_ips: dict[str, set[str]] = defaultdict(set)
MAX_LOGIN_HISTORY_PER_USER = 50

UNUSUAL_HOUR_START = 2    # 02:00 UTC
UNUSUAL_HOUR_END = 5      # 05:00 UTC
IMPOSSIBLE_TRAVEL_SECONDS = 3600  # 1 hour


def record_login_for_anomaly(username: str, ip: str) -> list[dict]:
    """Record a login and return any anomalies detected."""
    now = time.time()
    anomalies = []
    record = LoginRecord(timestamp=now, ip=ip, username=username)

    # 1. NEW IP DETECTION
    known = _user_known_ips[username]
    if known and ip not in known:
        anomalies.append({
            "type": "NEW_IP",
            "severity": "MEDIUM",
            "details": f"Login from new IP {ip} for user '{username}'. "
                       f"Known IPs: {', '.join(list(known)[:5])}",
        })
    known.add(ip)

    # 2. UNUSUAL HOUR DETECTION
    login_hour = datetime.now(timezone.utc).hour
    if UNUSUAL_HOUR_START <= login_hour < UNUSUAL_HOUR_END:
        anomalies.append({
            "type": "UNUSUAL_HOUR",
            "severity": "LOW",
            "details": f"Login at unusual hour (UTC {login_hour:02d}:xx) "
                       f"for user '{username}' from {ip}",
        })

    # 3. IMPOSSIBLE TRAVEL DETECTION
    history = _login_history[username]
    if history:
        last = history[-1]
        time_diff = now - last.timestamp
        if time_diff < IMPOSSIBLE_TRAVEL_SECONDS and last.ip != ip:
            anomalies.append({
                "type": "IMPOSSIBLE_TRAVEL",
                "severity": "HIGH",
                "details": (
                    f"User '{username}' logged in from {ip} only "
                    f"{int(time_diff)}s after login from {last.ip}. "
                    f"Possible credential sharing or compromise."
                ),
            })

    # Store record
    history.append(record)
    if len(history) > MAX_LOGIN_HISTORY_PER_USER:
        _login_history[username] = history[-MAX_LOGIN_HISTORY_PER_USER:]

    # Emit security events for each anomaly
    for a in anomalies:
        _emit_event(
            f"LOGIN_ANOMALY_{a['type']}", a["severity"], ip,
            a["details"], user=username,
        )

    return anomalies


def get_login_history(username: str = None, limit: int = 50) -> list[dict]:
    """Get login history for a user or all users."""
    results = []
    if username:
        for r in reversed(_login_history.get(username, [])[-limit:]):
            results.append({
                "username": r.username, "ip": r.ip,
                "timestamp": datetime.fromtimestamp(r.timestamp, tz=timezone.utc).isoformat(),
            })
    else:
        all_records = []
        for user_records in _login_history.values():
            all_records.extend(user_records)
        all_records.sort(key=lambda r: r.timestamp, reverse=True)
        for r in all_records[:limit]:
            results.append({
                "username": r.username, "ip": r.ip,
                "timestamp": datetime.fromtimestamp(r.timestamp, tz=timezone.utc).isoformat(),
            })
    return results


# ═══════════════════════════════════════════════════════════════════════
# 17. REAL-TIME ALERT QUEUE (for high-severity event polling)
# ═══════════════════════════════════════════════════════════════════════

_alert_queue: list[SecurityEvent] = []
_alert_counter: int = 0
MAX_ALERT_QUEUE = 100


def _maybe_queue_alert(event: SecurityEvent):
    """Queue CRITICAL/HIGH events for real-time polling."""
    global _alert_counter
    if event.severity in ("CRITICAL", "HIGH"):
        _alert_counter += 1
        _alert_queue.append(event)
        if len(_alert_queue) > MAX_ALERT_QUEUE:
            _alert_queue[:] = _alert_queue[-MAX_ALERT_QUEUE:]


def get_recent_alerts(since_id: int = 0) -> tuple[list[dict], int]:
    """Get alerts newer than since_id. Returns (alerts, latest_id)."""
    current_id = _alert_counter
    if since_id >= current_id:
        return [], current_id

    new_count = min(current_id - since_id, len(_alert_queue))
    alerts = _alert_queue[-new_count:]

    return [
        {
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "severity": e.severity,
            "source_ip": e.source_ip,
            "details": e.details,
            "user": e.user,
        }
        for e in alerts
    ], current_id


# ═══════════════════════════════════════════════════════════════════════
# 18. SECURITY SCORE (composite health metric 0-100)
# ═══════════════════════════════════════════════════════════════════════

def compute_security_score() -> dict:
    """Compute a 0-100 security score with breakdown by category."""
    now = time.time()

    # 1. Protection status (25%)
    from ..config import SECURITY_RATE_LIMIT_ENABLED
    protection_score = 100
    if not SECURITY_RATE_LIMIT_ENABLED:
        protection_score -= 30
    try:
        from ..core.encryption import is_encryption_active
        if not is_encryption_active():
            protection_score -= 20
    except Exception:
        protection_score -= 20
    protection_score = max(0, protection_score)

    # 2. Incident score (25%) - penalize for recent critical events
    events_24h = [e for e in _security_events if (now - _iso_to_ts(e.timestamp)) < 86400]
    critical_24h = sum(1 for e in events_24h if e.severity == "CRITICAL")
    high_24h = sum(1 for e in events_24h if e.severity == "HIGH")
    incident_score = max(0, 100 - (critical_24h * 25) - (high_24h * 10))

    # 3. Configuration score (20%)
    config_score = 0
    if PASSWORD_MIN_LENGTH >= 8:
        config_score += 25
    if PASSWORD_REQUIRE_UPPER:
        config_score += 25
    if PASSWORD_REQUIRE_DIGIT:
        config_score += 25
    if BRUTE_FORCE_THRESHOLD <= 5:
        config_score += 25

    # 4. Session hygiene (15%)
    session_count = len(_active_sessions)
    if session_count <= 10:
        session_score = 100
    elif session_count <= 50:
        session_score = 70
    else:
        session_score = 40

    # 5. Threat history (15%)
    blocked_events = [e for e in events_24h if e.blocked]
    if len(events_24h) == 0:
        threat_score = 100
    else:
        event_penalty = min(50, len(events_24h))
        block_ratio = len(blocked_events) / len(events_24h)
        threat_score = max(0, min(100, int(100 - event_penalty + (block_ratio * 30))))

    # Weighted total
    total = int(
        protection_score * 0.25 +
        incident_score * 0.25 +
        config_score * 0.20 +
        session_score * 0.15 +
        threat_score * 0.15
    )
    total = max(0, min(100, total))

    if total >= 90:
        grade = "A"
    elif total >= 75:
        grade = "B"
    elif total >= 60:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": total,
        "grade": grade,
        "breakdown": {
            "protection": {"score": protection_score, "weight": 25},
            "incidents": {"score": incident_score, "weight": 25,
                          "critical_24h": critical_24h, "high_24h": high_24h},
            "configuration": {"score": config_score, "weight": 20},
            "sessions": {"score": session_score, "weight": 15,
                         "active_count": session_count},
            "threats": {"score": threat_score, "weight": 15,
                        "events_24h": len(events_24h), "blocked_24h": len(blocked_events)},
        },
    }
