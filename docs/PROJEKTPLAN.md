Anweisung zur Erstellung einer PLAN.md für den Qolaba API MCP Server
Deine Rolle und Aufgabe
Du bist ein erfahrener Softwarearchitekt und technischer Projektmanager. Deine Aufgabe ist es, den gesamten Projektplan für den "Qolaba API MCP Server" sorgfältig zu analysieren, technische Umsetzungsschritte zu identifizieren und einen detaillierten, umsetzbaren Aufgabenplan zu erstellen. Das Ergebnis speicherst du als PLAN.md-Datei im Verzeichnis docs/.

Analyse-Richtlinien
Führe eine umfassende Analyse durch und achte dabei auf folgende Bereiche, basierend auf dem Projektplan:

Grundlagen & Einrichtung: Git-Repository, Python-Umgebung, Klonen des Frameworks, Abhängigkeiten und Konfigurationsmanagement.

Kernfunktionalität & API-Integration: API-Client-Modul, Fehlerbehandlung, MCP-Endpunkte, Daten-Serialisierung und -Validierung.

Testing & Qualitätssicherung: Unit-Tests, Integrationstests, Mocking-Strategien, Code-Reviews und Refactoring.

Deployment & Dokumentation: Docker-Containerisierung, CI/CD-Pipelines, Monitoring, Logging und technische Dokumentation.

Technologie-Stack: Python, fastmcp-Framework, Pydantic, Docker, GitHub Actions.

Struktur und Inhalt der zu erstellenden PLAN.md
Erstelle die PLAN.md-Datei exakt nach der folgenden Struktur und den Formatierungsregeln.

BEGINN DES INHALTS FÜR PLAN.md
Titel und Metadaten
Erstelle einen Haupttitel wie "# Qolaba API MCP Server Implementierungsplan" und einen Block mit folgenden Metadaten:

Last Updated: [Aktueller Monat und Jahr]

Project Status: [Deine Einschätzung der Umsetzungsreife, z.B. "Planungsphase"]

Total Tasks: [Gesamtzahl der von dir erstellten Aufgaben]

Analysis Date: [Aktueller Monat und Jahr]

🔍 Analyse-Zusammenfassung
Fasse deine Analyseergebnisse in einem kurzen Abschnitt zusammen. Liste die wichtigsten technischen Bereiche auf, die Aufmerksamkeit erfordern, basierend auf dem Projektplan.

Aufgaben nach Priorität und Phase
Gruppiere alle Aufgaben nach den folgenden vier Prioritätsstufen, die den Phasen des Projektplans entsprechen. Ordne die Aufgaben innerhalb jeder Prioritätsstufe nach den Analyse-Kategorien (z.B. "Grundlagen & Einrichtung", "Kernfunktionalität & API-Integration").

## 🔴 Kritische Priorität (Woche 1)

## 🟡 Hohe Priorität (Woche 2-3)

## 🟢 Mittlere Priorität (Woche 4)

## 🔵 Niedrige Priorität (Woche 5)

Aufgaben-Formatierung
Jede einzelne Aufgabe MUSS diesem Format folgen:
- [ ] **CATEGORY-XXX**: Kurze, prägnante Beschreibung der technischen Aufgabe

[ ] ist die Checkbox.

CATEGORY ist ein Kürzel für die Kategorie (z.B., SETUP, API, MCP, DATA, TEST, QA, DEPLOY, DOCS).

XXX ist eine dreistellige, fortlaufende Nummer pro Kategorie (beginnend bei 001).

📋 Zusammenfassung der Aufgabenkategorien
Erstelle eine Markdown-Tabelle, die die Anzahl der Aufgaben pro Kategorie und Priorität zusammenfasst. Die Tabelle soll Spalten für "Category", "Critical", "High", "Medium", "Low" und "Total" haben.

🎯 Implementierungsrichtlinien
Füge einen Abschnitt mit Implementierungsrichtlinien hinzu, der die Priorisierungsregeln, technische Abhängigkeiten zwischen Aufgaben und Erfolgskriterien für das Projekt definiert.

📝 Anmerkungen
Füge einen abschließenden Abschnitt hinzu, der bekannte Herausforderungen (Current Technical Challenges), spezifische Umsetzungsempfehlungen (Technical Implementation Needed) und kritische Erfolgsfaktoren (Project Success Critical Factors) zusammenfasst.

ENDE DES INHALTS FÜR PLAN.md