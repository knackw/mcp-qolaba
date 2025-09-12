# Anweisung zur Erstellung oder Aktualisierung eines strategischen KI-Automatisierungsberatung Umsetzungsplans (`TASKS.md`)

## Deine Rolle und Aufgabe

Du bist ein leitender Geschäftsstratege und KI-Automatisierungsexperte. Deine Aufgabe ist es, einen umfassenden und umsetzbaren Geschäfts-Umsetzungsplan zu erstellen oder aktualisieren, der auf einer tiefgehenden Analyse der Geschäftsziele und des aktuellen Umsetzungsstands basiert.

## Input-Dokumente

Du MUSST die folgenden Dokumente als Grundlage für deine Analyse und Synthese verwenden:
1.  **Der Businessplan:** `docs/Businessplan.md` für die übergeordneten Geschäftsziele, Marktanalyse und Strategie der KI-Automatisierungsberatung.
2.  **Die Aufgabenliste:** `docs/PLAN.md` für die granularen, geschäftlichen Umsetzungsaufgaben.
3.  **Projektdokumentation:** Weitere wichtige Informationen im docs-Ordner zur technischen und operativen Umsetzung.

## Deine Aufgabe

Synthetisiere die Informationen aus den Dokumenten und erstelle oder aktualisiere einen detaillierten, strategischen Geschäfts-Umsetzungsplan. Speichere diesen Plan in der Datei `docs/TASKS.md`. Der Plan soll nicht nur Aufgaben auflisten, sondern diese in einen strategischen Geschäftsrahmen einbetten, inklusive Begründungen, Zeitplänen und Erfolgsmetriken für die KI-Automatisierungsberatung.

## Struktur und Inhalt der zu erstellenden oder zu aktualisierenden `TASKS.md`

Erstelle oder aktualisierende `TASKS.md`-Datei exakt nach der folgenden, detaillierten Struktur.

---

### **BEGINN DES INHALTS FÜR `TASKS.md`**

# Executive Summary
Beginne mit einer prägnanten Zusammenfassung, die den Zweck des Dokuments, den aktuellen Geschäfts-Umsetzungsstatus (basierend auf der `PLAN.md`), die Hauptschwerpunkte und den geschätzten Zeitrahmen für kritische Geschäftsumsetzungen umreißt.

# Key Goals and Constraints
Extrahiere und liste die wichtigsten Geschäftsziele, operativen Einschränkungen und Qualitätsstandards auf.
- **Primary Goals:** Leite diese aus dem Businessplan ab (z.B. "Content-Pipeline aufbauen", "n8n-Workflows entwickeln", "Mitgliedschaftsplattform etablieren", "RAG-Systeme implementieren").
- **Technical Constraints:** Leite diese aus dem Businessplan ab (z.B. "WordPress + n8n", "IONOS Server", "Docker Container", "DSGVO-Konformität", "Self-Hosting").
- **Quality Standards:** Synthetisiere diese aus den Dokumenten (z.B. "Professional Business Development", "KI-Automatisierung Best Practices", "DSGVO-Standards").

# Thematische Geschäfts-Umsetzungspläne
Erstelle oder aktualisiere für jedes Hauptthema (z.B. "Content-Pipeline & Automatisierung", "Technische Infrastruktur", "Marketing & Vertrieb", "Produkt- & Dienstleistungsportfolio") einen eigenen nummerierten Abschnitt. Jeder dieser Abschnitte MUSS enthalten:
- **### Rationale:** Eine kurze Begründung, warum dieser Bereich wichtig ist, basierend auf der Analyse aus der `PLAN.md` und dem Businessplan.
- **Unterabschnitte mit Aufgaben:** Gruppiere die Aufgaben aus der `docs/PLAN.md` thematisch.
- **Aufgaben-Formatierung:** Übernimm die Aufgaben als Checkliste (`- [ ]`) und **behalte die originalen Aufgaben-IDs bei** (z.B., `CONTENT-001`, `INFRA-001`). Ergänze, wo sinnvoll, weitere, noch detailliertere Unteraufgaben ohne ID.

**Beispiel für einen Themen-Abschnitt:**
```markdown
## 1. Content-Pipeline & Automatisierung Implementation

### Rationale
Current analysis reveals critical need for automated content creation pipeline to establish thought leadership and generate leads...

### Critical Content Tasks (Month 1)

#### 1.1 n8n Content Workflow Setup
- [ ] **CONTENT-001**: Setup n8n workflow for Markdown to Blog conversion
- [ ] **CONTENT-002**: Implement automated social media posting pipeline
- [ ] Create content quality assurance processes
```

# Timeline and Milestones
Erstelle eine Zeitleiste mit klaren Meilensteinen für die wichtigsten Geschäftsphasen:
- **Phase 1 (Month 1-2): Fundament & Setup** 
- **Phase 2 (Month 3-4): Launch & Monetarisierung**
- **Phase 3 (Month 5-6): Marketing & Skalierung**

Jede Phase sollte ihre Hauptaufgaben, Abhängigkeiten und erwarteten Ergebnisse definieren.

# Success Metrics and KPIs
Definiere messbare Erfolgsindikatoren für jede Geschäftsphase:
- **Content KPIs:** Blog-Traffic, E-Mail-Liste Wachstum, Social Media Engagement
- **Business KPIs:** Mitgliedschafts-Conversions, Service-Leads, Umsatzziele
- **Technical KPIs:** Workflow-Performance, System-Verfügbarkeit, Automatisierungsgrad

# Risk Management and Contingencies
Identifiziere potenzielle Risiken und Mitigation-Strategien basierend auf der SWOT-Analyse aus dem Businessplan:
- **Technical Risks:** API-Abhängigkeiten, Server-Performance, Backup-Strategien
- **Business Risks:** Markt-Sättigung, Wettbewerb, Skalierungs-Herausforderungen
- **Operational Risks:** Content-Qualität, DSGVO-Compliance, Kundenakquisition

# Resource Requirements
Liste die benötigten Ressourcen für die erfolgreiche Umsetzung auf:
- **Human Resources:** Eigene Arbeitszeit, potenzielle Freelancer oder Subunternehmer
- **Technical Resources:** Server-Kapazität, Software-Lizenzen, Entwicklungstools
- **Financial Resources:** Marketing-Budget, Infrastruktur-Kosten, Rechtliche Beratung

# Implementation Notes
Füge abschließende Hinweise zur praktischen Umsetzung hinzu:
- **Dependencies:** Kritische Abhängigkeiten zwischen Aufgaben
- **Quality Gates:** Kriterien für das Abschließen von Phasen
- **Documentation:** Wichtige Dokumentationsanforderungen für Compliance und Skalierung

### **ENDE DES INHALTS FÜR `TASKS.md`**