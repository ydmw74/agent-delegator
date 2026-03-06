---
description: Delegiere einen Task an einen günstigeren Agenten
allowed-tools: Bash, Read, Write
argument-hint: "<task-beschreibung> [--agent gpt-4o-mini|ollama|opencode]"
---

Delegiere den folgenden Task an den günstigsten geeigneten Agenten:

TASK: $ARGUMENTS

SCHRITT 1 — Analyse:
Führe den Task-Classifier aus um die Komplexität zu bestimmen:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/task_classifier.py \
  --task "$ARGUMENTS" \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --pretty
```

Lese das JSON-Ergebnis. Falls `delegate: false`, teile dem User mit, warum
der Task zu komplex für Delegation ist und bearbeite ihn direkt.

SCHRITT 2 — Delegation:
Falls `delegate: true`, wähle den ersten empfohlenen aktivierten Agenten und führe die Delegation durch.

Für `ollama` (lokal):
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh \
  --prompt "TASK HIER" \
  --output-file /tmp/delegate_result_$$.txt \
  --verbose
```

Für `gpt-4o-mini` oder andere OpenAI-kompatible Agenten:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id AGENT-ID \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --prompt "TASK HIER" \
  --output-file /tmp/delegate_result_$$.txt \
  --verbose
```

Für `opencode`:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_opencode.sh \
  --prompt "TASK HIER" \
  --output-file /tmp/delegate_result_$$.txt \
  --verbose
```

SCHRITT 3 — Prüfung und Ausgabe:
Lese das Ergebnis:
```bash
cat /tmp/delegate_result_$$.txt
```

Prüfe das Ergebnis auf Qualität (Vollständigkeit, Korrektheit, Halluzinationen).
Korrigiere kleinere Fehler. Bei großen Problemen bearbeite den Task direkt.

Präsentiere das finale Ergebnis und erwähne kurz, welcher Agent verwendet wurde.
