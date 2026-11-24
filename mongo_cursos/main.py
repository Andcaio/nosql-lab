"""Menu de terminal da plataforma Aprenda+."""
from mongo_cursos import repositorio as repo
from mongo_cursos.relatorios import imprimir_relatorios


def ler_texto(texto):
    return input(texto).strip() or None


def ler_numero(texto, converter=float, obrigatorio=False):
    valor = input(texto).strip().replace(",", ".")
    if not valor:
        if obrigatorio:
            raise ValueError("Este valor é obrigatório.")
        return None
    try:
        return converter(valor)
    except ValueError:
        raise ValueError(f"Número inválido: {valor}") from None


def escolher(itens, descrever):
    if not itens:
        raise ValueError("Nada encontrado.")
    for numero, item in enumerate(itens, 1):
        print(f"  {numero}. {descrever(item)}")
    numero = ler_numero("Número: ", int, obrigatorio=True)
    if not 1 <= numero <= len(itens):
        raise ValueError("Número fora da lista.")
    return itens[numero - 1]


def escolher_aluno():
    print("\nAlunos:")
    lista = list(repo.alunos.find().sort("nome", 1))
    return escolher(lista, lambda a: f"{a['nome']} ({a['email']})")


def escolher_curso():
    categoria = ler_texto("Categoria (Enter para todas): ")
    print("\nCursos:")
    lista = repo.buscar_cursos(categoria=categoria)
    return escolher(lista, lambda c: f"{c['titulo']} - {c['vagas']} vagas")


def descrever_matricula(matricula, titulos):
    situacao = "concluída" if matricula["concluida"] else "em andamento"
    nota = f", nota {matricula['nota']}" if "nota" in matricula else ""
    titulo = titulos.get(matricula["curso_id"], "?")
    return f"{titulo} - {matricula['progresso']}% ({situacao}{nota})"


def escolher_matricula(aluno):
    lista = list(repo.matriculas.find({"aluno_id": aluno["_id"]}))
    ids_cursos = [m["curso_id"] for m in lista]

    cursos = repo.cursos.find({"_id": {"$in": ids_cursos}}, {"titulo": 1})
    titulos = {c["_id"]: c["titulo"] for c in cursos}

    print("\nMatrículas:")
    return escolher(lista, lambda m: descrever_matricula(m, titulos))


def opcao_buscar():
    print("\nDeixe em branco o filtro que não quiser usar.")
    categoria = ler_texto("Categoria: ")
    preco_max = ler_numero("Preço máximo: ")
    tag = ler_texto("Tag: ")

    encontrados = repo.buscar_cursos(categoria=categoria, preco_max=preco_max, tag=tag)
    print(f"\n{len(encontrados)} curso(s) encontrado(s):")
    for c in encontrados:
        tags = ", ".join(c["tags"])
        print(f"  {c['titulo']} | {c['categoria']} | R$ {c['preco']:.2f} | {c['vagas']} vagas | {tags}")


def opcao_matricular():
    aluno = escolher_aluno()
    curso = escolher_curso()
    repo.matricular(aluno["_id"], curso["_id"])
    print(f"\n{aluno['nome']} foi matriculado(a) em {curso['titulo']}.")


def opcao_progresso():
    aluno = escolher_aluno()
    matricula = escolher_matricula(aluno)
    progresso = ler_numero("Novo progresso (0 a 100): ", int, obrigatorio=True)
    repo.atualizar_progresso(matricula["_id"], progresso)
    print("Matrícula concluída!" if progresso == 100 else "Progresso atualizado.")


def opcao_avaliar():
    aluno = escolher_aluno()
    matricula = escolher_matricula(aluno)
    nota = ler_numero("Nota (1 a 5): ", int, obrigatorio=True)
    if repo.avaliar(matricula["_id"], nota):
        print("Avaliação registrada.")
    else:
        print("Só é possível avaliar uma matrícula concluída.")


OPCOES = {
    "1": ("Buscar cursos", opcao_buscar),
    "2": ("Matricular aluno", opcao_matricular),
    "3": ("Atualizar progresso", opcao_progresso),
    "4": ("Avaliar curso", opcao_avaliar),
    "5": ("Relatórios", imprimir_relatorios),
}


def main():
    while True:
        print("\n=== Aprenda+ ===")
        for chave, (nome, _) in OPCOES.items():
            print(f"{chave}. {nome}")
        print("0. Sair")

        escolha = input("Escolha: ").strip()
        if escolha == "0":
            print("Até mais!")
            break
        if escolha not in OPCOES:
            print("Opção inválida.")
            continue

        try:
            OPCOES[escolha][1]()
        except ValueError as erro:
            print(f"Erro: {erro}")


if __name__ == "__main__":
    main()
