import requests

class SchedulerAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_schedule(self, payload: dict) -> dict:
        """Sends the JSON payload to the FastAPI backend."""
        try:
            response = requests.post(f"{self.base_url}/schedule", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}