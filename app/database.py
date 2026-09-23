from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activities: Mapped[list["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "atividades"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    tipo_atividade: Mapped[str] = mapped_column(String(20))
    data_agendada: Mapped[datetime] = mapped_column(DateTime)
    nome_local: Mapped[str] = mapped_column(String(200))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    situacao: Mapped[str] = mapped_column(String(20), default="PLANEJADA")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="activities")
    assessments: Mapped[list["WeatherAssessment"]] = relationship(back_populates="activity", cascade="all, delete-orphan")

class WeatherAssessment(Base):
    __tablename__ = "avaliacoes_meteorologicas"
    id: Mapped[int] = mapped_column(primary_key=True)
    atividade_id: Mapped[int] = mapped_column(ForeignKey("atividades.id"), index=True)
    temperatura_c: Mapped[float] = mapped_column(Float)
    probabilidade_precipitacao: Mapped[float] = mapped_column(Float)
    velocidade_vento_kmh: Mapped[float] = mapped_column(Float)
    codigo_tempo: Mapped[int] = mapped_column(Integer)
    pontuacao: Mapped[int] = mapped_column(Integer)
    classificacao: Mapped[str] = mapped_column(String(20))
    recomendacao: Mapped[str] = mapped_column(Text)
    provedor: Mapped[str] = mapped_column(String(50))
    avaliado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activity: Mapped[Activity] = relationship(back_populates="assessments")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def migrar_esquema():
    """Mantém os bancos locais criados pela versão anterior utilizáveis."""
    tabelas = {"users": "usuarios", "activities": "atividades", "weather_assessments": "avaliacoes_meteorologicas"}
    colunas = {
        "usuarios": {"name": "nome", "password_hash": "senha_hash", "is_active": "ativo", "created_at": "criado_em", "updated_at": "atualizado_em"},
        "atividades": {"user_id": "usuario_id", "title": "titulo", "activity_type": "tipo_atividade", "scheduled_at": "data_agendada", "location_name": "nome_local", "notes": "observacoes", "status": "situacao", "created_at": "criado_em", "updated_at": "atualizado_em"},
        "avaliacoes_meteorologicas": {"activity_id": "atividade_id", "temperature_c": "temperatura_c", "precipitation_probability": "probabilidade_precipitacao", "wind_speed_kmh": "velocidade_vento_kmh", "weather_code": "codigo_tempo", "score": "pontuacao", "classification": "classificacao", "recommendation": "recomendacao", "provider": "provedor", "evaluated_at": "avaliado_em"},
    }
    with engine.begin() as conexao:
        existentes = set(inspect(conexao).get_table_names())
        for antiga, nova in tabelas.items():
            if antiga in existentes and nova not in existentes: conexao.execute(text(f"ALTER TABLE {antiga} RENAME TO {nova}"))
        for tabela, mapa in colunas.items():
            if tabela in inspect(conexao).get_table_names():
                existentes = {coluna["name"] for coluna in inspect(conexao).get_columns(tabela)}
                for antiga, nova in mapa.items():
                    if antiga in existentes and nova not in existentes: conexao.execute(text(f"ALTER TABLE {tabela} RENAME COLUMN {antiga} TO {nova}"))
