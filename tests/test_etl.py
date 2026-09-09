import pytest
import pandas as pd
from etl import transform_city_weather, get_coordinates

def test_transform_city_weather_valid_data():
    """Vérifie que la transformation des données brutes en DataFrame est conforme."""
    fake_raw_data = {
        "latitude": 48.85,
        "longitude": 2.35,
        "hourly": {
            "time": ["2026-09-01T00:00", "2026-09-01T01:00"],
            "temperature_2m": [18.5, 17.8],
            "relative_humidity_2m": [65, 70],
            "wind_speed_10m": [12.0, 10.5]
        }
    }
    
    df = transform_city_weather(fake_raw_data, "Paris")
    
    # Vérifications de structure et de types
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "city" in df.columns
    assert "temperature_celsius" in df.columns
    assert df["city"].iloc[0] == "Paris"
    assert df["temperature_celsius"].iloc[0] == 18.5
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

def test_transform_city_weather_empty_data():
    """Vérifie le comportement en cas de données corrompues ou vides de l'API."""
    assert transform_city_weather(None, "Paris") is None
    assert transform_city_weather({}, "Paris") is None
    assert transform_city_weather({"latitude": 48.85}, "Paris") is None

def test_get_coordinates_mocked(mocker):
    """Teste le géocodage sans faire d'appel réseau réel (simulation requests)."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": [{"latitude": 45.76, "longitude": 4.83}]
    }
    mocker.patch("requests.get", return_value=mock_response)
    
    result = get_coordinates("Lyon")
    assert result == {"city": "Lyon", "lat": 45.76, "lon": 4.83}