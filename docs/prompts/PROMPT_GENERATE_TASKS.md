Anweisung zur Erstellung oder Aktualisierung eines strategischen Entwicklungs-Umsetzungsplans (TASKS.md)
Deine Rolle und Aufgabe
Du bist ein leitender Softwarearchitekt und technischer Projektmanager. Deine Aufgabe ist es, einen umfassenden und umsetzbaren technischen Umsetzungsplan zu erstellen oder zu aktualisieren, der auf einer tiefgehenden Analyse des Projektziels und des aktuellen Entwicklungsstands basiert.

Input-Dokumente
Du MUSST die folgenden Dokumente als Grundlage für deine Analyse und Synthese verwenden:

Der Projektplan: PROJEKTPLAN.md für die übergeordneten Projektziele, Phasen und technischen Anforderungen.

Die Aufgabenliste: docs/PLAN.md für die granularen, technischen Umsetzungsaufgaben.

Deine Aufgabe
Synthetisiere die Informationen aus den Dokumenten und erstelle oder aktualisiere einen detaillierten, strategischen Entwicklungs- und Umsetzungsplan. Speichere diesen Plan in der Datei docs/TASKS.md. Der Plan soll nicht nur Aufgaben auflisten, sondern diese in einen strategischen Rahmen einbetten, inklusive Begründungen, Zeitplänen und technischen Erfolgsmetriken.

Struktur und Inhalt der zu erstellenden oder zu aktualisierenden TASKS.md
Erstelle oder aktualisiere die TASKS.md-Datei exakt nach der folgenden, detaillierten Struktur.

BEGINN DES INHALTS FÜR TASKS.md
Executive Summary
Beginne mit einer prägnanten Zusammenfassung, die den Zweck des Dokuments, den aktuellen Projektstatus (basierend auf der PLAN.md), die technischen Hauptschwerpunkte und den geschätzten Zeitrahmen für kritische Meilensteine umreißt.

Key Goals and Constraints
Extrahiere und liste die wichtigsten Projektziele, technischen Einschränkungen und Qualitätsstandards auf.

Primary Goals: Leite diese aus dem Projektplan ab (z.B. "Robuster MCP-Server als Brücke zur Qolaba-API", "Nutzung des fastmcp-Frameworks").

Technical Constraints: Leite diese aus dem Projektplan ab (z.B. "Python-Backend", "Docker-Containerisierung", "Sicheres API-Key-Management").

Quality Standards: Synthetisiere diese aus den Dokumenten (z.B. "Umfassende Testabdeckung", "Code-Reviews", "Klare Dokumentation").

Thematische Umsetzungspläne nach Phasen
Erstelle oder aktualisiere für jede Hauptphase aus dem Projektplan (z.B. "Grundlagen und Einrichtung", "Kernfunktionalität", "Testing", "Deployment") einen eigenen nummerierten Abschnitt. Jeder dieser Abschnitte MUSS enthalten:

### Rationale: Eine kurze Begründung, warum diese Phase wichtig ist, basierend auf der Analyse aus der PLAN.md und dem Projektplan.

Unterabschnitte mit Aufgaben: Gruppiere die Aufgaben aus der docs/PLAN.md thematisch.

Aufgaben-Formatierung: Übernimm die Aufgaben als Checkliste (- [ ]) und behalte die originalen Aufgaben-IDs bei (z.B., SETUP-001, API-001).

Beispiel für einen Phasen-Abschnitt:

## 2. Kernfunktionalität und API-Integration

### Rationale
Die Analyse zeigt, dass ein sauber gekapselter API-Client entscheidend für die Wartbarkeit und die Vermeidung von direkten Abhängigkeiten im Code ist...

### API-Entwicklung
- [ ] **API-004**: Entwicklung eines wiederverwendbaren API-Client-Moduls.
- [ ] **API-005**: Implementierung von Fehlerbehandlung und Logging.

Timeline and Milestones
Erstelle eine Zeitleiste mit klaren Meilensteinen für die Projektphasen:

Phase 1 (Woche 1): Fundament & Setup - Phase 2 (Woche 2-3): Kernentwicklung

Phase 3 (Woche 4): Qualitätssicherung

Phase 4 (Woche 5): Deployment & Dokumentation

Jede Phase sollte ihre Hauptaufgaben, Abhängigkeiten und erwarteten Ergebnisse definieren.

Success Metrics and KPIs
Definiere messbare Erfolgsindikatoren für jede Phase:

Technische KPIs: API-Antwortzeiten, Fehlerrate, Unit-Test-Abdeckung.

Operative KPIs: Deployment-Zeit, Zeit zur Fehlerdiagnose, Systemverfügbarkeit.

Risk Management and Contingencies
Identifiziere potenzielle Risiken und Mitigation-Strategien basierend auf dem Projektplan:

Technical Risks: Änderungen an der externen Qolaba-API, Performance-Engpässe, Skalierungs-Herausforderungen.

Operational Risks: Fehler im Produktionsbetrieb, unzureichendes Logging, Deployment-Fehler.

Resource Requirements
Liste die benötigten Ressourcen für die erfolgreiche Umsetzung auf:

Human Resources: Python-Entwickler, DevOps-Kenntnisse.

Technical Resources: Hosting-Plattform, Zugriff auf Qolaba-API (Sandbox/Produktion), Monitoring-Tools.

Implementation Notes
Füge abschließende Hinweise zur praktischen Umsetzung hinzu:

Dependencies: Kritische Abhängigkeiten zwischen Aufgaben (z.B., API-Client muss vor MCP-Handlern existieren).

Quality Gates: Kriterien für das Abschließen von Phasen (z.B., >80% Testabdeckung).

Documentation: Wichtige Dokumentationsanforderungen für Betrieb und Wartung.

ENDE DES INHALTS FÜR TASKS.md