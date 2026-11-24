"""Coleção cursos com validação de esquema."""
from pymongo.errors import WriteError

from mongo_cursos.conexao import obter_banco

VALIDADOR_CURSOS = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["titulo", "categoria", "preco", "vagas", "modulos"],
        "properties": {
            "titulo": {"bsonType": "string"},
            "categoria": {"bsonType": "string"},
            "preco": {
                "bsonType": "number",
                "minimum": 0,
            },
            "vagas": {
                "bsonType": "int",
                "minimum": 0,
            },
            "modulos": {"bsonType": "array"},
        },
    }
}


def criar_colecao_cursos(banco):
    if "cursos" in banco.list_collection_names():
        banco.command("collMod", "cursos", validator=VALIDADOR_CURSOS)
    else:
        banco.create_collection("cursos", validator=VALIDADOR_CURSOS)


def demonstrar_preco_negativo(banco):
    cursos = banco.get_collection("cursos")
    curso_invalido = {
        "titulo": "Curso de teste",
        "categoria": "Teste",
        "preco": -1,
        "vagas": 10,
        "modulos": [],
    }

    try:
        resultado = cursos.insert_one(curso_invalido)
    except WriteError as erro:
        print(f"Documento rejeitado pelo MongoDB (código {erro.code}).")
    else:
        cursos.delete_one({"_id": resultado.inserted_id})
        print("Atenção: o documento foi aceito. Revise o validador.")


if __name__ == "__main__":
    banco = obter_banco()
    criar_colecao_cursos(banco)
    print("Coleção cursos pronta, com validação.")
    demonstrar_preco_negativo(banco)
