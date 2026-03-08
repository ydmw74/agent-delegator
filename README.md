# Agent Delegator

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
    │                        Gemini/Groq)                 │
    │                                                     ▼
    └─── Komplex ──────────────────────────────► Claude direkt
                                                          │
                                                          ▼
                                              Konsolidiertes Ergebnis
```

**Claude bleibt immer der Orchestrator.** Es zerlegt Aufgaben, delegiert
abgrenzbare Subtasks und prüft die Ergebnisse.

## Unterstützte Agenten

| Agent | Typ | Kosten | Setup |
|-------|-----|--------|-------|
| **Ollama Cloud** | API, pay-per-use | Günstig | `OLLAMA_API_KEY` in `.env` |
| **Ollama lokal** | Lokal, kostenlos | Kostenlos | Ollama installieren + Modell laden |
| **GPT-4o-mini** | OpenAI API | ~$0.15/1M Token | `OPENAI_API_KEY` in `.env` |
| **Gemini Flash** | Google API | ~$0.075/1M Token | `GEMINI_API_KEY` in `.env` |
| **Groq (Llama)** | Groq API | ~$0.05/1M Token | `GROQ_API_KEY` in `.env` |

## Installation

### Schritt 1 — Skill installieren

Lade `agent-delegator.skill` in Cowork. Der Skill steht Claude danach
sofort zur Verfügung.

### Schritt 2 — API-Key hinterlegen

Der Skill sucht `.env` automatisch — du musst die Datei nur irgendwo
in deiner Cowork-Umgebung ablegen. Empfohlener Ort: ein beliebiger
Ordner, den du in Cowork als Arbeitsordner geöffnet hast.

```bash
# .env.example aus der .zip als Vorlage verwenden:
cp .env.example .env

# Keys eintragen (mindestens einen):
OLLAMA_API_KEY=dein-key-hier
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
# GROQ_API_KEY=...
```

API-Keys bekommst du hier:
- Ollama Cloud: https://ollama.com/settings/keys
- OpenAI: https://platform.openai.com/api-keys
- Gemini: https://aistudio.google.com/apikey
- Groq: https://console.groq.com/keys

> **Tipp:** Das `.zip` enthält `.env.example` als Vorlage zum Kopieren.
> Entpacken mit: `unzip agent-delegator.zip`

### Schritt 3 — Fertig

Claude findet den Key automatisch beim nächsten Start. Kein manuelles
Konfigurieren, keine zusätzlichen Schritte.

## Verwendung

### Automatisch

Claude verwendet den Skill automatisch sobald Aufgaben delegierbar sind.
Auslöser: "delegiere das", "spare Tokens", "nutze Ollama", etc.

### Manuell via Command

```
/delegate Formatiere diese Bullet-Points als Markdown-Tabelle: ...
/delegate Übersetze diese User Story ins Englische: ...
/delegate Schreibe Docstrings für diesen Python-Code: ...
```

## Routing-Logik

| Komplexität | Delegation | Empfohlene Agenten |
|-------------|-----------|-------------------|
| **Einfach** | ✅ Ja | Ollama gemma3:4b → Groq → GPT-4o-mini |
| **Mittel** | ✅ Ja (+ Review) | Ollama gemma3:12b → GPT-4o-mini → Gemini |
| **Komplex** | ❌ Nein | Claude direkt |

**Einfach:** Textformatierung, Übersetzung, Template-Befüllung,
Codekommentare/Docstrings, Changelog, Meeting-Protokoll.

**Mittel:** User Stories, Unit-Tests, Code-Dokumentation,
RACI-Matrix, Meeting-Agenden, Risiko-Templates.

**Komplex (immer Claude):** Architekturentscheidungen, Risikoanalysen,
Stakeholder-Kommunikation, Sicherheits- und Compliance-Prüfungen.

## Ollama lokal einrichten (optional, kein API-Key nötig)

```bash
# Ollama installieren: https://ollama.ai
ollama pull gemma3:4b        # Schnell, gut für einfache Tasks
ollama pull gemma3:12b       # Besser für Code und Dokumentation
```

## Erweiterte Nutzung (optional)

Das `.zip` enthält Hilfsskripte für direkten Aufruf:

| Skript | Beschreibung |
|--------|-------------|
| `scripts/call_ollama.sh` | Ollama Cloud oder lokal direkt aufrufen |
| `scripts/call_openai.py` | OpenAI-kompatible APIs aufrufen |
| `scripts/task_classifier.py` | Task-Komplexität analysieren |
| `scripts/setup.py` | Konfigurationsstatus prüfen |

```bash
# Beispiele:
bash scripts/call_ollama.sh --prompt "Deine Aufgabe" --model gemma3:4b
bash scripts/call_ollama.sh --list-models
python scripts/task_classifier.py --task "Ist dieser Task delegierbar?" --pretty
```

Alle OpenAI-kompatiblen APIs (Mistral, Together, Azure OpenAI, etc.)
können über `config/agents.json` mit `type: "openai-compatible"` hinzugefügt werden.
