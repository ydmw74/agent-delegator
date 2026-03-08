#!/usr/bin/env python3
"""
Agent Delegator — Task Classifier
===================================
Analysiert einen Task-Text und schlägt vor, ob und wohin dieser delegiert
werden soll. Gibt eine strukturierte JSON-Empfehlung zurück.

Verwendung durch Claude:
  python task_classifier.py --task "Formatiere diese Tabelle als Markdown"
  python task_classifier.py --task "..." --config /path/to/agents.json

Output (JSON):
  {
    "complexity": "simple" | "medium" | "complex",
    "confidence": 0.0 - 1.0,
    "delegate": true | false,
    "recommended_agents": ["ollama-cloud", "gpt-4o-mini"],
    "recommended_model": "llama3.2",
    "model_reasoning": "Schnell und ausreichend für Textformatierung",
    "model_alternatives": ["qwen2.5:3b", "mistral"],
    "reasoning": "...",
    "task_categories": ["text-transformation", "formatting"],
    "warnings": []
  }

Modell-Empfehlungen gelten primär für Ollama (lokal und Cloud), da dort
das Modell frei wählbar ist. Bei APIs wie GPT-4o-mini ist das Modell
bereits in agents.json festgelegt.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional


# ── Klassifizierungs-Regeln ─────────────────────────────────────────────────

# Keywords, die auf EINFACHE Tasks hinweisen (sicher delegierbar)
# Hinweis: Kein trailing \b bei deutschen Verben, da Konjugation (formatiere, übersetze, etc.)
# und Pluralformen (Docstrings, Tabellen) sonst nicht matchen.
SIMPLE_INDICATORS = [
    # Textformatierung
    r"\bformatier\w*|\bformat\b|\bumformat\w*|\blayout\b|\bstrukturier\w*",
    r"\bmarkdown\b|\btabell\w+|\bliste\b|\baufzählung\b|\bbullet\b",
    r"\bübersetze?\w*|\btranslat\w+|\btranslation\b",
    r"\bzusammenfass\w*|\bsummariz\w+|\bsummary\b|\bkurzfassung\b",
    r"\bextrahier\w*|\bextract\w*|\bparse\w*|\bparsen\b",
    r"\bkonvertier\w*|\bconvert\w*|\bumwandl\w*",
    # Templates und Boilerplate
    r"\bvorlage\b|\btemplate\b|\bmuster\b|\bboilerplate\b",
    r"\bausfüll\w*|\bfill.?in\b|\bplatzhalter\b|\bplaceholder\b",
    # Kleine Code-Tasks (Kommentare, Docstrings)
    r"\bkommentar\w*|\bcomment\w*|\bdocstrings?\b|\bdokumentation für\b",
    r"\brename\b|\bumbenennen\b|\bvariable.?name\b",
    r"\bregex\b|\bregular.?expression\b",
    # Einfache Datentransformation
    r"\bdatum\b|\bdate.?format\b|\bzeitstempel\b|\btimestamp\b",
    r"\bsortier\w*|\bsort\b|\balphabetisch\b|\bnumerisch\b",
    r"\bzähl\w*|\bcount\b|\banzahl\b",
    # PM-spezifisch (einfach)
    r"\bstatus.?update\b|\bstatusbericht\b|\bfortschritt\b",
    r"\bprotokoll.?formatier\w*|\bmeeting.?notes.?format\b",
    r"\bchangelog\b|\bchange.?log\b",
]

# Keywords, die auf MITTLERE Tasks hinweisen (delegierbar mit gutem Modell)
MEDIUM_INDICATORS = [
    # Code-Generierung
    r"\bunit.?tests?\b|\btestfall\b|\btest.?generier\w*",
    r"\brefactor\w*|\brefaktorier\w*|\bumstrukturier\w*",
    r"\bcode.?review\b|\breview.?code\b",
    r"\bimplementier\w+.{0,40}(einfach|simple|basic|klein)\b",
    # Dokumentation
    r"\breadme\b|\bapi.?dok\w*|\btechnische.?dok\w*",
    r"\buser.?stor\w+|\bakzeptanzkriterien\b|\bacceptance.?criteria\b",
    # PM-spezifisch (mittel)
    r"\brisikobewertung\b|\brisk.?assessment\b",
    r"\bprojektplan\b|\bproject.?plan\b",
    r"\bstakeholder.?liste\b|\braci\b",
    r"\bmeeting.?agenda\b|\bbesprechungsagenda\b",
]

# Keywords, die auf KOMPLEXE Tasks hinweisen (Claude direkt)
# Hinweis: Viele ohne trailing \b wegen deutschen Komposita (Architekturstrategie, etc.)
COMPLEX_INDICATORS = [
    # Architektur und Design
    r"\barchitektur|\barchitecture\b|\bsystem.?design\b|\btechnologie.?entscheidung\b",
    r"\bkonzept\w*|\bconcept\b|\bstrategi\w+|\bstrategy\b",
    r"\bbewert\w+.{0,40}(ansatz|approach|option)\b|\bevaluat\w+.{0,40}(option|approach)\b",
    # Sicherheit und Kritisches
    r"\bsicherheit\w*|\bsecurity\b|\bauthentifizier\w*|\bauthentication\b",
    r"\bcompliance\b|\bdatenschutz\w*|\bgdpr\b|\bdsgvo\b",
    # Multi-Step Reasoning
    r"\banalysier\w*.{0,40}(komplex|complex|umfassend)\b",
    r"\bursache\b|\broot.?cause\b|\bdebugging\b",
    # Kreativ und Strategisch
    r"\broadmap\b|\bvision\b|\bmission\b",
    r"\bstakeholder.?kommunikation\b|\bexecutive.?brief\b|\bmanagement.?summary\b",
    # PM-spezifisch (komplex)
    r"\brisikomanagement\b|\brisk.?mitigation\b|\beskalation\b",
    r"\bressourcen.?plan\w*|\bchange.?management\b|\borganisationsänderung\b",
]

# Warnsignale — bei diesen immer Claude
HARD_COMPLEX = [
    r"\b(passwort|password|credential|geheimnis|secret|token|api.?key)\b",
    r"\b(sicherheitslücke|vulnerability|exploit|schwachstelle)\b",
    r"\b(persönliche.?daten|personenbezogen|pii|dsgvo.?konform)\b",
    r"\b(rechts|legal|juristisch|haftung|liability)\b",
    r"\b(finanziell|financial|budget.?genehmig|budget.?freigabe)\b",
]

# ── Kategorie-Spezifizierung ────────────────────────────────────────────────

# Feinere Kategorie-Erkennung für Modell-Auswahl
CATEGORY_PATTERNS = {
    "translation": [r"\bübersetze?\w*|\btranslat\w+|\bins (englische|deutsche|französische)\b"],
    "formatting": [r"\bformatier\w*|\bformat\b|\bmarkdown\b|\btabell\w+|\bliste\b|\blayout\b"],
    "summarization": [r"\bzusammenfass\w*|\bsummariz\w+|\bsummary\b|\bkurzfassung\b"],
    "code": [r"\bcode\b|\bfunktion\b|\bklasse\b|\bmethod\b|\bfunction\b|\bskript\b|\bscript\b|\bpython\b|\bjavascript\b|\bjava\b"],
    "documentation": [r"\bdocstrings?\b|\bkommentar\w*|\bcomment\w*|\breadme\b|\bapi.?dok\w*|\bdokumentation\b"],
    "test-generation": [r"\bunit.?tests?\b|\btestfall\b|\btest.?generier\w*|\btest.?schreib\w*"],
    "data-extraction": [r"\bextrahier\w*|\bextract\w*|\bparse\w*|\bregex\b|\bdaten.?aus\b"],
    "template-filling": [r"\bvorlage\b|\btemplate\b|\bausfüll\w*|\bfill.?in\b|\bplatzhalter\b"],
    "user-stories": [r"\buser.?stor\w+|\bakzeptanzkriterien\b|\bacceptance.?criteria\b"],
    "meeting-docs": [r"\bprotokoll\b|\bmeeting.?notes\b|\bagenda\b|\bbesprechung\b"],
    "risk-matrix": [r"\brisiko\b|\brisk\b|\bmatrix\b"],
}


# ── Modell-Empfehlungen ──────────────────────────────────────────────────────
#
# Empfehlungen gelten für Ollama (lokal + Cloud), wo das Modell frei wählbar ist.
# Für APIs wie gpt-4o-mini ist das Modell in agents.json fixiert.
#
# Modell-Charakteristika (Orientierungswerte):
#   llama3.2      — 3B, sehr schnell, gut für Textformatierung/Übersetzung
#   qwen2.5:3b    — 3B, gut für einfache Code-Snippets
#   mistral       — 7B, ausgewogenes Allround-Modell
#   qwen2.5:7b    — 7B, stark für Code und Dokumentation
#   qwen2.5:14b   — 14B, für komplexere Code-Aufgaben

MODEL_RECOMMENDATIONS = {
    # EINFACHE Tasks ────────────────────────────────────────────────────────
    # Ollama Cloud verfügbare Modelle (Stand 2026-03):
    #   small : gemma3:4b, ministral-3:3b
    #   medium: gemma3:12b, ministral-3:8b
    #   large : gemma3:27b, ministral-3:14b, gpt-oss:20b
    "simple": {
        "translation": {
            "model": "gemma3:4b",
            "reasoning": "Gemma 3 4B ist für Übersetzungen schnell und ausreichend akkurat.",
            "alternatives": ["ministral-3:3b", "gemma3:12b"],
        },
        "formatting": {
            "model": "gemma3:4b",
            "reasoning": "Für reine Textformatierung genügt gemma3:4b vollständig.",
            "alternatives": ["ministral-3:3b", "gemma3:12b"],
        },
        "summarization": {
            "model": "gemma3:4b",
            "reasoning": "Einfache Zusammenfassungen: gemma3:4b schnell und kostengünstig.",
            "alternatives": ["ministral-3:3b", "gemma3:12b"],
        },
        "data-extraction": {
            "model": "gemma3:4b",
            "reasoning": "Regex und strukturierte Extraktion: gemma3:4b folgt Anweisungen zuverlässig.",
            "alternatives": ["ministral-3:3b"],
        },
        "template-filling": {
            "model": "gemma3:4b",
            "reasoning": "Template-Befüllung ist einfache Textverarbeitung — gemma3:4b ideal.",
            "alternatives": ["ministral-3:3b"],
        },
        "meeting-docs": {
            "model": "gemma3:4b",
            "reasoning": "Protokoll-Formatierung: gemma3:4b strukturiert Output zuverlässig.",
            "alternatives": ["ministral-3:8b"],
        },
        # Code-nahe einfache Tasks
        "documentation": {
            "model": "ministral-3:8b",
            "reasoning": "Docstrings und Kommentare: ministral-3:8b hat gutes Code-Verständnis.",
            "alternatives": ["gemma3:12b", "gemma3:4b"],
        },
        "code": {
            "model": "ministral-3:8b",
            "reasoning": "Einfache Code-Tasks: ministral-3:8b besser für Code als die 3B/4B Modelle.",
            "alternatives": ["gemma3:12b", "ministral-3:14b"],
        },
        # Default für einfache Tasks ohne spezifische Kategorie
        "default": {
            "model": "gemma3:4b",
            "reasoning": "Standard für einfache Aufgaben: schnell, kostengünstig, ausreichend.",
            "alternatives": ["ministral-3:3b", "gemma3:12b"],
        },
    },

    # MITTLERE Tasks ────────────────────────────────────────────────────────
    "medium": {
        "test-generation": {
            "model": "ministral-3:8b",
            "reasoning": "Unit-Test-Generierung: ministral-3:8b stark bei Code-Aufgaben.",
            "alternatives": ["gemma3:12b", "ministral-3:14b"],
        },
        "code": {
            "model": "ministral-3:14b",
            "reasoning": "Mittlere Code-Aufgaben (Refactoring, Review): ministral-3:14b für bessere Qualität.",
            "alternatives": ["gemma3:27b", "ministral-3:8b"],
        },
        "documentation": {
            "model": "gemma3:12b",
            "reasoning": "Technische Dokumentation (README, API-Docs): gemma3:12b ausgewogen.",
            "alternatives": ["ministral-3:8b", "ministral-3:14b"],
        },
        "user-stories": {
            "model": "ministral-3:8b",
            "reasoning": "User Stories und Akzeptanzkriterien: Ministral liefert strukturierten Output.",
            "alternatives": ["gemma3:12b", "gemma3:4b"],
        },
        "meeting-docs": {
            "model": "ministral-3:8b",
            "reasoning": "Meeting-Agenden und RACI: Ministral gut für strukturierte Dokumente.",
            "alternatives": ["gemma3:12b"],
        },
        "risk-matrix": {
            "model": "gemma3:12b",
            "reasoning": "Risikomatrizen erfordern strukturiertes Denken — gemma3:12b geeignet.",
            "alternatives": ["ministral-3:8b", "ministral-3:14b"],
        },
        # Default für mittlere Tasks
        "default": {
            "model": "gemma3:12b",
            "reasoning": "Mittlere Aufgaben: gemma3:12b bietet gute Balance aus Qualität und Geschwindigkeit.",
            "alternatives": ["ministral-3:8b", "ministral-3:14b"],
        },
    },
}


def get_fine_categories(text: str) -> list:
    """Erkenne feinere Aufgaben-Kategorien für die Modell-Auswahl."""
    text_lower = text.lower()
    found = []
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(category)
                break
    return found


def recommend_model(complexity: str, fine_categories: list) -> dict:
    """Empfehle das optimale Ollama-Modell basierend auf Komplexität und Kategorien."""
    if complexity == "complex":
        return {
            "model": None,
            "reasoning": "Komplexe Aufgabe — Claude direkt empfohlen, kein Delegate-Modell.",
            "alternatives": [],
        }

    level_recs = MODEL_RECOMMENDATIONS.get(complexity, MODEL_RECOMMENDATIONS["simple"])

    # Suche nach bester passender Kategorie (Priorität: spezifischste zuerst)
    priority_order = [
        "code", "test-generation", "documentation",  # Code-nah zuerst
        "user-stories", "risk-matrix", "meeting-docs",  # PM-spezifisch
        "translation", "summarization", "data-extraction",  # Textverarbeitung
        "formatting", "template-filling",  # Formatierung
    ]

    for prio_cat in priority_order:
        if prio_cat in fine_categories and prio_cat in level_recs:
            rec = level_recs[prio_cat].copy()
            rec["matched_category"] = prio_cat
            return rec

    # Fallback: Default für dieses Komplexitätslevel
    rec = level_recs["default"].copy()
    rec["matched_category"] = "default"
    return rec


@dataclass
class ClassificationResult:
    complexity: str = "complex"
    confidence: float = 0.5
    delegate: bool = False
    recommended_agents: list = field(default_factory=list)
    recommended_model: Optional[str] = None
    model_reasoning: str = ""
    model_alternatives: list = field(default_factory=list)
    reasoning: str = ""
    task_categories: list = field(default_factory=list)
    fine_categories: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def score_text(text: str, patterns: list) -> tuple[int, list]:
    """Return (match_count, matched_categories)."""
    text_lower = text.lower()
    matches = []
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matches.append(pattern)
    return len(matches), matches


def estimate_complexity(text: str) -> tuple[str, float, list]:
    """Returns (complexity, confidence, categories)."""
    # Hard checks first
    hard_score, _ = score_text(text, HARD_COMPLEX)
    if hard_score > 0:
        return "complex", 0.95, ["security-or-legal-concern"]

    simple_score, simple_matches = score_text(text, SIMPLE_INDICATORS)
    medium_score, medium_matches = score_text(text, MEDIUM_INDICATORS)
    complex_score, complex_matches = score_text(text, COMPLEX_INDICATORS)

    # Length heuristic — longer, more complex prompts tend to be complex tasks
    word_count = len(text.split())
    length_penalty = 0
    if word_count > 200:
        length_penalty = 1
    if word_count > 500:
        length_penalty = 2

    # Scoring
    complex_score += length_penalty

    categories = []
    if simple_matches:
        categories.append("text-transformation")
    if medium_matches:
        categories.append("code-or-documentation")
    if complex_matches:
        categories.append("reasoning-or-strategy")

    total = simple_score + medium_score + complex_score + 0.01
    simple_ratio = simple_score / total
    medium_ratio = medium_score / total
    complex_ratio = complex_score / total

    if complex_ratio > 0.4 or complex_score > 2:
        return "complex", min(0.9, 0.6 + complex_ratio * 0.4), categories
    elif simple_ratio > 0.5 and medium_score == 0:
        return "simple", min(0.9, 0.6 + simple_ratio * 0.4), categories
    elif medium_ratio > 0.3 or (simple_score > 0 and medium_score > 0):
        return "medium", min(0.85, 0.55 + medium_ratio * 0.4), categories
    elif simple_score > 0:
        return "simple", 0.65, categories
    else:
        return "complex", 0.55, categories


def load_enabled_agents(config_path: Optional[str]) -> dict:
    """Load enabled agents from config, grouped by cost tier."""
    if not config_path or not os.path.exists(config_path):
        return {
            "routing": {
                "simple": ["gpt-4o-mini"],
                "medium": ["gpt-4o-mini"],
            },
            "agents": [],
        }
    with open(config_path) as f:
        config = json.load(f)
    enabled = [a for a in config.get("agents", []) if a.get("enabled", False)]
    routing = config.get("routing_rules", {})
    return {"routing": routing, "agents": enabled}


def classify(task: str, config_path: Optional[str] = None) -> ClassificationResult:
    result = ClassificationResult()

    complexity, confidence, categories = estimate_complexity(task)
    result.complexity = complexity
    result.confidence = confidence
    result.task_categories = categories

    # Feinere Kategorien für Modell-Auswahl
    fine_cats = get_fine_categories(task)
    result.fine_categories = fine_cats

    # Modell-Empfehlung
    model_rec = recommend_model(complexity, fine_cats)
    result.recommended_model = model_rec.get("model")
    result.model_reasoning = model_rec.get("reasoning", "")
    result.model_alternatives = model_rec.get("alternatives", [])

    # Check for hard-complex patterns
    hard_score, _ = score_text(task, HARD_COMPLEX)
    if hard_score > 0:
        result.warnings.append(
            "Task enthält Sicherheits- oder Datenschutz-Keywords — Claude direkt empfohlen."
        )
        result.delegate = False
        result.recommended_model = None
        result.reasoning = (
            "Task betrifft sicherheitsrelevante oder rechtliche Themen. "
            "Delegation nicht empfohlen — Claude sollte direkt antworten."
        )
        return result

    # Determine delegation
    config = load_enabled_agents(config_path)
    routing = config["routing"]
    enabled_ids = [a["id"] for a in config["agents"]]

    if complexity == "simple":
        result.delegate = True
        candidates = routing.get("simple", [])
        result.recommended_agents = [a for a in candidates if a in enabled_ids]
        result.reasoning = (
            f"Task ist klar abgegrenzt und erfordert kein tiefes Reasoning. "
            f"Delegation spart Tokens bei gleichem Ergebnis."
        )
        if not result.recommended_agents:
            result.delegate = False
            result.warnings.append("Keine passenden Agenten aktiviert. Aktiviere einen in config/agents.json.")

    elif complexity == "medium":
        result.delegate = True
        candidates = routing.get("medium", [])
        result.recommended_agents = [a for a in candidates if a in enabled_ids]
        result.reasoning = (
            f"Task ist mittelschwer — ein gutes günstiges Modell kann dies erledigen. "
            f"Ergebnis sollte von Claude geprüft werden."
        )
        result.warnings.append("Medium-Aufgaben: Ergebnis vor Verwendung von Claude prüfen lassen.")
        if not result.recommended_agents:
            result.delegate = False
            result.warnings.append("Keine passenden Agenten aktiviert. Aktiviere einen in config/agents.json.")

    else:  # complex
        result.delegate = False
        result.recommended_model = None
        result.reasoning = (
            "Task erfordert mehrstufiges Reasoning, strategisches Urteilsvermögen "
            "oder domänenspezifisches Wissen. Claude direkt empfohlen."
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Klassifiziere einen Task für die Delegation.")
    parser.add_argument("--task", required=True, help="Task-Beschreibung")
    parser.add_argument(
        "--config",
        default="${CLAUDE_PLUGIN_ROOT}/config/agents.json",
        help="Pfad zur agents.json",
    )
    parser.add_argument("--pretty", action="store_true", help="JSON schön formatiert ausgeben")
    args = parser.parse_args()

    # Resolve config path
    config_path = args.config
    if "${CLAUDE_PLUGIN_ROOT}" in config_path:
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = config_path.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)

    result = classify(args.task, config_path if os.path.exists(config_path) else None)

    output = {
        "complexity": result.complexity,
        "confidence": round(result.confidence, 2),
        "delegate": result.delegate,
        "recommended_agents": result.recommended_agents,
        "recommended_model": result.recommended_model,
        "model_reasoning": result.model_reasoning,
        "model_alternatives": result.model_alternatives,
        "reasoning": result.reasoning,
        "task_categories": result.task_categories,
        "fine_categories": result.fine_categories,
        "warnings": result.warnings,
    }

    indent = 2 if args.pretty else None
    print(json.dumps(output, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
