# Assistente de Edital — CEF 2024

> Chatbot com RAG para consulta ao edital do **Concurso Público da Caixa Econômica Federal** — Engenheiro de Segurança do Trabalho e Médico do Trabalho (2024).

![Python](https://img.shields.io/badge/Python-3.12.5-3776AB?style=flat&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.2.13-1C3C3C?style=flat&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat&logo=openai&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-1.1.0-FF6B35?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-FF4B4B?style=flat&logo=streamlit&logoColor=white)

---

## Arquitetura

### Indexação (executada uma vez)

```
data/edital.pdf
      │
      ▼
 PyPDFLoader          — carrega o PDF página a página
      │
      ▼
 RecursiveCharacterTextSplitter  — divide em chunks (500 chars, overlap 100)
      │
      ▼
 OpenAI Embeddings               — text-embedding-3-small
      │
      ▼
 ChromaDB  ──────────────────── persiste em ./my_chroma_db
```

### Consulta (a cada pergunta)

```
 Pergunta do usuário
      │
      ▼
 ChromaDB Retriever  — busca semântica, retorna top-3 chunks
      │
      ▼
 ChatPromptTemplate  — injeta chunks como contexto
      │
      ▼
 GPT-4o (temperature=0)
      │
      ▼
 Resposta
```

### Estrutura de arquivos

```
├── app.py               # Interface Streamlit
├── data/
│   └── edital.pdf       # Edital da CEF 2024
├── src/
│   ├── ingest.py        # Carrega e divide o PDF em chunks
│   ├── embeddings.py    # Cria/carrega o banco vetorial
│   ├── retriever.py     # Configura o retriever
│   └── chain.py         # Monta a chain LCEL e expõe ask()
└── requirements.txt
```

---

## Como rodar

### Pré-requisitos

- Python 3.12.5+
- Chave de API da OpenAI

### Instalação

```bash
# 1. Clone o repositório (o PDF já está incluído em data/)
git clone <url-do-repositório>
cd <nome-da-pasta>

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure a chave da OpenAI
cp .env.example .env
# Edite o .env e preencha: OPENAI_API_KEY=sk-...
```

### Executar

```bash
streamlit run app.py
```

O banco vetorial é criado automaticamente na primeira execução e salvo em `./my_chroma_db`. Nas execuções seguintes ele é reutilizado sem recusar a API.

### Testar módulos individualmente (opcional)

```bash
cd src

python ingest.py        # Verifica carregamento e chunking do PDF
python embeddings.py    # Cria o banco vetorial e exibe contagem de chunks
python retriever.py     # Busca chunks relevantes para uma query de exemplo
python chain.py         # Faz uma pergunta completa ao RAG
```

---

## Decisões técnicas

### ChromaDB
Banco vetorial local sem necessidade de servidor. Persiste em disco no diretório `./my_chroma_db`, o que elimina o custo de recriar os embeddings a cada execução. Para um projeto de documento único e escopo fixo, a simplicidade supera alternativas como Pinecone ou Weaviate, que exigem infraestrutura externa.

### RecursiveCharacterTextSplitter — chunk_size=500, overlap=100
O `RecursiveCharacterTextSplitter` tenta dividir por parágrafos, depois por frases, depois por palavras — preservando coerência semântica ao máximo. O `chunk_size=500` garante contexto suficiente por chunk sem ultrapassar o limite de tokens do modelo de embedding. O `overlap=100` evita que informações partidas na borda de um chunk se percam: os 100 caracteres finais de cada chunk são repetidos no início do próximo.

### text-embedding-3-small
Melhor custo-benefício da OpenAI para busca semântica. Comparado ao `text-embedding-3-large`, entrega qualidade similar para textos administrativos/jurídicos em português com menor latência e custo por token.

### GPT-4o com temperature=0
`temperature=0` torna o modelo determinístico — dada a mesma pergunta e o mesmo contexto, a resposta é sempre a mesma. Essencial para um assistente de edital onde precisão e reprodutibilidade importam mais do que criatividade.

### k=3 no retriever
Retornar apenas os 3 chunks mais relevantes mantém o contexto enviado ao GPT-4o enxuto e focado. Valores maiores de `k` tendem a introduzir ruído e aumentar o custo por chamada sem melhorar a resposta para perguntas factuais.

### LCEL (LangChain Expression Language)
Padrão nativo da LangChain 1.x. Substitui as chains legadas (`create_retrieval_chain`, `create_stuff_documents_chain`) que foram removidas nessa versão. A sintaxe com `|` torna o pipeline legível como um fluxo linear de dados.
