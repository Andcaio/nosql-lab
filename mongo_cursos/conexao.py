"""Conexão com o MongoDB."""
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def obter_banco():
    uri = os.getenv("MONGO_URI")

    nome_banco = os.getenv("MONGO_DB")

    if not uri or not nome_banco:
        raise RuntimeError(
            "MONGO_URI e MONGO_DB não foram lidos. "
            "Confira o arquivo .env e os nomes usados em os.getenv()."
        )

    cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)

    return cliente.get_database(nome_banco)


if __name__ == "__main__":
    banco = obter_banco()
    banco.command("ping")
    print(f"Conectado ao banco '{banco.name}'!")
