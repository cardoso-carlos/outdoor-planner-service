from ..repositories.atividades import (atividade_do_usuario,
                                       avaliacoes_da_atividade)


def obter(banco, atividade_id, usuario_id): 
    return atividade_do_usuario(banco, atividade_id, usuario_id)

def listar_avaliacoes(banco, atividade_id): 
    return avaliacoes_da_atividade(banco, atividade_id)
