# Prompt: Erstellung eines Projektplans für einen MCP-Server

## Persona
Agiere als erfahrener Senior Projektmanager, spezialisiert auf die Planung von Softwareprojekten im Backend-Bereich. Deine Pläne sind bekannt für ihre Klarheit, Struktur und Umsetzbarkeit.

## Ziel
Erstelle einen umfassenden und detaillierten Projektplan für die Entwicklung eines MCP-Servers, der als Schnittstelle zu einer externen API dient. Das Ergebnis speicherst du als `PLAN.md`-Datei im Verzeichnis `docs/`.

## Kontext
Das primäre Referenzdokument für diese Aufgabe ist der beigefügte `PROJEKTPLAN.md`. Dieses Dokument dient als Vorlage und Best-Practice-Beispiel für die Struktur, die Phasen und den Detaillierungsgrad. Das Projekt wird das Python-Framework fastmcp nutzen.

## Anweisungen

1. Analysiere die Vorlage: Studiere den `PROJEKTPLAN.md` sorgfältig. Verstehe die Logik hinter der Aufteilung in vier Phasen und die Art der Ziele und Aktionen, die pro Phase definiert sind.
2. Struktur übernehmen: Gliedere den neuen Plan exakt nach den vier Hauptphasen der Vorlage:
   - Phase 1: Grundlagen und Einrichtung
   - Phase 2: Kernfunktionalität und API-Integration
   - Phase 3: Testing und Qualitätssicherung
   - Phase 4: Deployment und Dokumentation
3. Inhalte anpassen und detaillieren: Formuliere für jede Phase die spezifischen Ziele und konkreten Aktionen. Nutze die Aktionen aus dem `PROJEKTPLAN.md` als Inspiration, aber passe sie auf ein generisches oder neues Projekt an. Stelle sicher, dass jede Aktion ein klar definiertes Ergebnis hat.
   - Phase 1: Behandle Themen wie Anforderungsanalyse (API-Spezifikation, Authentifizierung), Umgebungs-Setup (Git, virtuelle Umgebung, Framework) und Konfigurationsmanagement (.env, Secrets).
   - Phase 2: Beschreibe die Entwicklung der Kernkomponenten wie eines API-Clients (mit Fehlerbehandlung), der MCP-Endpunkte und der Datenvalidierung (z.B. mit Pydantic).
   - Phase 3: Plane konkrete Teststrategien, einschließlich Unit-Tests (mit Mocking), Integrationstests gegen eine Sandbox und Code-Reviews zur Qualitätssicherung.
   - Phase 4: Definiere eine vollständige Deployment-Strategie, inklusive Containerisierung (Docker), CI/CD-Pipelines, Monitoring/Logging und der Erstellung einer essenziellen Projektdokumentation.
4. Zeitplan entwerfen: Weise jeder Hauptphase eine realistische, geschätzte Dauer in Wochen zu.
5. Formatierung: Gib das Ergebnis als gut lesbare Markdown-Datei aus. Verwende Überschriften, Listen und Fettungen, um die Struktur klar hervorzuheben.

## Struktur und Inhalt der zu erstellenden `PLAN.md`

Erstelle die `PLAN.md`-Datei exakt nach der folgenden Struktur und den Formatierungsregeln.

---

### **BEGINN DES INHALTS FÜR `PLAN.md`**

# Titel und Metadaten
Erstelle einen Haupttitel wie "# KI-Automatisierungsberatung Implementation Plan" und einen Block mit folgenden Metadaten:
- **Last Updated:** [Aktueller Monat und Jahr]
- **Business Status:** [Deine Einschätzung der Umsetzungsreife auf einer Skala von 1-10]
- **Total Tasks:** [Gesamtzahl der von dir erstellten Aufgaben]
- **Analysis Date:** [Aktueller Monat und Jahr]

# 🔍 KI-Automatisierungsberatung Analysis Summary
Fasse deine Analyseergebnisse in einem kurzen Abschnitt zusammen. Liste die wichtigsten Geschäftsbereiche auf, die Aufmerksamkeit erfordern, basierend auf dem Businessplan.

# Aufgaben nach Priorität
Gruppiere alle Aufgaben nach den folgenden vier Prioritätsstufen. Ordne die Aufgaben innerhalb jeder Prioritätsstufe nach den Analyse-Kategorien (z.B. "Content-Pipeline & Automatisierung", "Technische Infrastruktur", "Marketing & Vertrieb").

- `## 🔴 Critical Priority (Immediate - Month 1)`
- `## 🟡 High Priority (Month 2-3)`
- `## 🟢 Medium Priority (Month 4-6)`
- `## 🔵 Low Priority (Month 7-12)`

# Aufgaben-Formatierung
Jede einzelne Aufgabe MUSS diesem Format folgen:
` - [ ] **CATEGORY-XXX**: Kurze, prägnante Beschreibung der Geschäfts-Aufgabe`
- `[ ]` ist die Checkbox.
- `CATEGORY` ist ein Kürzel für die Kategorie (z.B., `CONTENT`, `INFRA`, `MARKET`, `PROD`, `LEGAL`, `TECH`, `AUTO`, `SALES`, `FIN`, `DOC`, `STRAT`, `QA`).
- `XXX` ist eine dreistellige, fortlaufende Nummer pro Kategorie (beginnend bei `001`).

# 📋 Task Categories Summary
Erstelle eine Markdown-Tabelle, die die Anzahl der Aufgaben pro Kategorie und Priorität zusammenfasst. Die Tabelle soll Spalten für "Category", "Critical", "High", "Medium", "Low" und "Total" haben.

# 🎯 Implementation Guidelines
Füge einen Abschnitt mit Implementierungsrichtlinien hinzu, der die Priorisierungsregeln, Abhängigkeiten zwischen Aufgaben und Erfolgskriterien für das KI-Automatisierungsgeschäft definiert.

# 📝 Notes
Füge einen abschließenden Abschnitt hinzu, der bekannte Herausforderungen (`Current Business Challenges`), spezifische Umsetzungsempfehlungen (`KI-Automatisierung Business Implementation Needed`) und kritische Erfolgsfaktoren (`Business Success Critical Factors`) zusammenfasst.

### **ENDE DES INHALTS FÜR `PLAN.md`**