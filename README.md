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
| `agent-delegator` | Skill | Vollständiger Workflow: Analyse → Routing → Delegation → Konsolidierung |
| `/delegate` | Command | Manuell einen Task delegieren |
| `/delegate-config` | Command | Agenten konfigurieren und Status prüfen |

## Unterstützte Agenten

| Agent | Typ | Kosten | Setup |
|-------|-----|--------|-------|
| **Ollama Cloud** | API, pay-per-use | Günstig | API-Key in `.env` → `OLLAMA_API_KEY=...` |
| **Ollama lokal** | Lokal, kostenlos | Kostenlos | Ollama installieren + Modell laden |
| **GPT-4o-mini** | OpenAI API | ~$0.15/1M | `OPENAI_API_KEY=...` in `.env` |
| **Gemini Flash** | Google API | ~$0.075/1M | `GEMINI_API_KEY=...` in `.env` |
| **Groq (Llama)** | Groq API | ~$0.05/1M | `GROQ_API_KEY=...` in `.env` |
| **opencode CLI** | Lokales CLI | Modell-abhängig | `npm install -g opencode-ai` |

## Setup

### 1. API-Keys einrichten

Kopiere `.env.example` zu `.env` und trage deine Keys ein:

```bash
cp .env.example .env
# .env bearbeiten:
OLLAMA_API_KEY=dein-key-hier
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
# GROQ_API_KEY=...
```

Die Scripts lesen `.env` automatisch — kein manuelles `export` nötig.

### 2. Status prüfen

```bash
python scripts/setup.py
```

### 3. Agenten aktivieren

Bearbeite `config/agents.json` und setze `"enabled": true` für gewünschte Agenten.
Oder via Command:

```bash
/delegate-config enable gpt-4o-mini
/delegate-config enable gemini-flash
```

### 4. Ollama lokal einrichten (optional, kein API-Key nötig)

```bash
# Ollama installieren: https://ollama.ai
ollama pull gemma3:4b        # Schnell, gut für einfache Tasks
ollama pull qwen2.5:7b       # Besser für Code und Dokumente
```

## Installation

Es gibt zwei Wege, den Skill zu installieren:

### Option A — `.skill` Datei (empfohlen)

Lade `agent-delegator.skill` in Cowork. Der Skill wird automatisch
installiert und steht Claude direkt zur Verfügung.

> **Hinweis zur Konfiguration:** Das `.skills`-Verzeichnis in Cowork ist
> schreibgeschützt. API-Keys können dort nicht direkt eingetragen werden.
> Verwende in diesem Fall **Option B** für die Konfiguration.

### Option B — `.zip` Datei (für API-Key-Konfiguration)

Lade `agent-delegator.zip` herunter und entpacke sie in einen Ordner deiner
Wahl (z.B. `~/Documents/agent-delegator/`). Dort hast du vollen Schreibzugriff
und kannst die `.env` Datei mit deinen API-Keys befüllen:

```bash
# Entpacken (Beispiel macOS/Linux):
unzip agent-delegator.zip -d ~/Documents/

# .env anlegen und Keys eintragen:
cd ~/Documents/agent-delegator
cp .env.example .env
# .env bearbeiten und OLLAMA_API_KEY, OPENAI_API_KEY etc. eintragen

# Setup prüfen:
python scripts/setup.py
```

Öffne den Ordner danach in Cowork als Arbeitsordner — Claude findet die
`.env` automatisch über den `$SKILL_DIR` Pfad.

Der Skill deckt den kompletten Ablauf ab:
1. **Klassifizieren** — Complexity-Analyse via `task_classifier.py`
2. **Routen** — Entscheidung: delegieren oder Claude direkt
3. **Ausführen** — Delegation an gewählten Agenten
4. **Konsolidieren** — Qualitätsprüfung und Zusammenführung der Ergebnisse

## Verwendung

### Automatisch (via Skill)

Claude verwendet den `agent-delegator` Skill automatisch wenn Aufgaben
in Subtasks aufgeteilt werden können. Das Routing passiert transparent.

### Manuell (/delegate Command)

```
/delegate Formatiere diese Bullet-Points als Markdown-Tabelle: ...
/delegate Übersetze diese User Story ins Englische: ...
/delegate Schreibe Docstrings für diesen Python-Code: ...
```

### Direkter Skript-Aufruf (für Fortgeschrittene)

**Ollama** (Cloud oder lokal):
```bash
bash scripts/call_ollama.sh --prompt "Deine Aufgabe" --model gemma3:4b
bash scripts/call_ollama.sh --list-models
```

**OpenAI-kompatibel** (GPT-4o-mini, Gemini, Groq, etc.):
```bash
python scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --config config/agents.json \
  --prompt "Deine Aufgabe"
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

**Einfach (Beispiele):** Textformatierung, Übersetzung, Template-Befüllung,
Codekommentare / Docstrings, Changelog strukturieren, Meeting-Protokoll.

**Mittel (Beispiele):** User Stories, Unit-Test-Generierung, Code-Dokumentation,
RACI-Matrix, Meeting-Agenden, Risiko-Templates.

**Komplex (immer Claude):** Architekturentscheidungen, Risikoanalysen,
Stakeholder-Kommunikation, Sicherheits- und Compliance-Prüfungen.

## Konfiguration

Bearbeite `config/agents.json` um Agenten zu aktivieren/deaktivieren
und Modelle/API-Endpunkte anzupassen.

Alle OpenAI-kompatiblen APIs (Mistral, Together, Perplexity, Azure OpenAI, etc.)
können über `type: "openai-compatible"` hinzugefügt werden.

## Skripte

| Skript | Beschreibung |
|--------|-------------|
| `scripts/task_classifier.py` | Task-Komplexität analysieren + Modell empfehlen |
| `scripts/call_openai.py` | OpenAI-kompatible API aufrufen |
| `scripts/call_ollama.sh` | Ollama (Cloud oder lokal) aufrufen |
| `scripts/call_opencode.sh` | opencode CLI aufrufen |
| `scripts/setup.py` | Installation und Status prüfen |
