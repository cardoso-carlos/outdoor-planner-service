def score_weather(temperature_c: float, precipitation_probability: float, wind_speed_kmh: float) -> tuple[int, str, str]:
    score = 100
    score -= 35 if temperature_c < 5 or temperature_c > 35 else 15 if temperature_c < 12 or temperature_c >= 30 else 0
    score -= 35 if precipitation_probability >= 80 else 20 if precipitation_probability >= 50 else 10 if precipitation_probability >= 30 else 0
    score -= 35 if wind_speed_kmh >= 50 else 20 if wind_speed_kmh >= 30 else 10 if wind_speed_kmh >= 20 else 0
    score = max(0, min(100, score))
    if score >= 70: return score, "RECOMENDADO", "Condições favoráveis para a atividade planejada."
    if score >= 40: return score, "ATENCAO", "Planeje-se com atenção às condições meteorológicas."
    return score, "NAO_RECOMENDADO", "Condições desfavoráveis para a atividade planejada."
