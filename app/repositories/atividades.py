from sqlalchemy import select
from ..database import Activity, WeatherAssessment

def atividade_do_usuario(banco, atividade_id, usuario_id):
    return banco.scalar(select(Activity).where(Activity.id == atividade_id, Activity.usuario_id == usuario_id))

def avaliacoes_da_atividade(banco, atividade_id):
    return banco.scalars(select(WeatherAssessment).where(WeatherAssessment.atividade_id == atividade_id).order_by(WeatherAssessment.avaliado_em.desc()))
