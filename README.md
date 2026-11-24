# nosql-lab: catálogo da plataforma Aprenda+

Catálogo de cursos em MongoDB com Python (PyMongo), com carga inicial de dados, operações CRUD, validação de esquema, um menu de terminal e três relatórios para a coordenação.

## Como executar

### 1. Pré-requisitos

- Python 3 instalado.
- Uma conta no [MongoDB Atlas](https://www.mongodb.com/atlas). O plano gratuito (M0) é suficiente.

### 2. Preparar o MongoDB Atlas

1. Crie um cluster gratuito.
2. Em **Security > Database & Network Access > Database Users**, crie um usuário do banco com senha.
3. Em **IP Access List**, clique em **Add IP Address** e libere o IP do seu computador.
4. Em **Clusters > Connect > Drivers**, escolha **Python** e copie a connection string.

O banco e as coleções não precisam ser criados à mão: os scripts criam tudo.

### 3. Instalar e configurar

Todos os comandos abaixo rodam na pasta raiz do projeto.

```bash
git clone https://github.com/Andcaio/nosql-lab.git
cd nosql-lab
python -m pip install -r requirements.txt
```

Copie o arquivo de exemplo para `.env`:

```bash
cp .env.example .env              # Linux/macOS/Git Bash
Copy-Item .env.example .env       # PowerShell
```

Abra o `.env` e preencha com a connection string do passo 2. Troque o usuário e a senha e remova os sinais `<` e `>`:

```env
MONGO_URI=mongodb+srv://usuario:senha@seu-cluster.mongodb.net/
MONGO_DB=aprenda_mais
```

O `.env` está no `.gitignore` e nunca vai para o repositório.

### 4. Rodar

| Ordem | Comando | O que faz |
|---|---|---|
| 1 | `python -m mongo_cursos.conexao` | Testa a conexão com um `ping`. |
| 2 | `python -m mongo_cursos.validacao` | Cria a coleção `cursos` com validação e mostra um curso de preço negativo sendo rejeitado. |
| 3 | `python -m mongo_cursos.seed` | Insere 30 cursos em 5 categorias, 10 alunos e 30 matrículas. Rodar de novo não duplica nada. |
| 4 | `python -m mongo_cursos.main` | Abre o menu: buscar cursos, matricular, atualizar progresso, avaliar e ver os relatórios. |

## Estrutura

```text
nosql-lab/
├── mongo_cursos/
│   ├── conexao.py      # obter_banco(): lê MONGO_URI e MONGO_DB e cria o MongoClient
│   ├── validacao.py    # $jsonSchema da coleção cursos e demonstração de rejeição
│   ├── seed.py         # carga inicial idempotente com insert_many e random
│   ├── repositorio.py  # CRUD e regras de negócio
│   ├── relatorios.py   # três relatórios com aggregate
│   └── main.py         # menu de terminal
├── .env.example
├── requirements.txt
└── README.md
```

## Regras de negócio

| Regra | Como foi garantida |
|---|---|
| E-mail do aluno é único | Índice único em `alunos.email`. |
| Aluno não se matricula duas vezes no mesmo curso | Índice único composto em `matriculas` (`aluno_id` + `curso_id`) e conferência antes de gravar. |
| Curso sem vagas não aceita matrícula | `find_one_and_update` com `vagas > 0` e `$inc: -1` em um único comando, o que evita que dois alunos peguem a última vaga ao mesmo tempo. |
| Progresso de 0 a 100, concluída ao chegar a 100 | `atualizar_progresso` usa `$set` e marca `concluida: true` em 100. |
| Nota de 1 a 5, só depois de concluir | `avaliar` recusa notas fora da faixa e só altera matrículas com `concluida: true`. |
| Remover aluno remove as matrículas dele | `remover_aluno` apaga as matrículas com `delete_many`, devolve as vagas aos cursos e depois apaga o aluno. O MongoDB não tem `ON DELETE CASCADE`. |

## Validação

A coleção `cursos` é criada com `$jsonSchema`, exigindo `titulo`, `categoria`, `preco` (número >= 0), `vagas` (inteiro >= 0) e `modulos` (array). Os demais campos, como `certificado` e `pre_requisitos`, continuam opcionais, mantendo a flexibilidade do documento. Para ver a rejeição de um preço negativo, rode `python -m mongo_cursos.validacao`.

## Relatórios

| Relatório | Pergunta que responde |
|---|---|
| Avaliação média por curso | Quais cursos são mais bem avaliados? |
| Matrículas por categoria | Quantas matrículas e conclusões cada categoria tem? |
| Cursos com mais alunos | Quais cursos são mais procurados e quantas vagas restam? |

Os relatórios usam `aggregate` com `$lookup` para juntar matrículas e cursos. Isso não contradiz a modelagem: a página do curso, aberta o tempo todo, é lida com uma única consulta, e o join fica só nos relatórios, usados com bem menos frequência.

## Justificativas de modelagem

O projeto usa três coleções: `cursos`, `alunos` e `matriculas`. A escolha entre embutir e referenciar considerou o padrão de leitura e o limite de 16 MB por documento.

| Dado | Escolha | Justificativa |
|---|---|---|
| Módulos | Embutidos em `cursos` | São exibidos junto com o curso, então a página é montada com uma única consulta, sem os 7 joins do modelo antigo. A lista é pequena (de 3 a 20 módulos) e fica longe do limite de 16 MB. |
| Instrutor | Embutido em `cursos` | Tem poucos campos e aparece sempre na página do curso. |
| Alunos | Coleção própria | Um aluno existe independentemente de um curso e pode fazer vários cursos. |
| Matrículas | Coleção própria, com `aluno_id` e `curso_id` | Crescem sem limite definido, mudam com frequência (progresso e nota) e não precisam ser carregadas ao abrir a página do curso. |

## Em que situação embutir as matrículas no curso seria um erro de modelagem?

Seria um erro quando um curso pode acumular muitas matrículas. Com matrículas de 200 bytes, cerca de 80.000 já ocupam 16 MB. Um curso com 200.000 matrículas precisaria de 40 MB, e o MongoDB recusaria com erro as gravações que ultrapassassem o limite, impedindo novas matrículas.

Mesmo abaixo do limite, a escolha continuaria ruim: abrir a página do curso traria todas as matrículas sem necessidade, e cada atualização de progresso alteraria um documento cada vez maior.
