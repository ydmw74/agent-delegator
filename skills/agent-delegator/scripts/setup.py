#!/usr/bin/env python3
"""
Agent Delegator — Setup & Konfigurationsprüfung
=================================================
Überprüft die Installation und zeigt den Status aller konfigurierten Agenten.

Usage:
  python setup.py
  python setup.py --fix     (versucht fehlende Pakete zu installieren)
  python setup.py --json    (JSON-Output für programmatische Verwendung)
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request


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
    """Prüft ob Ollama läuft und listet verfügbare Modelle."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        if models:
            detail = f"läuft — Modelle: {', '.join(models[:3])}"
            if len(models) > 3:
                detail += f" (+{len(models)-3} weitere)"
        else:
            detail = "läuft — keine Modelle geladen (ollama pull llama3.2)"
        return {"name": "Ollama", "ok": True, "detail": detail}
    except Exception:
        return {
            "name": "Ollama",
            "ok": False,
            "detail": "nicht erreichbar — starte Ollama oder installiere: https://ollama.ai",
        }


def check_api_key(env_var: str, service: str) -> dict:
    val = os.environ.get(env_var, "")
    ok = len(val) > 10
    return {
        "name": f"{service} ({env_var})",
        "ok": ok,
        "detail": f"gesetzt ({len(val)} Zeichen)" if ok else f"nicht gesetzt — export {env_var}=...",
    }


def check_config() -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(script_dir)
    config_path = os.path.join(plugin_root, "config", "agents.json")
    if not os.path.exists(config_path):
        return {"name": "agents.json", "ok": False, "detail": f"nicht gefunden: {config_path}"}
    with open(config_path) as f:
        config = json.load(f)
    enabled = [a["id"] for a in config.get("agents", []) if a.get("enabled")]
    return {
        "name": "agents.json",
        "ok": True,
        "detail": f"OK — aktivierte Agenten: {enabled if enabled else ['(keine)']}",
    }


def print_check(check: dict, use_emoji: bool = True):
    icon = "✅" if check["ok"] else "❌"
    if not use_emoji:
        icon = "[OK]" if check["ok"] else "[FEHLER]"
    print(f"  {icon} {check['name']}: {check['detail']}")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args

    checks = [
        check_python(),
        check_curl(),
        check_config(),
        ("", None),  # Separator
        check_ollama(),
        check_opencode(),
        ("", None),
        check_api_key("OPENAI_API_KEY", "OpenAI"),
        check_api_key("GEMINI_API_KEY", "Gemini"),
        check_api_key("GROQ_API_KEY", "Groq"),
    ]

    if as_json:
        output = [c for c in checks if isinstance(c, dict)]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print("=" * 55)
    print("  Agent Delegator — Setup-Status")
    print("=" * 55)

    for check in checks:
        if not isinstance(check, dict):
            print()
            continue
        print_check(check)

    print()

    # Gesamtstatus
    all_checks = [c for c in checks if isinstance(c, dict)]
    critical = [c for c in all_checks[:3] if not c["ok"]]  # Python, curl, config
    if critical:
        print("⚠️  Kritische Probleme — bitte beheben:")
        for c in critical:
            print(f"   → {c['name']}: {c['detail']}")
    else:
        enabled_agents = [
            c for c in all_checks[4:]  # Skip python/curl/config/separator
            if c["ok"] and c["name"] not in ("", )
        ]
        if enabled_agents:
            print("✅ Bereit. Aktivierte Delegation-Targets:", len(enabled_agents))
        else:
            print("⚠️  Keine Delegation-Targets aktiv.")
            print("   → Aktiviere Ollama (starte die App) oder setze einen API-Key.")
            print("   → Aktiviere Agenten in config/agents.json (enabled: true)")


if __name__ == "__main__":
    main()
