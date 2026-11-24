"""Carga inicial do banco (idempotente)."""
import random
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from mongo_cursos.conexao import obter_banco
from mongo_cursos.validacao import criar_colecao_cursos

COLECOES = ("cursos", "alunos", "matriculas")

CATALOGO = {
    "Dados": [
        "Python para Análise de Dados", "SQL do Zero", "Power BI na Prática",
        "Estatística Aplicada", "Machine Learning Básico", "Engenharia de Dados",
    ],
    "Programação": [
        "Lógica de Programação", "JavaScript Moderno", "Java Orientado a Objetos",
        "APIs com FastAPI", "Git e GitHub", "Testes de Software",
    ],
    "Design": [
        "Figma Essencial", "UX Research", "UI para Aplicativos",
        "Teoria das Cores", "Tipografia Digital", "Design System",
    ],
    "Negócios": [
        "Gestão de Projetos", "Scrum na Prática", "Finanças para Iniciantes",
        "Empreendedorismo Digital", "Liderança de Equipes", "Excel para Negócios",
    ],
    "Marketing": [
        "Marketing Digital", "SEO na Prática", "Copywriting",
        "Mídias Sociais", "Tráfego Pago", "Marketing de Conteúdo",
    ],
}

TAGS = {
    "Dados": ["python", "sql", "pandas", "bi", "estatistica"],
    "Programação": ["backend", "frontend", "git", "api", "testes"],
    "Design": ["figma", "ux", "ui", "cores", "prototipo"],
    "Negócios": ["gestao", "agil", "financas", "lideranca", "excel"],
    "Marketing": ["seo", "conteudo", "redes-sociais", "anuncios", "copy"],
}

NIVEIS = ["iniciante", "intermediario", "avancado"]

INSTRUTORES = [
    {"nome": "Ana Lima", "email": "ana@aprendamais.com"},
    {"nome": "Bruno Costa", "email": "bruno@aprendamais.com"},
    {"nome": "Carla Souza", "email": "carla@aprendamais.com"},
    {"nome": "Diego Alves", "email": "diego@aprendamais.com"},
    {"nome": "Elisa Rocha", "email": "elisa@aprendamais.com"},
]

NOMES_ALUNOS = [
    "Bia Martins", "Davi Nunes", "Eva Ribeiro", "Gabriel Pires", "Helena Dias",
    "Igor Moura", "Julia Freitas", "Lucas Teixeira", "Marina Campos", "Nina Barros",
]


def gerar_modulos():
    modulos = []
    for ordem in range(1, random.randint(3, 20) + 1):
        aulas = [f"Aula {ordem}.{n}" for n in range(1, random.randint(2, 4) + 1)]
        modulos.append({"ordem": ordem, "titulo": f"Módulo {ordem}", "aulas": aulas})
    return modulos


def gerar_cursos():
    cursos = []
    for categoria, titulos in CATALOGO.items():
        for indice, titulo in enumerate(titulos):
            curso = {
                "_id": ObjectId(),
                "titulo": titulo,
                "categoria": categoria,
                "carga_horaria": random.choice([10, 20, 30, 40, 60]),
                "preco": round(random.uniform(49, 499), 2),
                # O último curso de cada categoria começa lotado
                "vagas": 0 if indice == len(titulos) - 1 else random.randint(10, 40),
                "tags": random.sample(TAGS[categoria], 2) + [random.choice(NIVEIS)],
                "instrutor": dict(random.choice(INSTRUTORES)),
                "modulos": gerar_modulos(),
            }
            # Campos opcionais: nem todo curso tem (flexibilidade do documento)
            if random.random() < 0.5:
                curso["certificado"] = True
            if random.random() < 0.25:
                curso["pre_requisitos"] = ["Lógica de Programação"]
            cursos.append(curso)
    return cursos


def gerar_alunos():
    agora = datetime.now(timezone.utc)
    alunos = []
    for nome in NOMES_ALUNOS:
        alunos.append({
            "_id": ObjectId(),
            "nome": nome,
            "email": f"{nome.split()[0].lower()}@example.com",
            "data_cadastro": agora - timedelta(days=random.randint(60, 365)),
        })
    return alunos


def gerar_matriculas(alunos, cursos, quantidade=30):
    # Cada par (aluno, curso) aparece uma única vez nesta lista
    pares = [(aluno, curso) for aluno in alunos for curso in cursos]
    random.shuffle(pares)

    matriculas = []
    for aluno, curso in pares:
        if len(matriculas) == quantidade:
            break
        if curso["vagas"] == 0:
            continue

        curso["vagas"] -= 1
        progresso = random.choice([10, 25, 40, 60, 80, 100, 100])

        concluida = progresso == 100

        matricula = {
            "aluno_id": aluno["_id"],
            "curso_id": curso["_id"],
            "data": aluno["data_cadastro"] + timedelta(days=random.randint(0, 59)),
            "progresso": progresso,
            "concluida": concluida,
        }
        if concluida:
            matricula["nota"] = random.randint(1, 5)
        matriculas.append(matricula)
    return matriculas


def criar_indices(banco):
    banco.get_collection("alunos").create_index("email", unique=True)

    banco.get_collection("matriculas").create_index(
        [("aluno_id", 1), ("curso_id", 1)], unique=True
    )


def popular(banco):
    criar_colecao_cursos(banco)
    criar_indices(banco)

    total = sum(banco.get_collection(nome).count_documents({}) for nome in COLECOES)
    if total > 0:
        print(f"Banco já populado ({total} documentos). Nada foi inserido.")
        return

    alunos = gerar_alunos()
    cursos = gerar_cursos()
    matriculas = gerar_matriculas(alunos, cursos)

    dados = {"cursos": cursos, "alunos": alunos, "matriculas": matriculas}
    for nome, documentos in dados.items():
        banco.get_collection(nome).insert_many(documentos)
        print(f"{nome}: {len(documentos)} documentos inseridos.")


if __name__ == "__main__":
    popular(obter_banco())
