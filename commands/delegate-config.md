---
description: Zeige und konfiguriere Delegation-Agenten
allowed-tools: Bash, Read, Write
argument-hint: "[show|enable <agent-id>|disable <agent-id>|setup]"
---

Verwalte die Konfiguration des Agent Delegators.

ARGUMENT: $ARGUMENTS

FALL 1 — Kein Argument oder "show":
Zeige den aktuellen Status aller Agenten:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```

Dann zeige die aktuelle Konfiguration:
```bash
cat ${CLAUDE_PLUGIN_ROOT}/config/agents.json
```

Erkläre dem User welche Agenten aktiviert sind und was noch konfiguriert
werden müsste (fehlende API-Keys, nicht installierte CLIs).

FALL 2 — "setup":
Führe den interaktiven Setup-Check durch:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```

Erkläre dem User für jeden nicht-OK-Punkt, was zu tun ist. Biete an,
die agents.json anzupassen wenn der User einen Agenten aktivieren möchte.

FALL 3 — "enable <agent-id>" oder "disable <agent-id>":
Lese die aktuelle agents.json, ändere `"enabled"` für den angegebenen
Agenten und speichere die Datei zurück.

Agenten-IDs: gpt-4o-mini, gemini-flash, groq-llama, ollama-local, opencode

Nach der Änderung: Bestätige die neue Konfiguration und zeige den
geänderten Eintrag.

FALL 4 — Unbekanntes Argument:
Erkläre die verfügbaren Optionen:
- `/delegate-config` oder `/delegate-config show` — Status aller Agenten
- `/delegate-config setup` — Installations-Check mit Anleitungen
- `/delegate-config enable gpt-4o-mini` — Agenten aktivieren
- `/delegate-config disable gpt-4o-mini` — Agenten deaktivieren
