from retriever import get_retriever
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "Você é um assistente especializado em análise de editais. "
    "Use os seguintes pedaços de contexto recuperado para responder à pergunta. "
    "Se você não souber a resposta com base no contexto, diga que não encontrou no documento. "
    "Mantenha a resposta concisa e profissional."
    "\n\n"
    "Contexto:\n{context}"
)


def _format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def get_chain():
    retriever = get_retriever(k=3)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    return (
        {"context": retriever | _format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def ask(pergunta: str) -> str:
    chain = get_chain()
    return chain.invoke(pergunta)


if __name__ == "__main__":
    print(ask("Qual o valor total do edital?"))
