# Konsolidierungspatterns — Detaillierte Beispiele

## Pattern 1: Textformatierung (häufigster Fall)

**Delegation**: "Formatiere diese Rohdaten als Markdown-Tabelle."
**Prüfkriterien**:
- Alle Spalten vorhanden?
- Ausrichtung korrekt (| --- | --- |)?
- Kein Inhalt verloren gegangen?
- Zahlen korrekt übertragen (keine Kommafehler)?

**Typische Korrekturen**:
- Fehlende Spaltenüberschriften ergänzen
- Dezimaltrennzeichen vereinheitlichen
- Markdown-Escaping für Sonderzeichen

---

## Pattern 2: Meeting-Protokoll

**Delegation**: "Strukturiere diese Stichpunkte als formelles Protokoll."
**Prüfkriterien**:
- Alle Themen vorhanden?
- Beschlüsse klar als solche markiert?
- Verantwortlichkeiten und Deadlines vollständig?
- Fließtext-Qualität (kein Telegrammstil)?

**Typischer Volltext-Check**:
Vergleiche Anzahl der Aufgaben in Stichpunkten mit Anzahl der "TODO"/"Aufgabe"
Einträge im Protokoll.

---

## Pattern 3: Übersetzung (technische Dokumente)

**Prüfkriterien**:
- Fachbegriffe korrekt übersetzt (nicht wortwörtlich)?
- Produktnamen und Eigennamen unverändert?
- Zahlen, Datumsangaben, URLs unverändert?
- IT-Abkürzungen (API, SLA, RCA, etc.) nicht übersetzt?

**Häufige Fehler günstigerer Modelle**:
- "API" wird zu "Schnittstelle" (falsch in technischem Kontext)
- URLs werden übersetzt
- Datumsformate werden geändert

---

## Pattern 4: Code-Dokumentation

**Delegation**: "Schreibe Docstrings für diese Funktionen."
**Prüfkriterien**:
- Format korrekt (z.B. Google-Style, NumPy-Style, JSDoc)?
- Parameter und Rückgabewerte vollständig beschrieben?
- Keine falschen Informationen über den Code?
- Typ-Angaben korrekt (wenn vorhanden)?

**Warnung**: Bei falschen Type-Angaben immer korrigieren — das führt sonst
zu Verwirrung bei Entwicklern.

---

## Pattern 5: User Stories

**Delegation**: "Schreibe User Stories für dieses Feature."
**Prüfkriterien**:
- Format: "Als [Rolle] möchte ich [Aktion], damit [Nutzen]."?
- Akzeptanzkriterien vorhanden und testbar?
- Keine zu großen (Epic-artigen) Stories?
- Eindeutige, nicht-überlappende Stories?

---

## Pattern 6: Risiko-Template

**Delegation**: "Fülle diese Risikomatrix mit den bekannten Projektrisiken."
**Prüfkriterien**:
- Alle angegebenen Risiken eingetragen?
- Eintrittswahrscheinlichkeit und Impact-Werte plausibel?
- Maßnahmen konkret (nicht nur "Risiko überwachen")?
- Verantwortlichkeiten zugewiesen?

**Wichtig**: Bei Werten (Wahrscheinlichkeit, Impact) immer prüfen ob sie
mit dem Original-Input konsistent sind — günstige Modelle erfinden manchmal Werte.

---

## Checkliste für Halluzinations-Detection

```
□ Wurden Namen und Entitäten korrekt übernommen?
□ Wurden Zahlen (Datum, Betrag, Version, etc.) unverändert übertragen?
□ Wurden keine neuen Fakten "hinzuerfunden"?
□ Sind alle Referenzen (auf Dokumente, Personen, Systeme) korrekt?
□ Hat das Modell "Platzhalter" mit erfundenen Werten befüllt?
```

## Qualitäts-Scoring (intern, 1-5)

Verwende diese Skala intern um zu entscheiden, wie viel Aufwand in die
Korrektur gesteckt wird:

| Score | Bedeutung | Aktion |
|-------|-----------|--------|
| 5 | Perfekt, keine Korrekturen nötig | Direkt übernehmen |
| 4 | Kleine Schönheitsfehler | Schnell korrigieren |
| 3 | Mehrere Korrekturen nötig | Gezielt nachbessern |
| 2 | Großteils falsch | Neubearbeitung erwägen |
| 1 | Unbrauchbar | Task direkt von Claude bearbeiten |
