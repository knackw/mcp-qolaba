# GitHub Copilot Anweisungen für Qolaba MCP Server

Du hilfst bei der Entwicklung des Qolaba API MCP Servers. Beachte folgende Richtlinien:

## Projekt-Kontext
- **Ziel**: Entwicklung eines robusten MCP-Servers für die Qolaba-API
- **Framework**: FastMCP v2
- **Sprache**: Python 3.11+
- **Architektur**: Modulare Struktur mit API-Client, MCP-Handler und Datenmodellen

## Code-Standards
- Verwende Type Hints für alle Funktionen
- Folge PEP 8 Code-Stil
- Schreibe docstrings im Google-Format
- Nutze Pydantic für Datenvalidierung
- Implementiere async/await für I/O-Operationen

## Sicherheit
- Sensible Daten (API-Keys) nur über Umgebungsvariablen
- Nutze sichere Konfigurationsmanagement-Patterns
- Implementiere robuste Fehlerbehandlung
- Verwende Retry-Mechanismen für API-Calls

## Testing
- Schreibe Unit-Tests für alle neuen Funktionen
- Nutze pytest als Test-Framework
- Mocke externe API-Calls mit unittest.mock
- Zielwert: >80% Test-Coverage

## Dokumentation
- Kommentiere komplexe Geschäftslogik
- Aktualisiere README.md bei Änderungen
- Dokumentiere neue MCP-Tools und Endpunkte

Siehe [Projektplan](../docs/PROJEKTPLAN.md) für Details.