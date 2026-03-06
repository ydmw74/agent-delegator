# Komplexitäts-Rubrik: Detaillierte Entscheidungstabelle

## Entscheidungsmatrix

| Kriterium | Einfach (delegieren) | Mittel (delegieren + prüfen) | Komplex (Claude direkt) |
|-----------|---------------------|------------------------------|------------------------|
| **Input vollständig?** | Ja, alles vorhanden | Weitgehend ja | Nein, Nachfragen nötig |
| **Output klar definiert?** | Ja, Format bekannt | Weitgehend ja | Nein, offen |
| **Mehrstufiges Denken?** | Nein | Wenig | Ja |
| **Domänenwissen nötig?** | Wenig bis keins | Etwas | Tief |
| **Fehler-Toleranz?** | Hoch (leicht prüfbar) | Mittel | Niedrig (Konsequenzen) |
| **Kreativität nötig?** | Nein | Wenig | Ja |

## IT-Projektmanagement: Spezifische Beispiele

### ✅ EINFACH — Sicher delegieren

| Task | Beschreibung | Empfohlener Agent |
|------|-------------|-------------------|
| Statusbericht formatieren | Rohdaten (Bullet Points) → PM-Standardformat | Ollama / GPT-4o-mini |
| Changelog aus Commits | Git-Log → strukturierter Changelog | GPT-4o-mini |
| Meeting-Protokoll strukturieren | Stichpunkte → Fließtext-Protokoll | Ollama / GPT-4o-mini |
| Datumsformatierung harmonisieren | Gemischte Datumsformate → ISO 8601 | Ollama |
| Template befüllen | Projektvorlage + Daten → ausgefüllte Vorlage | GPT-4o-mini |
| Glossar übersetzen | Fachbegriffe Deutsch ↔ Englisch | GPT-4o-mini / Gemini |
| Tabelle in Markdown | Excel-Inhalt → Markdown-Tabelle | Ollama |
| Aufgabenliste sortieren | Nach Priorität / Fälligkeit sortieren | Ollama |
| Akronymverzeichnis | Akronyme aus Text extrahieren und erklären | GPT-4o-mini |
| Commit-Messages normalisieren | Auf Convention-Format bringen | Ollama |

### 🟡 MITTEL — Delegieren + von Claude prüfen lassen

| Task | Beschreibung | Empfohlener Agent |
|------|-------------|-------------------|
| User Stories schreiben | Aus Feature-Beschreibung → As a/I want/So that | GPT-4o-mini |
| Akzeptanzkriterien | Aus User Story → Gherkin oder Prosaform | GPT-4o-mini |
| API-Dokumentation | Aus vorhandenem Code → Markdown-Docs | opencode |
| Unit Tests generieren | Für beigegebenen, einfachen Code | opencode |
| Code-Review: Style | ESLint/Format-Probleme identifizieren | opencode |
| RACI-Matrix-Entwurf | Aus Projektbeschreibung → erste RACI-Version | GPT-4o-mini |
| Meeting-Agenda | Aus Themen-Liste → strukturierte Agenda | GPT-4o-mini |
| Risiko-Template ausfüllen | Bekannte Risiken → Risikomatrix-Einträge | GPT-4o-mini |
| Sprint-Bericht | Velocity + Completed Stories → Bericht | GPT-4o-mini |
| Stakeholder-Liste erstellen | Aus Beschreibung → Stakeholder-Inventar | GPT-4o-mini |

### 🔴 KOMPLEX — Claude direkt (nie delegieren)

| Task | Warum komplex |
|------|--------------|
| Technologie-Auswahlentscheidung | Trade-offs, Kontext, langfristige Konsequenzen |
| Architektur-Design | Novel problem, viele abhängige Entscheidungen |
| Risikoanalyse und -bewertung | Domänenwissen, Kontext, Kausalität |
| Eskalationsplan | Stakeholder-Kontext, politisches Gespür |
| Budget-Freigabe vorbereiten | Zahlen, Rechtfertigung, Verantwortlichkeit |
| Security-Review | Sicherheitskritisch, Expertenwissen |
| Change Management Plan | Organisationspsychologie, Kontext |
| Executive Summary | Empfänger-spezifisch, strategisch |
| Konfliktlösung | Soziale Intelligenz, Kontext |
| Root Cause Analysis | Mehrstufiges Reasoning, Kausalität |

## Warnsignale: Immer Claude direkt

Wenn der Task eines dieser Keywords enthält, nie delegieren:

- Passwort, Credentials, API-Key, Token, Secret
- Sicherheitslücke, Vulnerability, Exploit
- Personenbezogene Daten, DSGVO, GDPR, PII
- Rechtlich, Legal, Haftung, Compliance (detailliert)
- Budget-Freigabe, Genehmigung, Autorisierung

## Unsicherheits-Heuristik

Wenn du unsicher bist: **Delegiere lieber nicht.**

Die Kostenersparnis lohnt sich nicht, wenn:
1. Du das Ergebnis sowieso nochmals komplett umschreiben musst
2. Die Aufgabe mehr als ~3 Iterationen der Delegation benötigen würde
3. Ein Fehler im delegierten Ergebnis schwere Konsequenzen hätte
