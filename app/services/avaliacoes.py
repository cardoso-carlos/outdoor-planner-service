from ..database import WeatherAssessment
from ..weather_client import forecast
from ..weather_score_service import score_weather


async def criar(banco, atividade):
    tempo = await forecast(atividade.latitude, atividade.longitude, atividade.data_agendada)
    pontuacao, classificacao, recomendacao = score_weather(tempo.temperature_c, tempo.precipitation_probability, tempo.wind_speed_kmh)
    avaliacao = WeatherAssessment(atividade_id=atividade.id, temperatura_c=tempo.temperature_c, probabilidade_precipitacao=tempo.precipitation_probability, velocidade_vento_kmh=tempo.wind_speed_kmh, codigo_tempo=tempo.weather_code, pontuacao=pontuacao, classificacao=classificacao, recomendacao=recomendacao, provedor=tempo.provider)
    banco.add(avaliacao); banco.commit(); banco.refresh(avaliacao)
    return avaliacao
