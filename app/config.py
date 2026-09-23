import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/outdoor_planner.db")
WEATHER_API_BASE_URL = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com")
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-real-environment-32")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
