# Assistente de Edital — CEF 2024

> Projeto de estudo: chatbot com RAG para consulta ao edital do **Concurso Público da Caixa Econômica Federal** — Engenheiro de Segurança do Trabalho e Médico do Trabalho (2024).

![Projeto de estudo](https://img.shields.io/badge/projeto-de%20estudo-6366F1?style=flat)
![Python](https://img.shields.io/badge/Python-3.12.5-3776AB?style=flat&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.2.13-1C3C3C?style=flat&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat&logo=openai&logoColor=white)
![langchain-chroma](https://img.shields.io/badge/langchain--chroma-1.1.0-FF6B35?style=flat)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-FF4B4B?style=flat&logo=streamlit&logoColor=white)

---

## Por que eu construí isso

Este é um **projeto pessoal de aprendizado**, não um produto. Eu queria sair da teoria e entender na prática como três tecnologias funcionam e se encaixam: **RAG**, **LangChain** e **banco de dados vetorial**.

Escolhi um edital de concurso de propósito. É um documento real, longo, denso e escrito em linguagem jurídica — exatamente o tipo de PDF sobre o qual um LLM sozinho alucina com confiança. Isso torna o caso de teste honesto: se a recuperação falhar, a resposta errada aparece na cara.

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

## O que eu aprendi

### RAG — recuperar antes de gerar

O GPT-4o não tem esse edital nos pesos dele. Perguntar direto sobre o valor da taxa de inscrição gera uma de duas coisas: um "não tenho acesso a esse documento" ou, pior, um número inventado com toda a confiança do mundo.

RAG resolve isso sem treinar nada. Em vez de ensinar o documento ao modelo, o pipeline **busca os trechos relevantes no momento da pergunta** e os injeta no prompt como contexto. O modelo deixa de responder de memória e passa a responder a partir de um texto que está ali na frente dele.

O aprendizado que mudou minha forma de pensar: **a qualidade da resposta é limitada pela qualidade da recuperação**. Se o chunk que contém a informação não é retornado, nenhum ajuste de prompt salva — o modelo simplesmente não recebeu o dado. Por isso, quando a resposta vem errada, o primeiro suspeito é o retriever ([src/retriever.py](src/retriever.py)), não o LLM.

O outro lado da moeda é ancorar o modelo no contexto recebido. A instrução "se você não souber a resposta com base no contexto, diga que não encontrou no documento" no `SYSTEM_PROMPT` ([src/chain.py:11-18](src/chain.py#L11-L18)) é o que autoriza o modelo a admitir ignorância em vez de preencher a lacuna com invenção.

### Banco de dados vetorial — busca por significado

Um **embedding** é a tradução de um texto em uma lista de números (um vetor) que representa seu significado. Aqui o `text-embedding-3-small` faz isso com cada chunk do edital. A propriedade que importa: textos com sentido parecido geram vetores próximos no espaço vetorial. Buscar deixa de ser comparar caracteres e passa a ser **medir distância entre significados**.

Foi aqui que a diferença em relação a um banco tradicional ficou clara. Um `WHERE texto LIKE '%custo da inscrição%'` não encontra nada se o edital escreve "valor da taxa de inscrição" — não há palavra em comum suficiente. A busca vetorial encontra, porque as duas frases querem dizer a mesma coisa. O ChromaDB é o que guarda esses vetores e responde "quais são os 3 mais parecidos com esta pergunta?".

Dois conceitos que só entendi de verdade implementando:

**Persistência não é otimização, é fundamento.** Gerar embeddings custa tempo e dinheiro (é uma chamada de API por lote de chunks). Recriar o índice a cada execução seria pagar duas vezes pela mesma coisa. A lógica de "o diretório já existe? carrega : cria" em [src/embeddings.py:15-32](src/embeddings.py#L15-L32) é simples, mas é o que separa um script de brinquedo de algo utilizável.

**Chunking é decisão de design, não detalhe de implementação.** O tamanho do chunk é um trade-off direto: um chunk grande demais dilui o sinal do embedding (um vetor tentando representar cinco assuntos diferentes não fica próximo de nenhum deles), e um chunk pequeno demais perde o contexto necessário para a resposta fazer sentido. O `add_start_index=True` ([src/ingest.py:15](src/ingest.py#L15)) guarda a posição original de cada chunk no documento — metadado que permite rastrear de onde a informação veio.

### LangChain — composição de peças

O valor da biblioteca ficou evidente quando percebi que loader, splitter, embeddings, vector store, LLM e output parser expõem **a mesma interface** (`Runnable`). Isso significa que trocar o ChromaDB por outro banco vetorial, ou o GPT-4o por outro modelo, não obriga a reescrever o resto do pipeline — só a peça substituída.

O **LCEL** (LangChain Expression Language) é o que torna essa composição legível. O pipeline em [src/chain.py:34-39](src/chain.py#L34-L39) se lê de cima para baixo como o fluxo real dos dados:

```python
{"context": retriever | _format_docs, "input": RunnablePassthrough()}
| prompt
| llm
| StrOutputParser()
```

A parte que me custou mais para entender foi o dicionário do início. Ele cria **dois ramos que recebem a mesma entrada** — a pergunta do usuário — e a processam de formas diferentes: o ramo `context` manda a pergunta ao retriever e formata os documentos retornados em texto, enquanto o `RunnablePassthrough()` só repassa a pergunta intacta. As duas saídas chegam ao `prompt` e preenchem os placeholders `{context}` e `{input}`. É um fan-out seguido de junção, escrito como um dicionário.

Um aprendizado colateral, mas valioso: **versão importa**. As chains prontas que aparecem em quase todo tutorial de RAG (`create_retrieval_chain`, `create_stuff_documents_chain`) foram removidas na LangChain 1.x. Passei tempo debugando `ImportError` antes de entender que o problema não era meu código — era o tutorial. Ler a documentação da versão que está instalada, e não a primeira que o Google devolve, faz parte do trabalho.

Por último, a organização em módulos de responsabilidade única em [src/](src/) não foi só estética: cada arquivo pode ser executado sozinho para inspecionar sua etapa isoladamente, o que torna possível descobrir *onde* o pipeline quebrou em vez de só constatar que a resposta final veio ruim.

---

## Como rodar

### Pré-requisitos

- Python 3.12.5+
- Chave de API da OpenAI

### Instalação

```bash
# 1. Clone o repositório (o PDF já está incluído em data/)
git clone https://github.com/guiakiraa/editalCaixa2024-rag.git
cd editalCaixa2024-rag

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

O banco vetorial é criado automaticamente na primeira execução e salvo em `./my_chroma_db`. Nas execuções seguintes ele é reutilizado, sem novas chamadas à API de embeddings.

### Inspecionar cada etapa do pipeline (opcional)

Cada módulo em `src/` tem um bloco `__main__` que executa e imprime a sua etapa isoladamente — útil para descobrir *onde* o pipeline quebrou em vez de só constatar que a resposta final veio ruim. Rode **a partir da raiz do projeto**: os caminhos do PDF e do banco vetorial são relativos ao diretório atual.

```bash
python src/ingest.py        # Carrega o PDF, divide em chunks e mostra o primeiro
python src/embeddings.py    # Cria/carrega o banco vetorial e conta os chunks
python src/retriever.py     # Recupera os 3 chunks mais relevantes para uma query
python src/chain.py         # Faz uma pergunta completa ao RAG
```

`retriever.py` e `chain.py` aceitam a pergunta como argumento; sem argumento, usam um exemplo padrão:

```bash
python src/retriever.py "quais são os requisitos do cargo?"
python src/chain.py "qual o valor da taxa de inscrição?"
```

Só o `ingest.py` roda sem consumir API. Os outros três geram embeddings (e o `chain.py` também chama o GPT-4o), então exigem uma `OPENAI_API_KEY` válida.

---

## Decisões técnicas e trade-offs

Todas as escolhas abaixo foram feitas com foco em aprendizado e escopo pequeno — um único documento, rodando localmente. Em produção, várias delas mereceriam outra resposta.

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

---

## Próximos passos de estudo

O que ficou de fora desta versão e por que vale explorar:

- **Citar a fonte na resposta.** Os metadados de página e posição já existem — o `PyPDFLoader` guarda o número da página e o `add_start_index=True` guarda o offset no documento. Falta apenas propagá-los até a resposta para o usuário poder conferir o trecho original no edital.
- **Memória de conversa.** Hoje cada pergunta é independente: `ask()` monta a chain e a invoca do zero a cada chamada ([src/chain.py:42-44](src/chain.py#L42-L44)). A interface mostra o histórico, mas o modelo não o recebe — então um follow-up como "e o prazo disso?" não tem a que se referir.
- **Avaliar a recuperação de forma sistemática.** Testar no olho não escala e não detecta regressões. O caminho é montar um conjunto de perguntas com resposta conhecida e medir se o chunk correto aparece entre os `k` retornados, o que permite comparar valores de `chunk_size`, `overlap` e `k` com número em vez de impressão.
- **Reranking e busca híbrida.** A busca puramente semântica erra em termos exatos — números de artigo, códigos, datas. Combinar similaridade vetorial com busca por palavra-chave (BM25) e reordenar os resultados com um modelo de reranking costuma resolver essa classe de falha.
- **Múltiplos documentos.** Suportar upload pela interface e vários PDFs simultâneos exigiria filtro por metadado no retriever, o que muda o desenho da consulta.
