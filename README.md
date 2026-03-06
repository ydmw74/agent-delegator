# Agent Delegator Plugin

Delegiert einfache und mittelkomplexe Subtasks an günstigere Agenten —
spart Claude-Token, ohne Qualitätsverlust.

## Konzept

```
User-Aufgabe
    │
    ▼
  Claude (Orchestrator)
    │
    ├─── Einfach/Mittel ──► Günstigerer Agent ──► Ergebnis zurück
    │                       (Ollama/GPT-mini/             │
    │                        Gemini/opencode)             │
    │                                                     ▼
    └─── Komplex ──────────────────────────────► Claude direkt
                                                          │
                                                          ▼
                                              Konsolidiertes Ergebnis
```

**Claude bleibt immer der Orchestrator.** Es zerlegt Aufgaben, delegiert
abgrenzbare Subtasks und prüft die Ergebnisse.

## Komponenten

| Komponente | Typ | Zweck |
|-----------|-----|-------|
| `task-router` | Skill | Komplexitätsbewertung und Routing-Entscheidung |
| `result-consolidator` | Skill | Prüfung und Zusammenführung der Ergebnisse |
| `/delegate` | Command | Manuell einen Task delegieren |
| `/delegate-config` | Command | Agenten konfigurieren und Status prüfen |

## Unterstützte Agenten

| Agent | Typ | Kosten | Setup |
|-------|-----|--------|-------|
| **Ollama** | Lokal, kostenlos | Kostenlos | Ollama installieren + `ollama pull llama3.2` |
| **GPT-4o-mini** | OpenAI API | ~$0.15/1M | `export OPENAI_API_KEY=...` |
| **Gemini Flash** | Google API | ~$0.075/1M | `export GEMINI_API_KEY=...` |
| **Groq (Llama)** | Groq API | ~$0.05/1M | `export GROQ_API_KEY=...` |
| **opencode CLI** | Lokales CLI | Modell-abhängig | `npm install -g opencode-ai` |

## Setup

### 1. Status prüfen
```bash
python scripts/setup.py
```

### 2. Ollama einrichten (empfohlen, kein API-Key nötig)
```bash
# Ollama installieren: https://ollama.ai
ollama pull llama3.2          # Schnell, gut für einfache Tasks
ollama pull qwen2.5:7b        # Besser für Code und Dokumente
```

### 3. Cloud-Agenten einrichten (optional)
```bash
# OpenAI
export OPENAI_API_KEY=sk-...
# In config/agents.json: "enabled": true bei gpt-4o-mini

# Gemini (günstiger)
export GEMINI_API_KEY=...
# In config/agents.json: "enabled": true bei gemini-flash
```

### 4. Agenten aktivieren
```bash
# Via Command:
/delegate-config enable gpt-4o-mini
/delegate-config enable gemini-flash
/delegate-config disable ollama-local
```

Oder direkt in `config/agents.json` editieren.

## Verwendung

### Automatisch (via Skills)
Claude verwendet den `task-router` Skill automatisch wenn Aufgaben
in Subtasks aufgeteilt werden können. Das Routing passiert transparent.

### Manuell (/delegate Command)
```
/delegate Formatiere diese Bullet-Points als Markdown-Tabelle: ...
/delegate Übersetze diese User Story ins Englische: ...
/delegate Schreibe Docstrings für diesen Python-Code: ...
```

### Direkter Skript-Aufruf (für Fortgeschrittene)

**Ollama**:
```bash
bash scripts/call_ollama.sh --prompt "Deine Aufgabe hier" --model llama3.2
bash scripts/call_ollama.sh --list-models
```

**OpenAI-kompatibel**:
```bash
python scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --config config/agents.json \
  --prompt "Deine Aufgabe hier"
```

**opencode**:
```bash
bash scripts/call_opencode.sh --prompt "Deine Code-Aufgabe"
```

**Task-Klassifizierung**:
```bash
python scripts/task_classifier.py --task "Ist dieser Task delegierbar?" --pretty
```

## Routing-Logik

| Komplexität | Delegation | Empfohlene Agenten |
|-------------|-----------|-------------------|
| **Einfach** | ✅ Ja | Ollama → Groq → GPT-4o-mini |
| **Mittel** | ✅ Ja (+ Review) | GPT-4o-mini → Gemini → opencode |
| **Komplex** | ❌ Nein | Claude direkt |

### Als einfach klassifiziert (Beispiele)
- Textformatierung, Markdown-Konvertierung
- Übersetzungen
- Template-Befüllung
- Changelog/Meeting-Protokoll strukturieren
- Regex und Datenextraktion

### Als mittel klassifiziert (Beispiele)
- User Stories und Akzeptanzkriterien
- Unit-Test-Generierung
- Code-Dokumentation
- RACI-Matrix und Meeting-Agenden

### Immer Claude direkt
- Architekturentscheidungen
- Risikoanalysen und Strategien
- Sicherheits- und Compliance-Prüfungen
- Stakeholder-Kommunikation auf Führungsebene

## Konfiguration

Bearbeite `config/agents.json` um Agenten zu aktivieren/deaktivieren
und Modelle/API-Endpunkte anzupassen.

Alle OpenAI-kompatiblen APIs (Mistral, Together, Perplexity, Azure OpenAI, etc.)
können über `type: "openai-compatible"` hinzugefügt werden.

## Skripte

| Skript | Beschreibung |
|--------|-------------|
| `scripts/call_openai.py` | OpenAI-kompatible API aufrufen |
| `scripts/call_ollama.sh` | Ollama (lokal) aufrufen |
| `scripts/call_opencode.sh` | opencode CLI aufrufen |
| `scripts/task_classifier.py` | Task-Komplexität analysieren |
| `scripts/setup.py` | Installation und Status prüfen |
