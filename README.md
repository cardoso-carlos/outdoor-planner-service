# Outdoor Planner Service

API secundária do Planejador de Atividades ao Ar Livre. Concentra autenticação JWT, hash Argon2, regras de negócio, SQLite e integração com Open-Meteo. O acesso público ocorre pelo gateway.

## Instalação local

Pré-requisito: Python 3.12+.

```bash
cd outdoor-planner-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Swagger local: http://localhost:8001/docs.

## Docker

Normalmente o serviço é iniciado pelo Compose no gateway. Para construir isoladamente:

```bash
docker build -t outdoor-planner-service .
docker run -p 8001:8001 outdoor-planner-service
```

## Responsabilidades

- Usuários, Argon2 e JWT.
- Isolamento das atividades por usuário.
- SQLite e histórico de avaliações.
- Previsão horária e pontuação de 0 a 100.

## Dados meteorológicos

Provider: Open-Meteo  
Website: https://open-meteo.com/  
License: CC BY 4.0

As avaliações são informativas e não são garantia de segurança.
