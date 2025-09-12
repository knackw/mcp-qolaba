# Prompt zur Implementierung einer spezifischen Entwicklungsaufgabe

**Ziel:** Schreibe den Python-Code zur Implementierung einer spezifischen Aufgabe aus dem Projektplan des "Qolaba API MCP Server".

**Kontext:** Du bist ein Full-Stack-Entwickler und arbeitest an der Umsetzung des [Qolaba-Projektplans](docs/PROJEKTPLAN.md).

**Anweisungen:**

1.  **Wähle eine Aufgabe:** Wähle eine konkrete, technische Aufgabe aus der Aufgabenliste (z.B. "Task 2.3 (API-Client): Implementiere eine Methode `get_data(endpoint: str)` mit Fehlerbehandlung für HTTP-Statuscodes").

2.  **Analysiere die Anforderungen:**
    *   Die Methode soll einen `endpoint` als String entgegennehmen.
    *   Sie soll eine GET-Anfrage an die Qolaba-API senden (die Basis-URL kommt aus der Konfiguration).
    *   Sie muss den API-Key im Header der Anfrage mitsenden.
    *   Sie muss auf Fehler-Statuscodes (4xx, 5xx) reagieren und eine entsprechende Exception auslösen.
    *   Bei Erfolg soll sie die JSON-Antwort der API zurückgeben.

3.  **Schreibe den Code:** Implementiere die Methode in Python unter Verwendung der `httpx`-Bibliothek (oder einer anderen geeigneten Bibliothek, die im Projekt verwendet wird).

4.  **Füge Kommentare hinzu:** Kommentiere den Code, um die Logik zu erklären, insbesondere die Fehlerbehandlung.

5.  **Beispiel-Code-Struktur:**

    ```python
    import httpx
    from .config import settings # Annahme: Konfiguration wird so geladen

    class QolabaAPIClient:
        def __init__(self):
            self.api_key = settings.QOLABA_API_KEY
            self.base_url = "https://api.qolaba.ai/v1" # Beispiel

        def get_data(self, endpoint: str) -> dict:
            """
            Führt eine GET-Anfrage an einen Endpunkt der Qolaba-API aus.

            Args:
                endpoint: Der API-Endpunkt (z.B. "/status").

            Returns:
                Die JSON-Antwort als Dictionary.

            Raises:
                httpx.HTTPStatusError: Wenn die API einen Fehler-Statuscode zurückgibt.
            """
            headers = {"Authorization": f"Bearer {self.api_key}"}
            with httpx.Client(base_url=self.base_url, headers=headers) as client:
                response = client.get(endpoint)
                response.raise_for_status()  # Löst eine Exception bei 4xx/5xx aus
                return response.json()
    ```