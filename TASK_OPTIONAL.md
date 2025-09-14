# Optionale Aufgaben (nicht-blockierend)

Diese Aufgaben sind nicht zwingend für die Funktionsfähigkeit. Sie erhöhen Wartbarkeit, DX und Zukunftssicherheit. Aufwandsschätzungen sind grob.

## 1) Typing-Schulden reduzieren (hoch)
- Beschreibung: Fehlende/lockere Type-Hints schließen, mypy-Basisverschärfung.
- Fokus: `src/qolaba_mcp_server/api/client.py`, `core/business_logic.py`, `config/settings.py`, danach `models/*` und `core/*`.
- Schritte:
  - [x] Rückgabe- und Parameter-Typen ergänzen (api/client.py, core/business_logic.py)
  - [x] Rückgabe- und Parameter-Typen ergänzen (config/settings.py)
  - [x] Rückgabe- und Parameter-Typen ergänzen (models/* Validatoren)
  - [x] Rückgabe- und Parameter-Typen ergänzen (weitere core/* bei Bedarf)
  - [x] Typen in `core/logging_config.py`/`core/metrics.py` für öffentliche Methoden ergänzt
  - [x] mypy-Warnungen abbauen; per-file-overrides reduzieren (Entfernung unnötiger ignores)
  - [x] mypy-Regeln schrittweise strenger machen (disallow_untyped_calls aktiviert)
- Aufwand: 4–8 Stunden

## 2) Pydantic v2 + pydantic-settings evaluieren (mittel)
- Beschreibung: Migration von v1-Patterns (`root_validator`) auf v2 (`model_post_init`); Settings mit `pydantic-settings`.
- Schritte:
  - [x] Evaluations-Branch anlegen
  - [x] `config/settings.py` auf `BaseSettings` (v2) umstellen
  - [x] Validatoren auf v2-Hook (`model_post_init`) migrieren
  - [x] Doku anpassen (AUTHENTICATION_PLAN, README Hinweis)
- Aufwand: 0,5–1,5 Tage

## 3) Pre-commit Hooks einführen (mittel)
- Beschreibung: `.pre-commit-config.yaml` mit `black`, `flake8`, `mypy` (optional `ruff`).
- Schritte:
  - [x] Konfiguration hinzufügen und `pre-commit install`
  - [x] README-Hinweis ergänzen
- Aufwand: 0,5–1 Stunden

## 4) Doku-Konsistenz & Sprache vereinheitlichen (mittel)
- Beschreibung: DE/EN-Mix konsistent; Glossar/Terminologie zentralisieren.
- Schritte:
  - [x] Seiten mit gemischter Sprache harmonisieren (Styleguide hinzugefügt)
  - [x] Glossar/Styleguide-Hinweis ergänzen (README verlinkt)
- Aufwand: 1–2 Stunden

## 5) MCP-Tool-Beispiele erweitern (mittel)
- Beschreibung: Je Tool kurzes Request/Response-Beispiel inkl. Felder.
- Schritte:
  - [x] `text_to_image`, `image_to_image`, `inpainting`, `replace_background`
  - [x] `text_to_speech`, `chat`, `store_file_in_vector_db`, `get_task_status`
- Aufwand: 2–4 Stunden

## 6) Smoke-Tests / E2E-Minicheck (niedrig)
- Beschreibung: Minimaler Start-/Health-Check-Test (Start via `python -m qolaba_mcp_server`, Tool `server_health`).
- Schritte:
  - [x] Testskript ergänzen
  - [x] Optional CI-Step hinzufügen
- Aufwand: ~1 Stunde

## 7) Security & Qualität (niedrig)
- Beschreibung: Optional CodeQL-Analyse ergänzen (Bandit existiert bereits).
- Schritte:
  - [x] CodeQL-Workflow hinzufügen
- Aufwand: ~1 Stunde

## 8) Docker & Build-Optimierung (niedrig)
- Beschreibung: Multi-Stage-Build optimieren, optional Hadolint-Check.
- Schritte:
  - [x] Multi-Stage-Optimierung (Python 3.11, install flow korrigiert)
  - [x] Hadolint in CI (optional)
- Aufwand: 1–2 Stunden

## 9) Logging/Observability verfeinern (niedrig)
- Beschreibung: Correlation-IDs/Request-IDs durchgängig, `structlog`-Setup vereinheitlichen.
- Schritte:
  - [x] Request-ID überall durchreichen (Client → Orchestrator → Tools)
  - [x] Zentrales Logging-Setup
- Aufwand: 1–2 Stunden

## 10) Retry-/Rate-Limit-Tests ausbauen (niedrig)
- Beschreibung: Tests für 429/`Retry-After`, 401→OAuth-Refresh, Jitter/Backoff.
- Schritte:
  - [x] 429/`Retry-After`-Pfad testen
  - [x] OAuth-Refresh bei 401 testen
- Aufwand: 1–2 Stunden
