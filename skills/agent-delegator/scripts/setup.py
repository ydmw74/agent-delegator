#!/usr/bin/env python3
"""
Agent Delegator — Setup & Konfigurationsprüfung
=================================================
Überprüft die Installation und zeigt den Status aller konfigurierten Agenten.

Usage:
  python setup.py               (Status-Übersicht)
  python setup.py --json        (JSON-Output)
  python setup.py --show-keys   (zeigt konfigurierte Keys aus .env)
"""

import json
import os
import shutil
import sys
import urllib.request


# ---------------------------------------------------------------------------
# .env Loader — liest .env aus dem Skill-Root (eine Ebene über scripts/)
# ---------------------------------------------------------------------------

def load_dotenv(skill_root: str) -> dict:
    """Lädt .env aus dem Skill-Root und gibt gefundene Keys zurück."""
    env_path = os.path.join(skill_root, ".env")
    loaded = {}
    if not os.path.exists(env_path):
        return loaded
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
                loaded[key] = value
    return loaded


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python() -> dict:
    return {
        "name": "Python",
        "ok": sys.version_info >= (3, 8),
        "detail": f"Python {sys.version.split()[0]}",
    }


def check_curl() -> dict:
    ok = shutil.which("curl") is not None
    return {"name": "curl", "ok": ok, "detail": "gefunden" if ok else "nicht gefunden"}


def check_opencode() -> dict:
    ok = shutil.which("opencode") is not None
    return {
        "name": "opencode CLI",
        "ok": ok,
        "detail": "gefunden" if ok else "nicht installiert (npm install -g opencode-ai)",
    }


def check_ollama() -> dict:
    """Prüft ob Ollama (lokal) läuft und listet verfügbare Modelle."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        if models:
            detail = f"läuft — Modelle: {', '.join(models[:3])}"
            if len(models) > 3:
                detail += f" (+{len(models)-3} weitere)"
        else:
            detail = "läuft — keine Modelle geladen (ollama pull gemma3:4b)"
        return {"name": "Ollama (lokal)", "ok": True, "detail": detail}
    except Exception:
        return {
            "name": "Ollama (lokal)",
            "ok": False,
            "detail": "nicht erreichbar (optional — https://ollama.ai)",
        }


def check_api_key(env_var: str, service: str) -> dict:
    val = os.environ.get(env_var, "")
    ok = len(val) > 10
    return {
        "name": f"{service}",
        "ok": ok,
        "detail": f"✓ Key gesetzt ({len(val)} Zeichen)" if ok else f"kein Key — {env_var} in .env eintragen",
    }


def check_config(skill_root: str) -> dict:
    config_path = os.path.join(skill_root, "config", "agents.json")
    if not os.path.exists(config_path):
        return {"name": "agents.json", "ok": False, "detail": f"nicht gefunden: {config_path}"}
    with open(config_path) as f:
        config = json.load(f)
    enabled = [a["id"] for a in config.get("agents", []) if a.get("enabled")]
    return {
        "name": "agents.json",
        "ok": True,
        "detail": f"aktivierte Agenten: {', '.join(enabled) if enabled else '(keine)'}",
    }


def check_env_file(skill_root: str) -> dict:
    env_path = os.path.join(skill_root, ".env")
    example_path = os.path.join(skill_root, ".env.example")
    if os.path.exists(env_path):
        return {"name": ".env", "ok": True, "detail": f"vorhanden ({env_path})"}
    elif os.path.exists(example_path):
        return {
            "name": ".env",
            "ok": False,
            "detail": f"fehlt — bitte kopieren: cp .env.example .env",
        }
    return {"name": ".env", "ok": False, "detail": "fehlt (keine .env.example gefunden)"}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_check(check: dict):
    icon = "✅" if check["ok"] else "❌"
    print(f"  {icon} {check['name']}: {check['detail']}")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args

    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(script_dir)

    loaded_keys = load_dotenv(skill_root)

    checks = [
        check_python(),
        check_curl(),
        check_env_file(skill_root),
        check_config(skill_root),
        None,  # Separator
        check_ollama(),
        check_api_key("OLLAMA_API_KEY", "Ollama Cloud"),
        None,
        check_api_key("OPENAI_API_KEY", "OpenAI (GPT-4o-mini)"),
        check_api_key("GEMINI_API_KEY", "Gemini Flash"),
        check_api_key("GROQ_API_KEY", "Groq (Llama)"),
    ]

    if as_json:
        output = [c for c in checks if c]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print("=" * 55)
    print("  Agent Delegator — Setup-Status")
    print(f"  Skill-Verzeichnis: {skill_root}")
    print("=" * 55)

    if loaded_keys:
        print(f"  📄 .env geladen ({len(loaded_keys)} Keys)\n")

    for check in checks:
        if check is None:
            print()
            continue
        print_check(check)

    print()

    # Gesamtstatus
    real_checks = [c for c in checks if c]
    critical = [c for c in real_checks[:4] if not c["ok"]]
    if critical:
        print("⚠️  Bitte beheben:")
        for c in critical:
            print(f"   → {c['name']}: {c['detail']}")
    else:
        active = [c for c in real_checks if c["ok"] and c["name"] not in ("Python", "curl", "agents.json", ".env")]
        if active:
            print(f"✅ Bereit. {len(active)} Delegation-Target(s) aktiv.")
        else:
            print("⚠️  Kein Delegation-Target aktiv.")
            print("   → Starte Ollama lokal, oder trage einen API-Key in .env ein.")
            print(f"   → .env liegt in: {skill_root}")


if __name__ == "__main__":
    main()
