"""Relatórios do painel da coordenação."""
from mongo_cursos.conexao import obter_banco

banco = obter_banco()
cursos = banco.get_collection("cursos")
matriculas = banco.get_collection("matriculas")


def avaliacao_media_por_curso():
    """Relatório 1: cursos mais bem avaliados."""
    return list(matriculas.aggregate([
        {"$match": {"nota": {"$exists": True}}},
        {"$group": {
            "_id": "$curso_id",
            "media": {"$avg": "$nota"},
            "avaliacoes": {"$sum": 1},
        }},
        {"$sort": {"media": -1, "avaliacoes": -1}},
        {"$lookup": {
            "from": "cursos", "localField": "_id", "foreignField": "_id", "as": "curso",
        }},
        {"$unwind": "$curso"},
        {"$project": {
            "_id": 0, "titulo": "$curso.titulo",
            "media": {"$round": ["$media", 2]}, "avaliacoes": 1,
        }},
    ]))


def matriculas_por_categoria():
    """Relatório 2: total de matrículas e concluídas em cada categoria."""
    return list(matriculas.aggregate([
        {"$lookup": {
            "from": "cursos", "localField": "curso_id", "foreignField": "_id", "as": "curso",
        }},
        {"$unwind": "$curso"},
        {"$group": {
            "_id": "$curso.categoria",
            "total": {"$sum": 1},
            "concluidas": {"$sum": {"$cond": ["$concluida", 1, 0]}},
        }},
        {"$sort": {"total": -1}},
    ]))


def ocupacao_dos_cursos(limite=10):
    """Relatório 3: cursos com mais alunos e as vagas que restam."""
    return list(cursos.aggregate([
        {"$lookup": {
            "from": "matriculas", "localField": "_id", "foreignField": "curso_id",
            "as": "inscritos",
        }},
        {"$project": {
            "_id": 0, "titulo": 1, "vagas_restantes": "$vagas",
            "alunos": {"$size": "$inscritos"},
        }},
        {"$sort": {"alunos": -1, "titulo": 1}},
        {"$limit": limite},
    ]))


def imprimir_relatorios():
    print("\n== Relatório 1: avaliação média por curso ==")
    for linha in avaliacao_media_por_curso():
        print(f"{linha['titulo']}: {linha['media']} ({linha['avaliacoes']} avaliação(ões))")

    print("\n== Relatório 2: matrículas por categoria ==")
    for linha in matriculas_por_categoria():
        print(f"{linha['_id']}: {linha['total']} matrículas, {linha['concluidas']} concluídas")

    print("\n== Relatório 3: cursos com mais alunos ==")
    for linha in ocupacao_dos_cursos():
        print(f"{linha['titulo']}: {linha['alunos']} alunos, {linha['vagas_restantes']} vagas restantes")


if __name__ == "__main__":
    imprimir_relatorios()
