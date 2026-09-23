from datetime import datetime
from enum import StrEnum
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from .controllers.atividades import listar_avaliacoes as buscar_avaliacoes
from .controllers.atividades import obter as obter_atividade
from .database import (Activity, Base, User, WeatherAssessment, engine, get_db,
                       migrar_esquema)
from .security import (create_token, decode_token, hash_password,
                       verify_password)
from .services.avaliacoes import criar as criar_avaliacao
from .weather_client import forecast
from .weather_score_service import score_weather

app = FastAPI(title="Serviço Planejador de Atividades ao Ar Livre")
security = HTTPBearer()
Db = Annotated[Session, Depends(get_db)]


class TipoAtividade(StrEnum):
    CORRIDA = "CORRIDA"
    CAMINHADA = "CAMINHADA"
    CICLISMO = "CICLISMO"
    TRILHA = "TRILHA"
    OUTRA = "OUTRA"


class Situacao(StrEnum):
    PLANEJADA = "PLANEJADA"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class Usuario(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str = Field(min_length=8)


class Credenciais(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class Atividade(BaseModel):
    titulo: str = Field(min_length=1)
    tipo_atividade: TipoAtividade
    data_agendada: datetime
    nome_local: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    observacoes: str | None = None
    situacao: Situacao = Situacao.PLANEJADA


class Atualizacao(BaseModel):
    titulo: str | None = Field(None, min_length=1)
    tipo_atividade: TipoAtividade | None = None
    data_agendada: datetime | None = None
    nome_local: str | None = Field(None, min_length=1)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    observacoes: str | None = None
    situacao: Situacao | None = None


def usuario_saida(x):
    return {
        k: getattr(x, k)
        for k in ("id", "nome", "email", "ativo", "criado_em")
    }


def atividade_saida(x):
    return {
        k: getattr(x, k)
        for k in (
            "id",
            "titulo",
            "tipo_atividade",
            "data_agendada",
            "nome_local",
            "latitude",
            "longitude",
            "observacoes",
            "situacao",
            "criado_em",
            "atualizado_em",
        )
    }


def avaliacao_saida(x):
    return {
        k: getattr(x, k)
        for k in (
            "id",
            "atividade_id",
            "temperatura_c",
            "probabilidade_precipitacao",
            "velocidade_vento_kmh",
            "codigo_tempo",
            "pontuacao",
            "classificacao",
            "recomendacao",
            "provedor",
            "avaliado_em",
        )
    }


def atual(
    c: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    b: Db,
):
    try:
        u = b.get(User, int(decode_token(c.credentials)["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Token inválido ou expirado.")

    if not u or not u.ativo:
        raise HTTPException(401, "Token inválido ou expirado.")

    return u


def proprietaria(
    atividade_id: int,
    u: Annotated[User, Depends(atual)],
    b: Db,
):
    x = obter_atividade(b, atividade_id, u.id)
    if not x:
        raise HTTPException(404, "Atividade não encontrada.")
    return x


@app.on_event("startup")
def iniciar():
    migrar_esquema()
    Base.metadata.create_all(engine)


@app.get("/saude")
def saude():
    return {"situacao": "ok"}


@app.post("/api/v1/auth/register", status_code=201)
def cadastrar(p: Usuario, b: Db):
    if b.scalar(select(User).where(User.email == str(p.email).lower())):
        raise HTTPException(409, "E-mail já cadastrado.")

    x = User(
        nome=p.nome.strip(),
        email=str(p.email).lower(),
        senha_hash=hash_password(p.senha),
    )
    b.add(x)
    b.commit()
    b.refresh(x)
    return usuario_saida(x)


@app.post("/api/v1/auth/login")
def entrar(p: Credenciais, b: Db):
    x = b.scalar(select(User).where(User.email == str(p.email).lower()))
    if not x or not x.ativo or not verify_password(p.senha, x.senha_hash):
        raise HTTPException(401, "E-mail ou senha inválidos.")

    return {
        "token_acesso": create_token(x.id, x.email),
        "tipo_token": "bearer",
        "expira_em": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/api/v1/auth/me")
def eu(u: Annotated[User, Depends(atual)]):
    return usuario_saida(u)


@app.post("/api/v1/atividades", status_code=201)
def criar(p: Atividade, u: Annotated[User, Depends(atual)], b: Db):
    if p.data_agendada < datetime.now(p.data_agendada.tzinfo):
        raise HTTPException(
            422, "A atividade deve ser agendada para o futuro."
        )

    x = Activity(usuario_id=u.id, **p.model_dump())
    b.add(x)
    b.commit()
    b.refresh(x)
    return atividade_saida(x)


@app.get("/api/v1/atividades")
def listar(
    u: Annotated[User, Depends(atual)],
    b: Db,
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    tipo_atividade: TipoAtividade | None = None,
    situacao: Situacao | None = None,
    ordenar_por: str = Query(
        "data_agendada",
        pattern="^(data_agendada|criado_em)$",
    ),
    ordem: str = Query("crescente", pattern="^(crescente|decrescente)$"),
):
    q = select(Activity).where(Activity.usuario_id == u.id)

    if tipo_atividade:
        q = q.where(Activity.tipo_atividade == tipo_atividade)
    if situacao:
        q = q.where(Activity.situacao == situacao)

    total = b.scalar(select(func.count()).select_from(q.subquery()))
    col = getattr(Activity, ordenar_por)
    q = (
        q.order_by(col.desc() if ordem == "decrescente" else col.asc())
        .offset((pagina - 1) * tamanho_pagina)
        .limit(tamanho_pagina)
    )

    return {
        "itens": [atividade_saida(x) for x in b.scalars(q)],
        "pagina": pagina,
        "tamanho_pagina": tamanho_pagina,
        "total": total,
    }


@app.get("/api/v1/atividades/{atividade_id}")
def obter(x: Annotated[Activity, Depends(proprietaria)]):
    return atividade_saida(x)


@app.put("/api/v1/atividades/{atividade_id}")
def atualizar(
    p: Atualizacao,
    x: Annotated[Activity, Depends(proprietaria)],
    b: Db,
):
    for k, v in p.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(x, k, v)

    b.commit()
    b.refresh(x)
    return atividade_saida(x)


@app.delete("/api/v1/atividades/{atividade_id}", status_code=204)
def excluir(x: Annotated[Activity, Depends(proprietaria)], b: Db):
    b.delete(x)
    b.commit()


@app.post("/api/v1/atividades/{atividade_id}/avaliacoes", status_code=201)
async def avaliar(x: Annotated[Activity, Depends(proprietaria)], b: Db):
    return avaliacao_saida(await criar_avaliacao(b, x))


@app.get("/api/v1/atividades/{atividade_id}/avaliacoes")
def avaliacoes(x: Annotated[Activity, Depends(proprietaria)], b: Db):
    return {
        "itens": [
            avaliacao_saida(a)
            for a in buscar_avaliacoes(b, x.id)
        ]
    }
