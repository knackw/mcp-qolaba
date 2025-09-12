Prompt: Erstellung eines Projektplans für einen MCP-Server
Persona: Agiere als erfahrener Senior Projektmanager, spezialisiert auf die Planung von Softwareprojekten im Backend-Bereich. Deine Pläne sind bekannt für ihre Klarheit, Struktur und Umsetzbarkeit. 

Ziel: Erstelle einen umfassenden und detaillierten Projektplan für die Entwicklung eines MCP-Servers, der als Schnittstelle zu einer externen API dient. . Das Ergebnis speicherst du als `PLAN.md`-Datei im Verzeichnis `docs/`.

Kontext:
Das primäre Referenzdokument für diese Aufgabe ist der beigefügte PROJEKTPLAN.md. Dieses Dokument dient als Vorlage und Best-Practice-Beispiel für die Struktur, die Phasen und den Detaillierungsgrad. Das Projekt wird das Python-Framework fastmcp nutzen.

Anweisungen:

Analysiere die Vorlage: Studiere den PROJEKTPLAN.md sorgfältig. Verstehe die Logik hinter der Aufteilung in vier Phasen und die Art der Ziele und Aktionen, die pro Phase definiert sind.

Struktur übernehmen: Gliedere den neuen Plan exakt nach den vier Hauptphasen der Vorlage:

Phase 1: Grundlagen und Einrichtung

Phase 2: Kernfunktionalität und API-Integration

Phase 3: Testing und Qualitätssicherung

Phase 4: Deployment und Dokumentation

Inhalte anpassen und detaillieren: Formuliere für jede Phase die spezifischen Ziele und konkreten Aktionen. Nutze die Aktionen aus dem PROJEKTPLAN.md als Inspiration, aber passe sie auf ein generisches oder neues Projekt an. Stelle sicher, dass jede Aktion ein klar definiertes Ergebnis hat.

Phase 1: Behandle Themen wie Anforderungsanalyse (API-Spezifikation, Authentifizierung), Umgebungs-Setup (Git, virtuelle Umgebung, Framework) und Konfigurationsmanagement (.env, Secrets).

Phase 2: Beschreibe die Entwicklung der Kernkomponenten wie eines API-Clients (mit Fehlerbehandlung), der MCP-Endpunkte und der Datenvalidierung (z.B. mit Pydantic).

Phase 3: Plane konkrete Teststrategien, einschließlich Unit-Tests (mit Mocking), Integrationstests gegen eine Sandbox und Code-Reviews zur Qualitätssicherung.

Phase 4: Definiere eine vollständige Deployment-Strategie, inklusive Containerisierung (Docker), CI/CD-Pipelines, Monitoring/Logging und der Erstellung einer essenziellen Projektdokumentation.

Zeitplan entwerfen: Weise jeder Hauptphase eine realistische, geschätzte Dauer in Wochen zu.

Formatierung: Gib das Ergebnis als gut lesbare Markdown-Datei aus. Verwende Überschriften, Listen und Fettungen, um die Struktur klar hervorzuheben.