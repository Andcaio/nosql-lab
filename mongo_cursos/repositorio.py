"""Operações CRUD do catálogo."""
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from mongo_cursos.conexao import obter_banco

banco = obter_banco()
cursos = banco.get_collection("cursos")
alunos = banco.get_collection("alunos")
matriculas = banco.get_collection("matriculas")


def buscar_cursos(categoria=None, preco_max=None, tag=None):
    filtro = {}
    if categoria is not None:
        filtro["categoria"] = categoria
    if preco_max is not None:
        filtro["preco"] = {"$lte": preco_max}
    if tag is not None:
        filtro["tags"] = tag

    projecao = {"modulos": 0}
    return list(cursos.find(filtro, projecao))


def adicionar_modulo(curso_id, modulo):
    resultado = cursos.update_one(
        {"_id": ObjectId(curso_id)},
        {"$push": {"modulos": modulo}},
    )
    return resultado.matched_count == 1


def atualizar_progresso(matricula_id, progresso):
    if not 0 <= progresso <= 100:
        raise ValueError("O progresso deve estar entre 0 e 100.")

    atualizacao = {
        "$set": {
            "progresso": progresso,
            "concluida": progresso == 100,
        }
    }
    # Se a matrícula deixou de estar concluída, a nota não vale mais
    if progresso < 100:
        atualizacao["$unset"] = {"nota": ""}

    resultado = matriculas.update_one({"_id": ObjectId(matricula_id)}, atualizacao)
    return resultado.matched_count == 1


def remover_aluno(aluno_id):
    aluno_id = ObjectId(aluno_id)
    cursos_do_aluno = matriculas.distinct("curso_id", {"aluno_id": aluno_id})

    removidas = matriculas.delete_many({"aluno_id": aluno_id})

    # Cada matrícula removida devolve uma vaga ao curso
    if cursos_do_aluno:
        cursos.update_many({"_id": {"$in": cursos_do_aluno}}, {"$inc": {"vagas": 1}})

    resultado = alunos.delete_one({"_id": aluno_id})
    return resultado.deleted_count == 1, removidas.deleted_count


def matricular(aluno_id, curso_id):
    aluno_id, curso_id = ObjectId(aluno_id), ObjectId(curso_id)
    if alunos.count_documents({"_id": aluno_id}) == 0:
        raise ValueError("Aluno não encontrado.")
    if matriculas.count_documents({"aluno_id": aluno_id, "curso_id": curso_id}) > 0:
        raise ValueError("O aluno já está matriculado neste curso.")

    # Busca e altera em UM comando: só encontra o curso se ainda houver vaga
    curso = cursos.find_one_and_update(
        {"_id": curso_id, "vagas": {"$gt": 0}},
        {"$inc": {"vagas": -1}},
    )
    if curso is None:
        raise ValueError("Curso não encontrado ou sem vagas.")

    try:
        resultado = matriculas.insert_one({
            "aluno_id": aluno_id,
            "curso_id": curso_id,
            "data": datetime.now(timezone.utc),
            "progresso": 0,
            "concluida": False,
        })
    except DuplicateKeyError:
        # Outra matrícula igual entrou ao mesmo tempo: devolve a vaga
        cursos.update_one({"_id": curso_id}, {"$inc": {"vagas": 1}})
        raise ValueError("O aluno já está matriculado neste curso.")
    return resultado.inserted_id


def avaliar(matricula_id, nota):
    if not 1 <= nota <= 5:
        raise ValueError("A nota deve ser de 1 a 5.")

    resultado = matriculas.update_one(
        {"_id": ObjectId(matricula_id), "concluida": True},
        {"$set": {"nota": nota}},
    )
    return resultado.matched_count == 1


if __name__ == "__main__":
    encontrados = buscar_cursos(categoria="Dados", preco_max=500)
    print(f"Cursos de Dados até R$ 500: {len(encontrados)}")
    print(f"Algum veio com módulos? {any('modulos' in c for c in encontrados)}")
