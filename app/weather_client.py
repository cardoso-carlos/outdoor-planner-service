from dataclasses import dataclass
from datetime import datetime
import httpx
from fastapi import HTTPException
from .config import HTTP_TIMEOUT_SECONDS, WEATHER_API_BASE_URL

@dataclass
class WeatherData:
    temperature_c: float
    precipitation_probability: float
    wind_speed_kmh: float
    weather_code: int
    provider: str
    forecast_time: datetime

async def forecast(latitude: float, longitude: float, scheduled_at: datetime) -> WeatherData:
    days = (scheduled_at.date() - datetime.now(scheduled_at.tzinfo).date()).days + 1
    if days > 16 or days < 1:
        raise HTTPException(422, "A atividade está fora do período disponível para previsão meteorológica.")
    params = {"latitude": latitude, "longitude": longitude, "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m", "timezone": "auto", "forecast_days": days}
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{WEATHER_API_BASE_URL}/v1/forecast", params=params)
            response.raise_for_status(); hourly = response.json()["hourly"]
        target = scheduled_at.strftime("%Y-%m-%dT%H:00")
        index = hourly["time"].index(target)
        return WeatherData(float(hourly["temperature_2m"][index]), float(hourly["precipitation_probability"][index]), float(hourly["wind_speed_10m"][index]), int(hourly["weather_code"][index]), "Open-Meteo", scheduled_at)
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(503, "Não foi possível consultar as condições meteorológicas.")
