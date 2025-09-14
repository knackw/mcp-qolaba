<div align="center">

<!-- omit in toc -->
# Qolaba API MCP Server 🚀

<strong>Robuster MCP-Server für die Qolaba-API Integration</strong>

*Entwickelt mit FastMCP Framework*

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastMCP](https://img.shields.io/badge/framework-FastMCP_v2-green.svg)](https://gofastmcp.com)
[![License](https://img.shields.io/github/license/jlowin/fastmcp.svg)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)](./tests)

</div>

> [!Important]
>
> #### Qolaba API MCP Server
>
> Dieser MCP-Server fungiert als robuste Brücke zwischen dem Model Context Protocol und der [Qolaba-API](https://docs.qolaba.ai/api-platform).
>
> **Kernfunktionen:**
> - Sichere API-Authentifizierung und Credential-Management
> - Robuste Fehlerbehandlung mit Retry-Mechanismen
> - Asynchrone Request-Verarbeitung für optimale Performance
> - Umfassende Datenvalidierung mit Pydantic-Modellen
> - Produktionsreife Containerisierung mit Docker
>
> Der Server basiert auf dem [FastMCP Framework v2](https://gofastmcp.com) und folgt modernen Python-Entwicklungsstandards.

---

Dieser MCP-Server ermöglicht die nahtlose Integration der [Qolaba-API](https://docs.qolaba.ai/api-platform) in MCP-kompatible Anwendungen. Mit sauberer, Pythonischer Code-Architektur bietet er eine zuverlässige und erweiterbare Lösung für API-Interaktionen.

```python
# server.py (vereinfacht)
from fastmcp import FastMCP
from qolaba_mcp_server.api.client import QolabaHTTPClient
from qolaba_mcp_server.config import get_settings

mcp = FastMCP("Qolaba API Server 🚀")
settings = get_settings()

@mcp.tool
async def pricing() -> dict:
    async with QolabaHTTPClient(settings) as client:
        res = await client.get("pricing")
    return res.content if isinstance(res.content, dict) else {"status": res.status_code}

if __name__ == "__main__":
    mcp.run()
```

## 🚀 Schnellstart

### Lokale Entwicklung

```bash
# Repository klonen
git clone <repository-url>
cd mcp-qolaba

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder: .venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -e .

# Umgebungsvariablen konfigurieren
cp .env.example .env
# API-Schlüssel in .env eintragen

# Server starten (benötigt Python 3.11+)
python -m qolaba_mcp_server
```

### Docker Deployment

```bash
# Docker Image erstellen
docker build -t qolaba-mcp-server .

# Container starten
docker run -p 8000:8000 --env-file .env qolaba-mcp-server
```

## 📚 Dokumentation

Die vollständige Projektdokumentation finden Sie in:

- **[Projektplan](./docs/PROJEKTPLAN.md)** - Übergeordnete Projektziele und Phasen
- **[Aufgabenplan](./docs/PLAN.md)** - Detaillierte Implementierungsschritte
- **[FastMCP Dokumentation](https://gofastmcp.com)** - Framework-Referenz
- **[Qolaba API Docs](https://docs.qolaba.ai/api-platform)** - API-Referenz
- **[Troubleshooting](./docs/development/TROUBLESHOOTING.md)** - Häufige Fehler und Lösungen
 - **[Styleguide & Glossar](./docs/development/STYLEGUIDE.md)** - Sprach- und Formatregeln
 - **[Tool-Beispiele](./docs/snippets/qolaba_tools_examples.mdx)** - Requests/Responses für MCP-Tools

---

## 📋 Inhaltsverzeichnis

- [🏗️ Architektur](#️-architektur)
- [⚙️ Konfiguration](#️-konfiguration)
- [🛠️ Verfügbare Tools](#️-verfügbare-tools)
- [🔧 Entwicklung](#-entwicklung)
- [🧪 Testing](#-testing)
- [🐳 Deployment](#-deployment)
- [📊 Monitoring](#-monitoring)
- [🤝 Mitwirken](#-mitwirken)

---

## 🏗️ Architektur

Der Qolaba MCP Server folgt einer modularen Architektur:

```
src/qolaba_mcp_server/
├── api/          # Qolaba API Client und HTTP-Handling
├── mcp/          # MCP-spezifische Handler und Endpunkte
├── config/       # Konfigurationsmanagement und Settings
├── models/       # Pydantic-Datenmodelle
└── utils/        # Hilfsfunktionen und Utilities
```

### Kernkomponenten

- **API Client**: Abstrahiert die Qolaba-API-Kommunikation
- **MCP Handler**: Verarbeitet MCP-Protokoll-Nachrichten
- **Config Manager**: Verwaltet Umgebungsvariablen und API-Credentials
- **Data Models**: Validiert und serialisiert Daten mit Pydantic

## ⚙️ Konfiguration

### Umgebungsvariablen

```bash
# .env Datei
QOLABA_API_KEY=your_api_key_here
QOLABA_API_BASE_URL=https://api.qolaba.ai/v1
LOG_LEVEL=INFO
RETRY_MAX_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2.0
```

Hinweis: Die Settings nutzen pydantic-settings mit Prefix `QOLABA_`. Typische Variablen:
- `QOLABA_ENV` (z. B. development/test/staging/production)
- `QOLABA_API_BASE_URL`, `QOLABA_API_KEY`
- `QOLABA_CLIENT_ID`, `QOLABA_CLIENT_SECRET`, `QOLABA_TOKEN_URL`, `QOLABA_SCOPE`
- `QOLABA_TIMEOUT`, `QOLABA_VERIFY_SSL`
- `QOLABA_HTTP_PROXY`, `QOLABA_HTTPS_PROXY`

### Konfigurationsdatei

```python
# Konfiguration (vereinfacht)
from qolaba_mcp_server.config import get_settings

settings = get_settings()  # lädt Werte aus Umgebungsvariablen/.env
print(settings.redacted_dict())
```

## 🛠️ Verfügbare Tools

Der MCP-Server stellt folgende Tools zur Verfügung:

### `qolaba_query`
```python
@mcp.tool
async def qolaba_query(query: str) -> dict:
    """Execute a query via Qolaba API"""
```

### `qolaba_analyze`
```python
@mcp.tool
async def qolaba_analyze(data: dict) -> dict:
    """Analyze data using Qolaba AI capabilities"""
```

## 🔧 Entwicklung

### Voraussetzungen

- Python 3.11+
- Git
- Docker (optional)

### Setup der Entwicklungsumgebung

```bash
# Repository klonen
git clone <repository-url>
cd mcp-qolaba

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate

# Entwicklungsabhängigkeiten installieren
pip install -e ".[dev]"

# Pre-commit hooks einrichten
pre-commit install
```

## 🧪 Testing

```bash
# Unit-Tests ausführen
pytest tests/unit/

# Integrationstests ausführen
pytest tests/integration/

# Tests mit Coverage
pytest --cov=qolaba_mcp_server --cov-report=html

# Linting und Code-Qualität
black src/ tests/
flake8 src/ tests/
mypy src/
```

## 🧩 Troubleshooting

For common issues (including the JetBrains 400 error about missing tool names), see the Troubleshooting guide: [docs/development/TROUBLESHOOTING.md](./docs/development/TROUBLESHOOTING.md).

## 🐳 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["python", "-m", "qolaba_mcp_server"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  qolaba-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QOLABA_API_KEY=${QOLABA_API_KEY}
    restart: unless-stopped
```

## 📊 Monitoring

Der Server bietet integrierte Monitoring-Funktionen:

- **Health Check**: `/health` Endpunkt
- **Metriken**: Prometheus-kompatible Metriken
- **Strukturiertes Logging**: JSON-Format für zentrale Aggregation

### Logging-Konfiguration

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
```

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte beachten Sie:

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/neues-feature`)
3. Änderungen committen (`git commit -am 'Neues Feature hinzugefügt'`)
4. Branch pushen (`git push origin feature/neues-feature`)
5. Pull Request erstellen

### Code-Standards

- Befolgen Sie PEP 8
- Verwenden Sie Type Hints
- Schreiben Sie Tests für neue Funktionen
- Dokumentieren Sie API-Änderungen

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](./LICENSE) für Details.

## 🆘 Support

- **Issues**: [GitHub Issues](../../issues)
- **Diskussionen**: [GitHub Discussions](../../discussions)
- **Dokumentation**: [Projektdokumentation](./docs/)

---

*Entwickelt mit ❤️ und dem FastMCP Framework*

