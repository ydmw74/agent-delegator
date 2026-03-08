# Agent Capabilities — Stärken und Grenzen

## Übersicht

| Agent | Kosten | Geschwindigkeit | Stärken | Grenzen |
|-------|--------|----------------|---------|---------|
| **Ollama (lokal)** | Kostenlos | Mittel–Schnell | Offline, kein API-Key, Datenschutz | Hardware-abhängig, kleinere Modelle |
| **GPT-4o-mini** | ~$0.15/1M Tokens | Sehr schnell | Breite Fähigkeiten, zuverlässig | Braucht API-Key, Online |
| **Gemini Flash** | ~$0.075/1M Tokens | Sehr schnell | Günstig, langer Kontext | Google-API, Online |
| **Groq (Llama)** | ~$0.05/1M Tokens | Extrem schnell | Günstigste Option | Kleineres Modell |
| **opencode CLI** | Abhängig v. Modell | Mittel | Code-spezialisiert, File-Ops | Nur Code-Tasks |

## Ollama (lokal)

**Einsatz**: Tasks, die keine Cloud-Verbindung brauchen, oder wenn Datenschutz wichtig ist.

**Empfohlene Modelle**:
- `llama3.2` (3.2B) — Sehr schnell, gut für Formatting, Transformation, einfache Texte
- `qwen2.5:7b` (7B) — Besser für Reasoning, Code, Dokumente; ~4GB RAM
- `qwen2.5:14b` (14B) — Sehr gut; ~9GB RAM, langsamer
- `mistral` (7B) — Gut für Sprache und strukturierte Ausgaben
- `phi4` (14B) — Microsofts effizientes Modell, gut für Reasoning
- `deepseek-r1:8b` — Chain-of-Thought Reasoning, gut für mittelkomplexe Analyse

**Setup**:
```bash
# 1. Ollama installieren: https://ollama.ai
# 2. Modell laden
ollama pull llama3.2
# 3. Ollama läuft automatisch als Daemon
```

**Verfügbare Modelle prüfen**:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh --list-models
```

**Grenzen**:
- Qualität abhängig vom lokalen Modell
- Langsamer auf schwacher Hardware
- Keine GPT-4-Klasse bei komplexen Tasks
- Empfehlung: Ergebnisse bei mittelkomplexen Tasks immer prüfen

---

## GPT-4o-mini (OpenAI)

**Einsatz**: Breite Palette von einfachen bis mittleren Tasks. Zuverlässigste Option für delegierte Tasks.

**Stärken**:
- Ausgezeichnet für Textformatierung und -transformation
- Gut für Übersetzungen (auch technische)
- Zuverlässig bei Template-Befüllung
- Gute Code-Kommentierung
- Strukturierte Datenextraktion

**Setup**:
```bash
export OPENAI_API_KEY=sk-...
```
In agents.json: `"enabled": true` bei `gpt-4o-mini`.

**Grenzen**:
- Kein tiefes Code-Reasoning (kein Kontext über mehrere Dateien)
- Halluziniert bei spezifischem Domänenwissen
- Nicht für sicherheitskritische Tasks

---

## Gemini 2.0 Flash (Google)

**Einsatz**: Wenn lange Kontexte nötig sind (bis 1M Tokens) oder als günstigere GPT-4o-mini-Alternative.

**Stärken**:
- Sehr günstiger Preis (~50% günstiger als GPT-4o-mini)
- Langer Kontext (z.B. große Dokumente zusammenfassen)
- Schnell

**Setup**:
```bash
export GEMINI_API_KEY=...
```
In agents.json: `"enabled": true` bei `gemini-flash`.

**API-Base**: `https://generativelanguage.googleapis.com/v1beta/openai`

---

## Groq (Llama 3.1 8B)

**Einsatz**: Wenn maximale Geschwindigkeit und minimale Kosten Priorität haben (einfachste Tasks).

**Stärken**:
- Extrem schnell (oft <1 Sekunde)
- Sehr günstig
- OpenAI-kompatibel

**Setup**:
```bash
export GROQ_API_KEY=...
```
In agents.json: `"enabled": true` bei `groq-llama`.

**Grenzen**: Kleineres 8B-Modell — nur für wirklich einfache Tasks.

---

## opencode CLI

**Einsatz**: Code-spezifische Tasks, die Dateizugriff und mehrere Iterationen brauchen.

**Stärken**:
- Kann direkt mit Dateien arbeiten
- Code-Generierung und Refactoring
- Debugging-Unterstützung

**Setup**:
```bash
npm install -g opencode-ai
# Modell über OPENCODE_DELEGATE_MODEL konfigurieren
export OPENCODE_DELEGATE_MODEL=claude-haiku-4-5-20251001
```

**Aktivieren**: In agents.json: `"enabled": true` bei `opencode`.

**Grenzen**:
- Nur für Code-Tasks sinnvoll
- Braucht separate Model-Credentials

---

## Agenten aktivieren/deaktivieren

Bearbeite `${CLAUDE_PLUGIN_ROOT}/config/agents.json`:
```json
{
  "agents": [
    {
      "id": "gpt-4o-mini",
      "enabled": true,    ← hier ändern
      ...
    }
  ]
}
```

Status prüfen:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```
