import requests

BASE_URL = "https://cuaca.bmkg.go.id/api/df/v1/forecast"

def get_forecast(lat: float, lon: float):
    """
    Ambil prakiraan cuaca BMKG ISDP berbasis koordinat.
    lat, lon : float
    return: dict | None
    """
    url = f"{BASE_URL}/point?lat={lat}&lon={lon}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] {e}")
        return None
