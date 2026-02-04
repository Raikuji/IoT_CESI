"""
Database backup/restore service
"""
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict

from config import settings

BACKUP_DIR = os.getenv("BACKUP_DIR", "/app/backups")


def ensure_backup_dir() -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return BACKUP_DIR


def list_backups() -> List[Dict]:
    ensure_backup_dir()
    items = []
    for name in os.listdir(BACKUP_DIR):
        if not (name.endswith(".dump") or name.endswith(".sql")):
            continue
        path = os.path.join(BACKUP_DIR, name)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        items.append({
            "name": name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items


def run_backup() -> Dict:
    ensure_backup_dir()
    if not shutil.which("pg_dump"):
        raise RuntimeError("pg_dump introuvable dans le conteneur")

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"backup-{timestamp}.dump"
    filepath = os.path.join(BACKUP_DIR, filename)

    cmd = [
        "pg_dump",
        settings.database_url,
        "-Fc",
        "--no-owner",
        "--no-privileges",
        "-f",
        filepath
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError(result.stderr.strip() or "Échec du backup")

    return {
        "name": filename,
        "path": filepath
    }


def restore_backup(filename: str) -> Dict:
    ensure_backup_dir()
    if not shutil.which("pg_restore"):
        raise RuntimeError("pg_restore introuvable dans le conteneur")

    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.isfile(filepath):
        raise FileNotFoundError("Backup introuvable")

    cmd = [
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
        "-d",
        settings.database_url,
        filepath
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Échec de la restauration")

    return {
        "name": filename
    }


def cleanup_old_backups(retention_days: int) -> int:
    ensure_backup_dir()
    if retention_days <= 0:
        return 0
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = 0
    for item in list_backups():
        try:
            created_at = datetime.fromisoformat(item["created_at"])
        except Exception:
            continue
        if created_at < cutoff:
            try:
                os.remove(os.path.join(BACKUP_DIR, item["name"]))
                deleted += 1
            except Exception:
                pass
    return deleted
