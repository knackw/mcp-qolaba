# Dokumentations-Styleguide & Glossar

Dieser Styleguide definiert Sprach- und Formatregeln für die Projektdokumentation.

## Sprache
- Primärsprache: Deutsch (DE). Englische Fachbegriffe sind zulässig, wenn etabliert.
- Einheitliche Terminologie verwenden (siehe Glossar).
- Aktive Sprache, kurze Sätze, klare Anweisungen.

## Struktur
- Überschriften-Hierarchie ab `##` (H2) beginnen.
- Pro Seite: kurze Einleitung, dann Aufgaben/Steps, dann „Nächste Schritte“.
- Codebeispiele vollständig und testbar, mit Sprache-Tag versehen.

## Formatierung
- Datei-/Klassen-/Funktionsnamen in Backticks (`like_this`).
- URLs als Markdown-Links mit sprechendem Text.
- Tabellen nur bei Mehrvergleich; sonst Listen.

## Glossar (Auszug)
- MCP: Model Context Protocol
- Orchestrator: Zentrale Geschäftslogik (`core/business_logic.py`)
- HTTP-Client: `QolabaHTTPClient` in `api/client.py`
- Settings: `QolabaSettings` in `config/settings.py`

## Schreibregeln für API-Beispiele
- Erfolgs- und Fehlerantwort zeigen.
- Parameter mit Typ und Grenzen dokumentieren.
- Auth-Hinweis (API-Key/OAuth) bei jedem Endpoint.

## Versionsangaben
- Pydantic: v1 (root_validator). Pydantic v2 ist optionales Vorhaben.
- Python: 3.11+

## Checkliste vor Merge
- [ ] Sprache konsistent (DE)
- [ ] Links funktionieren
- [ ] Codebeispiele laufen
- [ ] Terminologie entspricht Glossar
