# Agent Capabilities — Stärken und Grenzen (Stand 2026-06)

Auf drei reale Ziele beschränkt.

## Übersicht

| Agent | Rolle | Kosten | Geschwindigkeit | Stärken | Grenzen |
|-------|-------|--------|----------------|---------|---------|
| **Ollama Cloud** | 🟢 primär | sehr günstig | schnell | Breite Modellauswahl, OpenAI-kompatibel, frei wählbares Modell | Online, Cloud (keine sensiblen Daten) |
| **Inception Mercury 2** | ⚡ optional | sehr günstig | extrem schnell (~1000 tok/s) | Höchster Durchsatz, 128K Kontext | Online, ein Modell (`mercury-2`) |
| **GX10 / DGX-Spark** | 🔒 lokal | kostenlos | ~50–106 tok/s | Datenschutz, läuft im Heimnetz, Tool-Calling + Reasoning | Nur im Heimnetz erreichbar, ein Dienst pro Port |

---

## Ollama Cloud (primär)

**Einsatz**: Standard-Delegationsziel für einfache bis mittlere Tasks.

**Endpoint**: `https://ollama.com/v1` (OpenAI-kompatibel), Key `OLLAMA_API_KEY`.

**Empfohlene Modelle** (echter Cloud-Katalog, Stand 2026-06 — ändert sich, mit `--list-models` prüfen):
- `gemma3:4b`, `ministral-3:3b` — einfach: Formatierung, Übersetzung, Zusammenfassung (Default)
- `gemma3:12b`, `ministral-3:8b` — mittel: Docs, strukturierte Ausgaben, einfacher Code
- `gemma4:31b`, `gpt-oss:20b`, `ministral-3:14b` — stark: anspruchsvollere Tasks
- `qwen3-coder:480b`, `glm-4.7` — Code-/Tool-lastige Tasks
- `nemotron-3-ultra` — starkes Reasoning (550B MoE / 55B aktiv, 1M Kontext, Top-Open-Weight)
- `kimi-k2.6` — **Vision** (Bild + Video, 1T MoE / 32B aktiv, 256K Kontext) — einziges Cloud-Modell mit Multimodalität

> Default bewusst klein/günstig halten. `nemotron-3-ultra`/`kimi-k2.6` nur für anspruchsvolle bzw.
> multimodale Delegation — bei einfachen Tasks sind sie Overkill (langsamer, teurer).

**Verfügbare Modelle prüfen**:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh --list-models
```

**Grenzen**: Cloud — keine datenschutzkritischen Inhalte. Bei mittleren Tasks Ergebnis prüfen.

---

## Inception Mercury 2 (optional, schnellste Option)

**Einsatz**: Reine Speed-Tasks mit hohem Durchsatz.

**Endpoint**: `https://api.inceptionlabs.ai/v1` (OpenAI-kompatibel), Key `INCEPTION_API_KEY`.

**Modell**: `mercury-2` (Diffusion-LLM, ~1000 tok/s, 128K Kontext).

**Parameter**: `temperature` 0.5–1.0 (default 0.75); `reasoning_effort` `instant` (max Speed) → `low`/`medium`/`high` (mehr Tiefe).

**Setup**:
```bash
export INCEPTION_API_KEY=...   # https://platform.inceptionlabs.ai → API Keys
```

**Grenzen**: Online, nur das eine Modell.

---

## GX10 / DGX-Spark (lokal, für sensible Aufgaben)

**Einsatz**: Datenschutzkritische Aufgaben — bleibt komplett im Heimnetz, kein externer API-Call.

**Endpoint**: `http://gx10-74ac.amhomenet.de:8080/v1` (OpenAI-kompatibel), **kein API-Key**. Konfig/Repo: `ydmw74/spark-74ac`.

**Hardware**: ASUS Ascent GX10 (NVIDIA DGX Spark / GB10), 128 GB Unified Memory.

**Wichtig — Port 8080 bedient nur EINEN Dienst gleichzeitig**:
- **vLLM** (Autostart, primär): Modell-ID `/model` = `Qwen3.6-35B-A3B-NVFP4` (MoE 35B/3B, Reasoning + Tool-Calling, ~106 tok/s, 65k ctx)
- **llama-server Router** (Backup): `GLM-4.7-Flash` (Tool-Calling, kein Thinking) · `Qwen3.6-27B-MTP` (Reasoning, ~50 tok/s)

Laufendes Modell prüfen:
```bash
curl -s http://gx10-74ac.amhomenet.de:8080/v1/models
```

**Grenzen**: Nur im Heimnetz erreichbar; bei Kaltstart von vLLM ~3–5 Min Startzeit.

---

## Agenten aktivieren/deaktivieren

Bearbeite `${CLAUDE_PLUGIN_ROOT}/config/agents.json`:
```json
{
  "agents": [
    {
      "id": "ollama-cloud",
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
