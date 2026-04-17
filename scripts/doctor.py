"""
Mentor AI - Doctor
"""
from __future__ import annotations

import argparse
import shutil
import socket
import sys
from pathlib import Path


results: list[tuple[str, str, str]] = []


def ok(title, detail=""):
    results.append(("ok", title, detail))


def warn(title, detail=""):
    results.append(("warn", title, detail))


def err(title, detail=""):
    results.append(("err", title, detail))


def check_python():
    version = sys.version_info
    if version >= (3, 11):
        ok("Python", f"{version.major}.{version.minor}.{version.micro}")
    elif version >= (3, 10):
        warn("Python", f"{version.major}.{version.minor} recomendado 3.11+")
    else:
        err("Python", f"{version.major}.{version.minor} requiere 3.10+")


def check_packages():
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "httpx",
        "chromadb",
        ("fitz", "PyMuPDF"),
        ("docx", "python-docx"),
        ("PIL", "Pillow"),
        ("pytesseract", "pytesseract"),
        ("langchain_ollama", "langchain-ollama"),
    ]
    missing = []
    for item in required:
        module_name, label = item if isinstance(item, tuple) else (item, item)
        try:
            __import__(module_name)
        except ImportError:
            missing.append(label)
    if missing:
        err("Paquetes Python", f"Faltan: {', '.join(missing)}")
    else:
        ok("Paquetes Python", f"{len(required)} OK")


def check_env(fix=False):
    if Path(".env").exists():
        ok(".env", "presente")
    elif fix and Path(".env.example").exists():
        shutil.copy(".env.example", ".env")
        ok(".env", "creado desde .env.example")
    else:
        warn(".env", "No existe")


def check_dirs(fix=False):
    for directory in [Path("uploads"), Path("data"), Path("knowledge_base"), Path("frontend")]:
        if directory.exists():
            ok("Directorio", str(directory))
        elif fix and directory.name != "frontend":
            directory.mkdir(parents=True, exist_ok=True)
            ok("Directorio", f"creado {directory}")
        else:
            warn("Directorio", f"Falta {directory}")


def check_ports():
    for port, label in [(8765, "backend"), (8766, "frontend"), (11434, "ollama"), (8100, "chroma")]:
        sock = socket.socket()
        sock.settimeout(0.3)
        busy = sock.connect_ex(("127.0.0.1", port)) == 0
        sock.close()
        if busy and label in {"backend", "frontend"}:
            warn(f"Puerto {port}", f"{label} ocupado")
        else:
            ok(f"Puerto {port}", "ocupado" if busy else "libre")


def check_tesseract():
    path = shutil.which("tesseract")
    if path:
        ok("Tesseract", path)
    else:
        warn("Tesseract", "No encontrado")


def check_ollama():
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            ok("Ollama", "respondiendo")
        else:
            warn("Ollama", f"status {response.status_code}")
    except Exception as exc:
        warn("Ollama", f"no responde ({type(exc).__name__})")


def check_config():
    try:
        from core.config import settings
        ok(
            "Config",
            f"OCR={'on' if settings.OCR_ENABLED else 'off'} | Supabase={'on' if settings.supabase_enabled else 'degraded'}",
        )
    except Exception as exc:
        err("Config", str(exc))


def check_store():
    try:
        from core.ingestion import get_store
        counts = get_store().count_by_status()
        ok("IngestionStore", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "vacío")
    except Exception as exc:
        err("IngestionStore", str(exc))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="Crea directorios y .env si faltan")
    args = parser.parse_args()

    check_python()
    check_packages()
    check_env(args.fix)
    check_dirs(args.fix)
    check_ports()
    check_tesseract()
    check_ollama()
    check_config()
    check_store()

    errors = 0
    warnings = 0
    oks = 0
    for level, title, detail in results:
        if level == "ok":
            print(f"OK   {title}: {detail}")
            oks += 1
        elif level == "warn":
            print(f"WARN {title}: {detail}")
            warnings += 1
        else:
            print(f"ERR  {title}: {detail}")
            errors += 1

    print(f"\n{oks} OK | {warnings} warnings | {errors} errores")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
