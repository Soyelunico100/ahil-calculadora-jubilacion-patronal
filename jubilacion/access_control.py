from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
HASHES_PATH = PROJECT_DIR / "data" / "access_code_hashes.csv"
USAGE_PATH = PROJECT_DIR / "private" / "access_usage.json"
MAX_REPORTS_PER_CODE = 10
MASTER_ACCESS_HASH = "96c051773aea19ef1d8b167d031b0b3aac6e45678bf4bf9881dc70978cedea68"
MASTER_REPORT_LIMIT = 999999


@dataclass(frozen=True)
class AccessStatus:
    allowed: bool
    code_hash: str
    worker_id: str
    worker_label: str
    reports_used: int
    reports_remaining: int
    message: str
    is_master: bool = False


def normalize_code(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", code or "").upper()


def hash_code(code: str) -> str:
    normalized = normalize_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_secret(code: str) -> str:
    return hashlib.sha256((code or "").strip().encode("utf-8")).hexdigest()


def is_master_code(code: str) -> bool:
    return hash_secret(code) == MASTER_ACCESS_HASH


def worker_key(identificacion: str, trabajador: str) -> str:
    raw = identificacion.strip() or trabajador.strip()
    return re.sub(r"[^A-Za-z0-9]", "", raw).upper()


def worker_label(identificacion: str, trabajador: str) -> str:
    name = trabajador.strip() or "Trabajador sin nombre"
    ident = identificacion.strip()
    return f"{name} ({ident})" if ident else name


def validate_access(code: str, identificacion: str, trabajador: str) -> AccessStatus:
    normalized = normalize_code(code)
    worker_id = worker_key(identificacion, trabajador)
    label = worker_label(identificacion, trabajador)
    code_hash = hash_code(normalized)
    master = is_master_code(code)
    usage = _load_usage()
    record = usage.get(code_hash, {})
    reports_used = int(record.get("reports_used", 0))
    assigned_worker = record.get("worker_id", "")

    if master:
        if not worker_id:
            return _status(False, code_hash, worker_id, label, 0, "Ingrese cedula/identificacion o nombre del trabajador.", True)
        return _status(True, code_hash, worker_id, label, 0, "Clave master valida. Acceso ilimitado.", True)
    if len(normalized) != 8:
        return _status(False, code_hash, worker_id, label, reports_used, "El codigo debe tener 8 caracteres alfanumericos.")
    if not worker_id:
        return _status(False, code_hash, worker_id, label, reports_used, "Ingrese cedula/identificacion o nombre del trabajador.")
    if code_hash not in _load_hashes():
        return _status(False, code_hash, worker_id, label, reports_used, "Codigo no autorizado. Solicite un codigo valido.")
    if assigned_worker and assigned_worker != worker_id:
        assigned_label = record.get("worker_label", "otro trabajador")
        return _status(
            False,
            code_hash,
            worker_id,
            label,
            reports_used,
            f"Este codigo ya fue asignado a {assigned_label}. Para otro trabajador necesita otro codigo.",
        )
    if reports_used >= MAX_REPORTS_PER_CODE:
        return _status(False, code_hash, worker_id, label, reports_used, "Este codigo ya alcanzo el maximo de 10 informes.")

    return _status(True, code_hash, worker_id, label, reports_used, "Codigo valido.")


def register_report_download(code: str, identificacion: str, trabajador: str, report_type: str) -> AccessStatus:
    status = validate_access(code, identificacion, trabajador)
    if not status.allowed:
        return status
    if status.is_master:
        return status

    usage = _load_usage()
    record = _assign_record(usage, status)
    record["reports_used"] = int(record.get("reports_used", 0)) + 1
    record["last_report_type"] = report_type
    record["last_used_at"] = _now()
    _save_usage(usage)
    return validate_access(code, identificacion, trabajador)


def assign_code_to_worker(code: str, identificacion: str, trabajador: str) -> AccessStatus:
    status = validate_access(code, identificacion, trabajador)
    if not status.allowed:
        return status
    if status.is_master:
        return status
    usage = _load_usage()
    record = _assign_record(usage, status)
    record["last_validated_at"] = _now()
    _save_usage(usage)
    return validate_access(code, identificacion, trabajador)


def _status(
    allowed: bool,
    code_hash: str,
    worker_id: str,
    label: str,
    reports_used: int,
    message: str,
    is_master: bool = False,
) -> AccessStatus:
    remaining = MASTER_REPORT_LIMIT if is_master and allowed else max(MAX_REPORTS_PER_CODE - reports_used, 0)
    return AccessStatus(
        allowed=allowed,
        code_hash=code_hash,
        worker_id=worker_id,
        worker_label=label,
        reports_used=reports_used,
        reports_remaining=remaining,
        message=message,
        is_master=is_master,
    )


def _load_hashes() -> set[str]:
    if not HASHES_PATH.exists():
        return set()
    with HASHES_PATH.open(encoding="utf-8", newline="") as handle:
        return {row["code_hash"] for row in csv.DictReader(handle)}


def _load_usage() -> dict[str, dict]:
    if not USAGE_PATH.exists():
        return {}
    try:
        return json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_usage(usage: dict[str, dict]) -> None:
    USAGE_PATH.parent.mkdir(exist_ok=True)
    USAGE_PATH.write_text(json.dumps(usage, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assign_record(usage: dict[str, dict], status: AccessStatus) -> dict:
    record = usage.setdefault(status.code_hash, {})
    record.setdefault("created_at", _now())
    record["worker_id"] = status.worker_id
    record["worker_label"] = status.worker_label
    record.setdefault("reports_used", status.reports_used)
    return record
