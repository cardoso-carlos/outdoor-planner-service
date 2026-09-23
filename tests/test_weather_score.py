from app.weather_score_service import score_weather

def test_weather_score_boundaries():
    assert score_weather(20, 0, 0)[:2] == (100, "RECOMENDADO")
    assert score_weather(36, 80, 50)[:2] == (0, "NAO_RECOMENDADO")
