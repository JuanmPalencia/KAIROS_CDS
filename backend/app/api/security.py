"""
KAIROS CDS — API de ciberseguridad.

Endpoints para: dashboard de seguridad, sesiones activas, IPs bloqueadas,
eventos de seguridad, CSRF tokens y status de protecciones.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from ..auth.dependencies import get_current_user, require_role
from ..storage.models_sql import User
from ..core.cybersecurity import (
    get_security_events,
    get_security_stats,
    get_active_sessions,
    get_blocked_ips,
    block_ip,
    unblock_ip,
    generate_csrf_token,
    scan_input,
    validate_password,
    _brute_force,
    _rate_limits,
    _security_events,
    RATE_LIMITS,
    BRUTE_FORCE_THRESHOLD,
    BRUTE_FORCE_LOCKOUT,
    BRUTE_FORCE_WINDOW,
    PASSWORD_MIN_LENGTH,
)

import re, math

router = APIRouter(prefix="/api/security", tags=["security"])


# ── Pydantic models for request bodies ─────────────────────────────

class ScanInputBody(BaseModel):
    value: str

class CheckPasswordBody(BaseModel):
    password: str

class BlockIpBody(BaseModel):
    ip: str
    reason: str = "Manual block from dashboard"


# ── Dashboard Overview ──────────────────────────────────────────────

@router.get("/dashboard")
async def security_dashboard(
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Panel principal de ciberseguridad — solo ADMIN."""
    stats = get_security_stats()
    return {
        "status": "protected",
        "stats": stats,
        "protections": {
            "security_headers": True,
            "rate_limiting": True,
            "brute_force_detection": True,
            "input_scanning": True,
            "csrf_protection": True,
            "session_management": True,
            "ip_blocking": True,
            "password_policy": True,
            "input_sanitization": True,
            "sql_injection_scan": True,
            "xss_scan": True,
            "path_traversal_scan": True,
            "jwt_encryption": "HS256",
            "password_hashing": "bcrypt",
            "audit_blockchain": True,
        },
        "config": {
            "rate_limits": {k: {"max": v[0], "window_s": v[1]} for k, v in RATE_LIMITS.items()},
            "brute_force": {
                "threshold": BRUTE_FORCE_THRESHOLD,
                "window_s": BRUTE_FORCE_WINDOW,
                "lockout_s": BRUTE_FORCE_LOCKOUT,
            },
            "password_policy": {
                "min_length": PASSWORD_MIN_LENGTH,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digit": True,
            },
        },
    }


# ── Security Events ────────────────────────────────────────────────

@router.get("/events")
async def list_security_events(
    limit: int = Query(100, ge=1, le=500),
    severity: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL|INFO)$"),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Lista de eventos de seguridad recientes."""
    events = get_security_events(limit=limit, severity=severity)
    return {"events": events, "total": len(events)}


# ── Active Sessions ─────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Sesiones JWT activas."""
    return {"sessions": get_active_sessions()}


# ── Blocked IPs ─────────────────────────────────────────────────────

@router.get("/blocked-ips")
async def list_blocked_ips(
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """IPs bloqueadas manualmente."""
    return {"blocked_ips": get_blocked_ips()}


@router.post("/block-ip")
async def block_ip_endpoint(
    body: BlockIpBody,
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Bloquear una IP manualmente."""
    block_ip(body.ip, reason=f"Manual por {current_user.username}: {body.reason}")
    return {"ok": True, "blocked": body.ip}


@router.delete("/block-ip/{ip:path}")
async def unblock_ip_endpoint(
    ip: str,
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Desbloquear una IP."""
    unblock_ip(ip)
    return {"ok": True, "unblocked": ip}


# ── CSRF Token ──────────────────────────────────────────────────────

@router.get("/csrf-token")
async def get_csrf(current_user: User = Depends(get_current_user)):
    """Obtener un CSRF token de un solo uso."""
    return {"csrf_token": generate_csrf_token()}


# ── Threat Scan (manual) ───────────────────────────────────────────

@router.post("/scan-input")
async def scan_input_endpoint(
    body: ScanInputBody,
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """Escanear un texto manualmente para detectar amenazas."""
    text = body.value
    threat = scan_input(text)

    threats = []
    if threat:
        threats.append({"type": threat, "detail": f"Patrón {threat} detectado"})

    return {
        "threats_found": len(threats) > 0,
        "threats": threats,
        "clean": threat is None,
        "threat_type": threat,
        "text_length": len(text),
    }


# ── Password strength check ────────────────────────────────────────

@router.post("/check-password")
async def check_password_strength(
    body: CheckPasswordBody,
    current_user: User = Depends(get_current_user),
):
    """Verificar fortaleza de una contraseña (sin almacenarla)."""
    password = body.password
    ok, msg = validate_password(password)

    errors = []
    if not ok:
        errors.append(msg)

    # Additional checks for comprehensive error list
    if len(password) < PASSWORD_MIN_LENGTH:
        if f"Mínimo {PASSWORD_MIN_LENGTH}" not in " ".join(errors):
            errors.append(f"Mínimo {PASSWORD_MIN_LENGTH} caracteres")
    if not re.search(r"[A-Z]", password) and "mayúscula" not in " ".join(errors):
        errors.append("Debe incluir al menos una mayúscula")
    if not re.search(r"[a-z]", password) and "minúscula" not in " ".join(errors):
        errors.append("Debe incluir al menos una minúscula")
    if not re.search(r"\d", password) and "número" not in " ".join(errors):
        errors.append("Debe incluir al menos un número")

    # Calcular entropy bits
    charset = 0
    if re.search(r"[a-z]", password): charset += 26
    if re.search(r"[A-Z]", password): charset += 26
    if re.search(r"\d", password):    charset += 10
    if re.search(r"[^a-zA-Z\d]", password): charset += 32
    entropy = len(password) * math.log2(max(charset, 1)) if charset else 0

    level = "débil"
    if entropy >= 60: level = "fuerte"
    elif entropy >= 40: level = "media"

    return {
        "valid": ok,
        "errors": errors,
        "entropy_bits": round(entropy, 1),
        "strength": level,
    }
