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
    │                       (Ollama Cloud /              │
    │                        Mercury 2 / GX10 lokal)     │
    │                                                     ▼
    └─── Komplex ──────────────────────────────► Claude direkt
                                                          │
                                                          ▼
                                              Konsolidiertes Ergebnis
```

**Claude bleibt immer der Orchestrator.** Es zerlegt Aufgaben, delegiert
abgrenzbare Subtasks und prüft die Ergebnisse.

## Unterstützte Agenten (Stand 2026-06)

Auf drei reale Ziele beschränkt:

| Agent | Rolle | Typ | Kosten | Setup |
|-------|-------|-----|--------|-------|
| **Ollama Cloud** | 🟢 primär | API, OpenAI-kompatibel | Flatrate (pauschal/Monat) | `OLLAMA_API_KEY` in `.env` |
| **Inception Mercury 2** | ⚡ optional | API, OpenAI-kompatibel | sehr günstig | `INCEPTION_API_KEY` in `.env` |
| **GX10 / DGX-Spark** | 🔒 lokal | lokal im Heimnetz | kostenlos | kein Key — `http://gx10-74ac.amhomenet.de:8080/v1` |

Das lokale GX10-Setup ist im Repo `ydmw74/spark-74ac` dokumentiert.

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

# Keys eintragen:
OLLAMA_API_KEY=dein-key-hier      # primär
# INCEPTION_API_KEY=...           # optional (Mercury 2, schnellste Option)
# GX10 lokal braucht keinen Key (Heimnetz-Endpoint)
```

API-Keys bekommst du hier:
- Ollama Cloud (primär): https://ollama.com/settings/keys
- Inception Mercury 2 (optional): https://platform.inceptionlabs.ai
- GX10 / DGX-Spark (lokal): kein Key — Endpoint `http://gx10-74ac.amhomenet.de:8080/v1`

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
| **Einfach** | ✅ Ja | Ollama Cloud `gemma3:4b` → Mercury 2 |
| **Mittel** | ✅ Ja (+ Review) | Ollama Cloud `gemma3:12b`/`gemma4:31b` → GX10 lokal |
| **Sensibel** | ✅ Ja (lokal) | GX10 / DGX-Spark (Heimnetz) |
| **Komplex** | ❌ Nein | Claude direkt |

**Einfach:** Textformatierung, Übersetzung, Template-Befüllung,
Codekommentare/Docstrings, Changelog, Meeting-Protokoll.

**Mittel:** User Stories, Unit-Tests, Code-Dokumentation,
RACI-Matrix, Meeting-Agenden, Risiko-Templates.

**Komplex (immer Claude):** Architekturentscheidungen, Risikoanalysen,
Stakeholder-Kommunikation, Sicherheits- und Compliance-Prüfungen.

## GX10 / DGX-Spark lokal (für sensible Aufgaben, kein API-Key)

Läuft komplett im Heimnetz — OpenAI-kompatibler Endpoint auf Port 8080.
Setup im Repo `ydmw74/spark-74ac`. Port 8080 bedient nur EINEN Dienst:

```bash
# Laufendes Modell prüfen:
curl -s http://gx10-74ac.amhomenet.de:8080/v1/models

# vLLM (Autostart): Modell-ID "/model"  = Qwen3.6-35B-A3B-NVFP4
# llama-server Router (Backup): "GLM-4.7-Flash" / "Qwen3.6-27B-MTP"
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
