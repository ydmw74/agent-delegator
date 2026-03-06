---
name: result-consolidator
description: >
  This skill should be used after delegated subtasks have returned results
  and Claude needs to review, validate, and consolidate them into a final answer.

  Trigger phrases: "konsolidiere die Ergebnisse", "prüfe das Delegations-Ergebnis",
  "merge die Antworten", "fasse die Teilergebnisse zusammen",
  "consolidate delegation results", "review delegated output".

  Also trigger automatically after the task-router skill has completed
  one or more delegated tasks and their results need to be integrated.
version: 0.1.0
---

# Result Consolidator

Dieser Skill führt Claude durch die Prüfung und Zusammenführung von Ergebnissen,
die von anderen Agenten (Ollama, GPT-4o-mini, opencode, etc.) zurückgegeben wurden.

## Grundprinzip

Günstige Modelle können gut abgegrenzte Tasks erledigen — aber sie können
halluzinieren, Format-Anforderungen missverstehen oder unvollständige Ergebnisse
liefern. Claude fungiert als **Qualitätssicherung** und **Integrator**.

## Schritt 1: Ergebnis lesen

Lies die Ergebnisdatei(en) des delegierten Tasks:

```bash
cat /tmp/delegate_result.txt
```

Oder bei mehreren parallelen Tasks:
```bash
for f in /tmp/result_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
```

## Schritt 2: Qualitätsprüfung

Beurteile das Ergebnis anhand dieser Kriterien:

### Vollständigkeit
- Wurde die Aufgabe vollständig erledigt?
- Fehlen Teile, die explizit angefordert wurden?

### Korrektheit
- Bei Textformatierung: Stimmt die Struktur?
- Bei Code: Syntaktisch korrekt? Logisch sinnvoll?
- Bei Übersetzungen: Bedeutung beibehalten?
- Bei Datenextraktion: Alle relevanten Daten extrahiert?

### Halluzinations-Check
- Wurden Fakten erfunden, die nicht im Input standen?
- Wurden spezifische Werte (Zahlen, Namen, Daten) korrekt übertragen?
- Bei Templates: Wurden Platzhalter korrekt befüllt?

### Format-Konformität
- Stimmt das Ausgabeformat mit der Anforderung überein?
- Markdown korrekt? Tabellen vollständig? Listen konsistent?

## Schritt 3: Konsolidierungsmuster

### Muster A: Einfache Übernahme (Ergebnis ist gut)
Das delegierte Ergebnis ist vollständig und korrekt. Direkt übernehmen,
ggf. mit geringen Nachbesserungen.

```
[Ergebnis von Agent X, keine wesentlichen Änderungen]
```

### Muster B: Korrektur und Integration
Das Ergebnis ist größtenteils gut, aber mit Mängeln. Claude korrigiert
die Mängel und integriert das Ergebnis.

Häufige Korrekturen:
- Fehlende Felder ergänzen
- Falsches Format korrigieren
- Halluzinierte Fakten durch korrekte Werte ersetzen
- Inkonsistenzen glätten

### Muster C: Ablehnung und Neubearbeitung
Das Ergebnis ist unbrauchbar (zu viele Fehler, komplett falsches Format,
Halluzinationen die den Inhalt verfälschen). Claude bearbeitet den
ursprünglichen Task direkt.

Gründe für Ablehnung:
- Mehr als 30% des Inhalts ist falsch oder halluziniert
- Das Format weicht fundamental von der Anforderung ab
- Sicherheitsrelevante Fehler (z.B. falscher Code)

### Muster D: Zusammenführung (mehrere Subtasks)
Mehrere delegierte Ergebnisse werden zu einem kohärenten Gesamtergebnis
zusammengeführt.

Vorgehen:
1. Alle Teilergebnisse lesen
2. Redundanzen identifizieren und entfernen
3. Widersprüche auflösen (bei Zweifel: konservativere Version wählen)
4. Übergangsformulierungen hinzufügen
5. Auf Vollständigkeit prüfen
6. Gesamtstruktur harmonisieren

## Schritt 4: Transparenz gegenüber dem User

Wenn das Ergebnis auf delegierten Tasks basiert, kurz erwähnen — besonders
wenn Korrekturen vorgenommen wurden. Beispiele:

- "Ich habe einen günstigeren Agenten für die Formatierungsaufgabe eingesetzt und das Ergebnis geprüft."
- "Die Statusberichte wurden von einem Hilfs-Modell strukturiert; ich habe drei Format-Fehler korrigiert."
- "Das Ergebnis musste neu bearbeitet werden, da die Delegation unvollständig war."

Nicht erwähnen wenn: Das Ergebnis direkt übernehmbar war und keine Korrekturen nötig.

## Referenz: Konsolidierungspatterns

Lies `references/consolidation-patterns.md` für detaillierte Beispiele und
Textbausteine für häufige Konsolidierungsszenarien.
