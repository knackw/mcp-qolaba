# Qolaba MCP Server Entwicklungsrichtlinien

> **Zielgruppe**: LLM-gestützte Engineering-Agenten und menschliche Entwickler

Der Qolaba MCP Server ist ein robuster Python-basierter (Python ≥3.11) MCP-Server, der als Brücke zur Qolaba-API fungiert. Entwickelt mit dem FastMCP v2.0 Framework für optimale Performance und Wartbarkeit.

## Erforderlicher Entwicklungs-Workflow

**KRITISCH**: Führen Sie diese Befehle immer in Reihenfolge vor dem Commit aus:

```bash
# Abhängigkeiten installieren
pip install -e ".[dev]"

# Code-Qualität prüfen
black src/ tests/                    # Code-Formatierung
flake8 src/ tests/                   # Linting
mypy src/                           # Type-Checking

# Tests ausführen
pytest --cov=qolaba_mcp_server      # Unit-Tests mit Coverage
pytest tests/integration/           # Integrationstests
```

**Alle Schritte müssen erfolgreich sein** - dies wird durch CI/CD durchgesetzt.

**Tests müssen bestehen und Code-Qualität muss sauber sein vor dem Commit.**

## Repository-Struktur

| Pfad                               | Zweck                                                 |
| ---------------------------------- | ----------------------------------------------------- |
| `src/qolaba_mcp_server/`          | Qolaba MCP Server Quellcode (Python ≥ 3.11)         |
| `├─api/`                          | Qolaba API Client und HTTP-Request-Handling          |
| `├─mcp/`                          | MCP-Handler, Tools und Endpunkt-Definitionen         |
| `├─config/`                       | Konfigurationsmanagement und Settings                |
| `├─models/`                       | Pydantic-Datenmodelle für API-Requests/Responses     |
| `└─utils/`                        | Hilfsfunktionen und Utilities                        |
| `tests/unit/`                     | Unit-Tests für einzelne Komponenten                  |
| `tests/integration/`              | Integrationstests für End-to-End-Szenarien           |
| `docs/`                           | Projektdokumentation und Pläne                       |

## Entwicklungsphilosophie

### Sicherheit
- **Keine Credentials im Code**: API-Schlüssel und sensible Daten nur über Umgebungsvariablen
- **Sichere Konfiguration**: Pydantic Settings mit Validierung
- **Robuste Fehlerbehandlung**: Umfassende Exception-Behandlung und Logging

### Code-Qualität
- **Type Safety**: Vollständige Type-Hints für alle Funktionen
- **Async/Await**: Asynchrone I/O für optimale Performance
- **Pydantic Models**: Strenge Datenvalidierung und Serialisierung
- **Modular Design**: Klare Trennung von Verantwortlichkeiten

### Testing
- **Test-Driven Development**: Tests vor oder parallel zur Implementierung
- **Mocking**: Externe API-Calls werden gemockt für zuverlässige Tests
- **Coverage**: Mindestens 80% Testabdeckung für kritische Module
- **Integration Tests**: End-to-End-Tests für vollständige Workflows
